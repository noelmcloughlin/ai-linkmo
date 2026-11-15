#!/usr/bin/env bash
#
# Wrapper for the scheduled knowledge-librarian loop (Karpathy rule).
#
# `.github/workflows/knowledge-librarian.yaml` runs this script at a fixed,
# reviewed path, not a command from a repository variable, once the
# repository variable `KNOWLEDGE_LIBRARIAN_ENABLED` is "true". `AGENT_CLI`, a
# repository variable or secret, names the command that runs your coding
# agent non-interactively, such as the GitHub Copilot CLI, Claude Code or an
# internal agent runner.
#
# CONTRACT (the workflow relies on this):
#   - The agent WRITES one file, .lokf/patch.yaml, and this script applies it
#     with knowledge-apply.sh. So .lokf/knowledge/, a handled feedback.md
#     entry and its ledger line in questions.md change only through that
#     script. A run in which the agent changed any other path is refused, and
#     so is one whose result touches a person's event, note or text, which
#     knowledge-provenance.sh --unattended checks.
#   - The pen and that gate run from copies taken out of HEAD before the agent
#     runs, and a run in which the agent moved HEAD or changed those copies is
#     refused. The agent shares this job's user, so a file outside git, such
#     as .lokf/.venv, and a process it leaves running stay within its reach.
#     So these checks only stop a bad run early. The boundary is the
#     workflow's apply and publish jobs, on runners the agent never shared.
#   - The workflow hands on the patch file's copy in KNOWLEDGE_PATCH_OUT, and
#     nothing this job made from it, and its apply job runs the pen on it
#     again. A patch file that is a link is refused, and a refused run leaves
#     no copy.
#   - The files the *_OUT variables name are removed once the agent returns,
#     so the workflow reads only what was written after it.
#   - It MUST NOT commit, push or open pull requests: the workflow does.
#   - It exits 0 on success, whether or not it changed anything: the workflow
#     diffs the working tree to decide on a pull request. When the caller
#     allows a skip, a run that knowledge-report.sh finds quiet exits 0
#     before the agent is called.
#
# Inputs (env):
#   AGENT_CLI           command that runs the agent given a prompt via -p "<prompt>"
#   AGENT_PROMPT_FLAG   optional: the flag the prompt follows, -p by default,
#                       or the word arg when the agent takes the prompt as a
#                       bare last argument, as `codex exec` does
#   AGENT_API_KEY       optional: the agent's API key or token, from a secret
#   AGENT_API_KEY_ENV   the name the agent reads that key from, such as
#                       ANTHROPIC_API_KEY; required when AGENT_API_KEY is set
#   KNOWLEDGE_SKIP_QUIET optional: "true" skips the agent when
#                       knowledge-report.sh finds nothing waiting for it; set
#                       on a scheduled run only
#   KNOWLEDGE_DECLINED  optional: a file naming the changes a person declined
#                       by closing a pull request of the workflow's unmerged.
#                       knowledge-report.sh leaves them out of the quiet check
#                       and the agent's work list until they change again. Set
#                       on a scheduled run only
#   KNOWLEDGE_HANDOFF_OUT  optional: a file the pen writes the patch's `handoff`
#                       lines to, cleaned
#   KNOWLEDGE_PATCH_OUT optional: a file to copy the agent's patch file to, as
#                       it wrote it, once the checks pass and before the pen
#                       applies it here
#   KNOWLEDGE_RETRIEVAL optional: "true" scores, after the bundle is written,
#                       whether the index leads an agent to the concept behind
#                       each question readers asked (one more agent call)
#   KNOWLEDGE_RETRIEVAL_OUT  optional: a file to write that one score line to
#
set -euo pipefail

# Resolve the repo root from this script's location so it works regardless of cwd.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

# The skill may sit in any of the three install folders, or in skills/ in a
# repository that publishes the skills it uses; add another here if needed.
# .agents/skills/ is tried first: the scheduled workflow installs the pinned
# skill there, and a copy the host committed elsewhere, perhaps an older
# one, must not replace it.
skill=""
for candidate in .agents/skills/ktl-librarian/SKILL.md .claude/skills/ktl-librarian/SKILL.md \
                 .github/skills/ktl-librarian/SKILL.md skills/ktl-librarian/SKILL.md; do
  if [ -f "$candidate" ]; then skill="$candidate"; break; fi
done
[ -n "$skill" ] || {
  echo "knowledge-librarian: ktl-librarian SKILL.md not found in .agents/skills/, .claude/skills/, .github/skills/, or skills/" >&2
  exit 2
}

# A sync adds no file that was not there, so a sidecar synced from an older
# copy can lack the pen. Say so now, before an agent run is spent on a patch
# nothing could apply.
if [ ! -f .lokf/scripts/knowledge-apply.sh ] || [ ! -f .lokf/scripts/knowledge-apply.py ]; then
  echo "knowledge-librarian: .lokf/scripts/knowledge-apply.sh and knowledge-apply.py are not both here, and the bundle is written through them alone; ktl-sidecar's repair path lays them down" >&2
  exit 2
fi

if [ -z "${AGENT_CLI:-}" ]; then
  cat >&2 <<'EOF'
knowledge-librarian: AGENT_CLI is not set.

Set AGENT_CLI to your non-interactive agent command (e.g. a Copilot CLI or
internal runner). This wrapper hands it a prompt built from the ktl-librarian
skill; the agent is expected to write one file, .lokf/patch.yaml, which this
wrapper then applies with knowledge-apply.sh.
EOF
  exit 2
fi

# The prompt takes the patch file's format from knowledge-apply.sh --format
# and names no file inside the skill, because a scheduled run installs a
# skill pinned one release behind these scripts. Say so when that skill
# predates the patch file: nothing else tells the operator why the two differ.
if [ ! -f "$(dirname "$skill")/references/patch.md" ]; then
  echo "knowledge-librarian: $skill predates the patch file, so the prompt takes the format from knowledge-apply.sh --format; move the skills pin to a release that carries references/patch.md once one is tagged" >&2
fi

# The agent CLI reads the key under its own name. The name must end _API_KEY,
# _TOKEN or _KEY, so a slip cannot overwrite PATH, BASH_ENV or LD_PRELOAD,
# and must not start GITHUB_, GH_, GIT_, RUNNER_ or ACTIONS_, because gh, git
# and the runner read those names too. The key moves into an unexported
# variable, so the git commands this script runs never see it.
key_name="${AGENT_API_KEY_ENV:-}"
agent_key="${AGENT_API_KEY:-}"
unset AGENT_API_KEY AGENT_API_KEY_ENV
# Only the agent's process carries the pen's dry-run-only switch (see
# run_agent): one set outside would stop this script applying the patch.
unset KNOWLEDGE_PEN_DRY_RUN_ONLY
if [ -n "$agent_key" ] || [ -n "$key_name" ]; then
  if [ -z "$agent_key" ]; then
    echo "knowledge-librarian: AGENT_API_KEY_ENV is $key_name but the AGENT_API_KEY secret is empty" >&2
    exit 2
  fi
  if [ -z "$key_name" ]; then
    echo "knowledge-librarian: AGENT_API_KEY is set; set AGENT_API_KEY_ENV to the name your agent reads it from, such as ANTHROPIC_API_KEY" >&2
    exit 2
  fi
  if ! [[ "$key_name" =~ ^[A-Z][A-Z0-9_]*_(API_KEY|TOKEN|KEY)$ ]] \
     || [[ "$key_name" =~ ^(GITHUB|GH|GIT|RUNNER|ACTIONS)_ ]]; then
    echo "knowledge-librarian: AGENT_API_KEY_ENV '$key_name' is refused: use the upper-case name your agent reads its key from, ending _API_KEY, _TOKEN or _KEY and not starting GITHUB_, GH_, GIT_, RUNNER_ or ACTIONS_" >&2
    exit 2
  fi
fi

# How the prompt reaches the agent. Only a short flag, a long flag or the word
# arg is accepted, so the variable can add nothing but the prompt's position.
prompt_flag="${AGENT_PROMPT_FLAG:--p}"
if ! [[ "$prompt_flag" =~ ^(-[A-Za-z]|--[a-z][a-z0-9-]*|arg)$ ]]; then
  echo "knowledge-librarian: AGENT_PROMPT_FLAG '$prompt_flag' is refused: use a flag such as -p or --prompt, or the word arg for an agent that takes the prompt as its last argument" >&2
  exit 2
fi

# Build the prompt. The heredoc is unquoted so that $skill expands. Any
# backtick in the text MUST therefore be escaped (\`), or bash runs it as a
# command and blanks the word.
prompt="$(cat <<EOF
You are the repository knowledge librarian. Follow this skill file verbatim:
  - $skill

Task (Karpathy rule - continuous small corrections, not a rewrite):
  1. Follow the skill's Scrape & build procedure: bootstrap discovery if the
     bundle has no real concepts yet, otherwise the steady-state refresh of the
     sources recorded in the bundle (concept provenance and
     .lokf/knowledge/playbooks/knowledge-sources.md). Start a refresh from
     "bash .lokf/scripts/knowledge-report.sh worklist" where that script
     exists: a program has already found which sources moved, which notes a
     person left, and how much reader feedback waits. Where that list names
     changes a person declined, by closing a pull request without merging,
     propose none of them again, and say in the hand-off what you left.
  2. Reconcile the .lokf/ knowledge bundle with the repository: add missing
     concepts, correct stale facts, wire typed relations, and give every
     operation its log line - but only when the bundle content actually
     changed. If nothing changed, write no patch file at all; do not log
     administrative no-op runs.
  3. Write every change as an operation in .lokf/patch.yaml, in the shape
     "bash .lokf/scripts/knowledge-apply.sh --format" prints, and check it
     with "bash .lokf/scripts/knowledge-apply.sh --dry-run". Create and edit
     that file with your own file-writing tool, never with a shell redirect,
     a heredoc or a script. An unattended run may deny a shell command that
     writes, and a denied shell write does not mean the file cannot be
     written. Do NOT edit any
     file under .lokf/knowledge/, .lokf/feedback.md or .lokf/questions.md
     yourself, do NOT run the apply script without --dry-run, and do NOT run
     git, open PRs, or touch any other path: this wrapper applies the file
     after you finish. Cite sources for any claim whose authority is outside
     the repository.
  4. Mark concepts you create, and claims you cannot settle from the
     repository, as \`status: draft\` (with a plain-prose "## Open questions"
     section for the latter), exactly as the skill says. Put what the person
     reviewing the pull request should know, and that is no change to the
     bundle, in the patch file's "handoff" list, in your own words and never
     a reader's. The workflow writes the rest of the pull request itself, and
     your final reply reaches the job log only.
EOF
)"

# Security rationale (for human and automated reviewers): AGENT_CLI is trusted
# configuration that a repository admin sets in Settings, never repository
# contents, pull request data or model output. It is split on whitespace,
# with no globbing, and run as a quoted argv vector, with no eval and no
# `bash -c`, so bash does NOT re-evaluate it and shell metacharacters
# (; | & $() ``) are passed as inert arguments. Quotes inside it are not
# honoured, so keep it to a command and its flags, or wrap richer logic in a
# script. The agent runs only in the workflow's read-only `refresh` job
# (contents: read, no persisted credentials).
#
# The agent call and the checks after it sit in main(), called only from
# this file's last line. Bash reads a function body in full before running
# any of it, so an agent that truncates this script mid-run cannot make it
# skip anything after the agent call. A top-level statement runs only if the
# file on disk still holds it when bash reaches it.
read -r -a agent_cmd <<< "$AGENT_CLI"
if [ "${#agent_cmd[@]}" -eq 0 ]; then
  echo "knowledge-librarian: AGENT_CLI has no command after parsing" >&2
  exit 2
fi

# Become the agent, by exec from a subshell, so only that subshell's
# environment carries the key and KNOWLEDGE_PEN_DRY_RUN_ONLY. That switch
# makes the pen only check a patch file, so an agent that follows the
# skill's live-session step cannot apply its patch, which would make the pen
# delete the file and the check below refuse the bundle it wrote. The switch
# is a guard against that mistake, not a boundary.
run_agent() {
  export KNOWLEDGE_PEN_DRY_RUN_ONLY=1
  if [ "$prompt_flag" = arg ]; then
    exec "${agent_cmd[@]}" "$1"
  fi
  exec "${agent_cmd[@]}" "$prompt_flag" "$1"
}

# The prompt asks the agent to write only the patch file, but nothing forces
# it. Record the paths already dirty outside the bundle, such as a uv.lock the
# workflow refreshed, so the agent answers only for *new* ones. The bundle,
# ktl-docent's .lokf/feedback.md and the pen's ledger .lokf/questions.md are
# allowed. The bundle is named twice, because a git pathspec does not
# traverse a link. knowledge_bundle/ is usually the doorway link, where the
# pathspec matches nothing, but on a host rearranged by hand it is the real
# folder and .lokf/knowledge the link.
outside_bundle() {
  git status --porcelain -- '.' \
    ':(exclude).lokf/knowledge' ':(exclude)knowledge_bundle' ':(exclude).lokf/feedback.md' ':(exclude).lokf/questions.md' \
    | cut -c4- | sort -u
}
# Every path git sees changed, the patch file apart: the agent's one output,
# which .lokf/.gitignore keeps out of git anyway.
changed_paths() {
  git status --porcelain -- '.' ':(exclude).lokf/patch.yaml' | cut -c4- | sort -u
}

# Snapshots of .git/config, .git/hooks/ and .git/info/ taken before each agent
# call, at file scope for the EXIT trap. The three live in the folder that
# every work tree shares, where a linked work tree's `.git` file points. A
# clone made without templates has no hooks/ or info/ folder, so each is put
# back as it was, absent when it was absent.
config_snapshot=""
hooks_snapshot=""
info_snapshot=""
git_dir=""
had_hooks=0
had_info=0
snapshot_git_state() {
  git_dir="$(git rev-parse --git-common-dir)"
  config_snapshot="$(mktemp)"
  hooks_snapshot="$(mktemp -d)"
  info_snapshot="$(mktemp -d)"
  cp "$git_dir/config" "$config_snapshot"
  had_hooks=0; had_info=0
  if [ -d "$git_dir/hooks" ]; then had_hooks=1; cp -a "$git_dir/hooks/." "$hooks_snapshot/"; fi
  if [ -d "$git_dir/info" ]; then had_info=1; cp -a "$git_dir/info/." "$info_snapshot/"; fi
}

# Put .git/config, .git/hooks/ and .git/info/ back as they were before the
# agent ran, then forget the snapshot so a second call does nothing. main()
# calls it when the agent returns. The EXIT trap calls it on every other way
# out: a failing agent under `set -e`, a cancelled job (SIGINT or SIGTERM,
# which the traps in main() turn into an exit), or another error. Without
# the trap, a failing agent would leave its rewritten config for the
# workflow's next steps.
restore_git_state() {
  [ -n "$config_snapshot" ] || return 0
  cp "$config_snapshot" "$git_dir/config"
  rm -rf "$git_dir/hooks"
  if [ "$had_hooks" = 1 ]; then mkdir "$git_dir/hooks"; cp -a "$hooks_snapshot/." "$git_dir/hooks/"; fi
  rm -rf "$git_dir/info"
  if [ "$had_info" = 1 ]; then mkdir "$git_dir/info"; cp -a "$info_snapshot/." "$git_dir/info/"; fi
  rm -rf "$config_snapshot" "$hooks_snapshot" "$info_snapshot"
  config_snapshot=""
  hooks_snapshot=""
  info_snapshot=""
}

# Everything git can see of the working tree, as one digest: which paths
# differ from HEAD, how the tracked ones differ, and what the untracked ones
# hold. It uses git object ids, because a changed file of the same length can
# be made to match a checksum such as cksum's.
tree_state() {
  {
    git status --porcelain --untracked-files=all
    git diff HEAD
    git ls-files --others --exclude-standard | while IFS= read -r f; do printf '%s %s\n' "$(git hash-object --no-filters -- "$f")" "$f"; done
  } 2>/dev/null | git hash-object --stdin
}

# The index-only retrieval test (knowledge-report.sh's `retrieval`). The
# agent answers one prompt, holding the table of contents and the questions
# readers asked, from an empty directory, so the index is all it has. A
# program scores its reply as one line, "n of m". The prompt carries
# readers' words, so the reply is read only for concept paths, the same
# snapshot guards .git/config, .git/hooks/ and .git/info/, and a call that
# changed anything in the checkout refuses the run. This call could also
# write the hand-off file, outside the checkout, so the lines the pen put
# there are written back after it.
score_retrieval() {
  local prompt scratch before line handoff=""
  prompt="$(bash .lokf/scripts/knowledge-report.sh retrieval --prompt 2>/dev/null || true)"
  if [ -z "$prompt" ]; then
    echo "knowledge-librarian: no reader's question is on file, so retrieval is not scored"
    return 0
  fi
  scratch="$(mktemp -d)"
  before="$(tree_state)"
  if [ -n "${KNOWLEDGE_HANDOFF_OUT:-}" ] && [ -f "$KNOWLEDGE_HANDOFF_OUT" ] && [ ! -L "$KNOWLEDGE_HANDOFF_OUT" ]; then
    handoff="$(cat "$KNOWLEDGE_HANDOFF_OUT")"
  fi
  snapshot_git_state
  (
    cd "$scratch" || exit 1
    if [ -n "$key_name" ]; then export "$key_name=$agent_key"; fi
    run_agent "$prompt"
  ) > "$scratch/reply" 2>/dev/null || true
  restore_git_state
  if [ -n "${KNOWLEDGE_HANDOFF_OUT:-}" ]; then
    rm -f "$KNOWLEDGE_HANDOFF_OUT"
    [ -z "$handoff" ] || printf '%s\n' "$handoff" > "$KNOWLEDGE_HANDOFF_OUT"
  fi
  if [ "$(tree_state)" != "$before" ]; then
    echo "knowledge-librarian: the retrieval call changed files in the checkout - refusing" >&2
    rm -rf "$scratch"
    exit 3
  fi
  if ! patch_out_intact; then
    echo "knowledge-librarian: the retrieval call changed the copy of the patch file the workflow hands on - refusing" >&2
    rm -rf "$scratch"
    exit 3
  fi
  line="$(bash .lokf/scripts/knowledge-report.sh retrieval "$scratch/reply" 2>/dev/null | sed -n 1p)"
  rm -rf "$scratch"
  echo "knowledge-librarian: $line"
  if [ -n "${KNOWLEDGE_RETRIEVAL_OUT:-}" ]; then rm -f "$KNOWLEDGE_RETRIEVAL_OUT"; printf '%s\n' "$line" > "$KNOWLEDGE_RETRIEVAL_OUT"; fi
}

# The pen and the provenance gate, copied out of HEAD before the agent runs,
# with their digests held in this script's memory, so a script the agent
# rewrote never checks its work. File scope, so the EXIT trap can remove
# them.
tools_dir=""
tools_sum=""
tools=(knowledge-apply.sh knowledge-apply.py knowledge-provenance.sh)
take_tools() {
  local name
  tools_dir="$(mktemp -d)"
  for name in "${tools[@]}"; do
    if ! git show "HEAD:./.lokf/scripts/$name" > "$tools_dir/$name" 2>/dev/null; then
      rm -f "$tools_dir/$name"
    fi
  done
  if [ ! -f "$tools_dir/knowledge-apply.sh" ] || [ ! -f "$tools_dir/knowledge-apply.py" ]; then
    echo "knowledge-librarian: HEAD holds no .lokf/scripts/knowledge-apply.sh and knowledge-apply.py, and the patch is applied with HEAD's copies; commit them first" >&2
    exit 2
  fi
  tools_sum="$(tools_digest)"
}
# Each copy's git object id, from its bytes only, for the reason tree_state
# gives. Git runs from the repository, whose settings are restored by then,
# and never from the copies' folder, where the agent could have left a .git
# of its own.
tools_digest() {
  local name
  for name in "${tools[@]}"; do
    if [ -f "$tools_dir/$name" ] && [ ! -L "$tools_dir/$name" ]; then
      printf '%s %s\n' "$(git hash-object --no-filters -- "$tools_dir/$name" 2>/dev/null)" "$name"
    else
      printf 'none %s\n' "$name"
    fi
  done
}
tools_intact() { [ -n "$tools_dir" ] && [ -n "$tools_sum" ] && [ "$(tools_digest)" = "$tools_sum" ]; }

# Copy the patch file to KNOWLEDGE_PATCH_OUT, and hold its git object id in
# memory. The copy is written beside the path and moved into place, so a
# link left at the path is replaced, not followed. The retrieval call runs
# later and could write there too, so the copy must still match the id when
# that call returns.
patch_sum=""
hand_on_patch() {
  local out="${KNOWLEDGE_PATCH_OUT:-}" tmp
  [ -n "$out" ] || return 0
  tmp="$(mktemp "$out.XXXXXX")"
  cp .lokf/patch.yaml "$tmp"
  mv -f "$tmp" "$out"
  patch_sum="$(git hash-object --no-filters -- "$out")"
}
patch_out_intact() {
  [ -z "$patch_sum" ] && return 0
  [ -f "$KNOWLEDGE_PATCH_OUT" ] && [ ! -L "$KNOWLEDGE_PATCH_OUT" ] \
    && [ "$(git hash-object --no-filters -- "$KNOWLEDGE_PATCH_OUT" 2>/dev/null)" = "$patch_sum" ]
}

# A run that ends in a refusal hands nothing on, so the copy is removed too.
on_exit() {
  local rc=$?
  restore_git_state
  [ -z "$tools_dir" ] || rm -rf "$tools_dir"
  if [ "$rc" -ne 0 ] && [ -n "$patch_sum" ]; then rm -f "$KNOWLEDGE_PATCH_OUT"; fi
}

# The files the workflow reads after this script: the patch file's copy, the
# hand-off and the retrieval score. The agent could leave a link at one of
# them that sends a later write into the checkout, so each is removed once
# the agent returns.
clear_outputs() {
  local out
  for out in "${KNOWLEDGE_PATCH_OUT:-}" "${KNOWLEDGE_HANDOFF_OUT:-}" "${KNOWLEDGE_RETRIEVAL_OUT:-}"; do
    [ -z "$out" ] || rm -f "$out"
  done
}

main() {
  # When the caller allows it, a run with nothing to do ends here, before the
  # agent is called. knowledge-report.sh decides, on the checkout before any
  # agent has touched it. Anything but a clear "quiet" runs the agent: work
  # waiting, no history, or a report script too old to know the command.
  if [ "${KNOWLEDGE_SKIP_QUIET:-}" = true ] && [ -f .lokf/scripts/knowledge-report.sh ]; then
    local verdict rc=0
    verdict="$(bash .lokf/scripts/knowledge-report.sh quiet 2>/dev/null)" || rc=$?
    case "$rc" in
      0) echo "knowledge-librarian: $verdict - the agent is not run this time"; return 0 ;;
      1) echo "knowledge-librarian: $verdict" ;;
      *) echo "knowledge-librarian: knowledge-report.sh could not say whether this run is quiet, so the agent runs" ;;
    esac
  fi

  # The checks below are only as good as the `git status` they read. An
  # agent that sets core.fsmonitor or core.hooksPath in .git/config, or adds
  # a file to .git/hooks/, has *this script's* later git commands run its
  # code. One that adds a rule to .git/info/exclude hides its writes from
  # them. The workflow's detect and package steps read this checkout too,
  # after this script exits. So the three are restored on every exit. Only
  # SIGKILL escapes this, and a runner that kills the step with it also
  # discards the job. This is defence in depth, not the backstop: a person
  # reviewing the pull request before merge is.
  snapshot_git_state
  trap on_exit EXIT
  take_tools
  local head_before
  head_before="$(git rev-parse HEAD)"
  # A signal caught by a trap does not end the shell, so these turn it into an
  # exit, which runs the EXIT trap above. Bash delivers them only once the
  # foreground agent has exited, so the restore never races the agent.
  trap 'exit 129' HUP
  trap 'exit 130' INT
  trap 'exit 143' TERM

  local before_outside before_all before_flags
  before_outside="$(outside_bundle)"
  before_all="$(changed_paths)"
  # The checks below read `git status`, which says nothing of a file whose
  # index entry is flagged skip-worktree or assume-unchanged. An agent that
  # set a flag on a script here could replace it unseen, so the flags are
  # read before and after. A sparse checkout has such entries of its own,
  # and only a change to them is refused.
  before_flags="$(git ls-files -v | grep -v '^H ' || true)"

  echo "knowledge-librarian: refreshing the .lokf/ bundle via AGENT_CLI"
  # The key reaches the agent through its environment, under the name it
  # reads, and never appears in a process's argument list.
  (
    if [ -n "$key_name" ]; then export "$key_name=$agent_key"; fi
    run_agent "$prompt"
  )

  # Restore before the checks below read git, not only at exit.
  restore_git_state
  clear_outputs

  # The agent may not commit: a commit would move what the checks below
  # compare with.
  if [ "$(git rev-parse HEAD)" != "$head_before" ]; then
    echo "knowledge-librarian: the agent moved HEAD, which the checks compare with - refusing" >&2
    rm -f .lokf/patch.yaml
    exit 3
  fi
  if ! tools_intact; then
    echo "knowledge-librarian: the copies of the pen and the gate taken before the agent ran have changed - refusing" >&2
    rm -f .lokf/patch.yaml
    exit 3
  fi

  if [ "$(git ls-files -v | grep -v '^H ' || true)" != "$before_flags" ]; then
    echo "knowledge-librarian: the agent changed which files git watches (a skip-worktree or assume-unchanged flag) - refusing:" >&2
    comm -13 <(printf '%s\n' "$before_flags" | sort) <(git ls-files -v | grep -v '^H ' | sort) | sed '/^$/d; s/^/  /' >&2
    rm -f .lokf/patch.yaml
    exit 3
  fi

  # Anything but .lokf/patch.yaml that the agent changed, inside the bundle
  # or out, is refused before the file is applied, so a direct edit never
  # reaches the publish job.
  local touched
  touched="$(comm -13 <(printf '%s\n' "$before_all") <(changed_paths))"
  if [ -n "${touched//[$'\n\t ']/}" ]; then
    echo "knowledge-librarian: the agent changed files other than .lokf/patch.yaml - refusing:" >&2
    printf '%s\n' "$touched" | sed '/^$/d; s/^/  /' >&2
    rm -f .lokf/patch.yaml
    exit 3
  fi
  if [ -L .lokf/patch.yaml ]; then
    echo "knowledge-librarian: .lokf/patch.yaml is a link, and the agent writes the file itself - refusing" >&2
    rm -f .lokf/patch.yaml
    exit 3
  fi
  if [ -f .lokf/patch.yaml ]; then
    hand_on_patch
    echo "knowledge-librarian: applying .lokf/patch.yaml with knowledge-apply.sh"
    if ! bash "$tools_dir/knowledge-apply.sh" --root "$repo_root" ${KNOWLEDGE_HANDOFF_OUT:+--handoff "$KNOWLEDGE_HANDOFF_OUT"} .lokf/patch.yaml; then
      echo "knowledge-librarian: knowledge-apply.sh refused the patch, so nothing was written" >&2
      rm -f .lokf/patch.yaml
      exit 4
    fi
  else
    echo "knowledge-librarian: the agent wrote no .lokf/patch.yaml, so the bundle is unchanged"
  fi

  local stray
  stray="$(comm -13 <(printf '%s\n' "$before_outside") <(outside_bundle))"
  if [ -n "${stray//[$'\n\t ']/}" ]; then
    echo "knowledge-librarian: agent modified paths outside .lokf/knowledge/ - refusing:" >&2
    printf '%s\n' "$stray" | sed '/^$/d; s/^/  /' >&2
    exit 3
  fi

  # The gate checks the result for what the pen refuses before it writes. The
  # publish job runs the same check on a checkout the agent never shared, and
  # this one fails fast.
  if [ -f "$tools_dir/knowledge-provenance.sh" ] && ! bash "$tools_dir/knowledge-provenance.sh" --unattended; then
    echo "knowledge-librarian: the change touches a person's record - refusing" >&2
    exit 3
  fi

  if [ "${KNOWLEDGE_RETRIEVAL:-}" = true ] && [ -f .lokf/scripts/knowledge-report.sh ]; then
    score_retrieval
  fi
}

main "$@"
