#!/usr/bin/env bash
#
# Wrapper for the scheduled knowledge-librarian loop (Karpathy rule).
#
# `.github/workflows/knowledge-librarian.yaml` invokes this script directly - a
# fixed, reviewed path, not an arbitrary command from a repo variable. To arm the
# scheduled run, set the `KNOWLEDGE_LIBRARIAN_ENABLED` repository variable to
# "true", and set `AGENT_CLI` (repo variable or secret) to the command that runs
# your coding agent non-interactively - e.g. the GitHub Copilot CLI or an internal
# agent runner that accepts a prompt on `-p`/stdin.
#
# CONTRACT (the workflow relies on this):
#   - This script only READS the repo and WRITES files under .lokf/knowledge/
#     (the workflow diffs and commits that path only; tooling files are
#     ktl-sidecar's domain).
#   - It MUST NOT git commit, push, or open PRs - the workflow owns that.
#   - On success it exits 0 whether or not it changed anything; the workflow
#     diffs the working tree to decide whether to open a PR.
#
# Inputs (env):
#   AGENT_CLI           command that runs the agent given a prompt via -p "<prompt>"
#   AGENT_API_KEY       optional: the agent's API key or token, from a secret
#   AGENT_API_KEY_ENV   the name the agent reads that key from, such as
#                       ANTHROPIC_API_KEY; required when AGENT_API_KEY is set
#
set -euo pipefail

# Resolve the repo root from this script's location so it works regardless of cwd.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

# The ktl-librarian skill may live under any of these skill-directory
# conventions - the three install targets, plus bare skills/ for a repo that
# publishes the skills it also uses. If this repo uses a different one, add it here - a candidate
# list that doesn't match reality fails this whole script at run time, not at
# scaffold time.
skill=""
for candidate in .claude/skills/ktl-librarian/SKILL.md .github/skills/ktl-librarian/SKILL.md \
                 .agents/skills/ktl-librarian/SKILL.md skills/ktl-librarian/SKILL.md; do
  if [ -f "$candidate" ]; then skill="$candidate"; break; fi
done
[ -n "$skill" ] || {
  echo "knowledge-librarian: ktl-librarian SKILL.md not found in .claude/skills/, .github/skills/, .agents/skills/, or skills/" >&2
  exit 2
}

if [ -z "${AGENT_CLI:-}" ]; then
  cat >&2 <<'EOF'
knowledge-librarian: AGENT_CLI is not set.

Set AGENT_CLI to your non-interactive agent command (e.g. a Copilot CLI or
internal runner). This wrapper hands it a prompt built from the ktl-librarian
skill; the agent is expected to edit files under .lokf/knowledge/ only.
EOF
  exit 2
fi

# The workflow passes the key under one fixed name, and the agent CLI reads it
# under its own. Check the name here, before anything runs: it must look like a
# credential (ending _API_KEY, _TOKEN or _KEY), so a slip cannot overwrite
# PATH, BASH_ENV or LD_PRELOAD. It must not start GITHUB_, GH_, GIT_, RUNNER_ or
# ACTIONS_, because gh, git and the runner read those names too, and the key
# would reach them as well as the agent. The key moves into an unexported
# variable, so the git commands this script runs never see it.
key_name="${AGENT_API_KEY_ENV:-}"
agent_key="${AGENT_API_KEY:-}"
unset AGENT_API_KEY AGENT_API_KEY_ENV
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

# Build the prompt. The agent should follow the skill verbatim, edit only the
# .lokf/knowledge/ bundle, and make no VCS operations.
# The heredoc is unquoted so $skill expands - which means any backtick in the
# text MUST be escaped (\`) or bash runs it as a command and blanks the word.
prompt="$(cat <<EOF
You are the repository knowledge librarian. Follow this skill file verbatim:
  - $skill

Task (Karpathy rule - continuous small corrections, not a rewrite):
  1. Follow the skill's Scrape & build procedure: bootstrap discovery if the
     bundle has no real concepts yet, otherwise the steady-state refresh of the
     sources recorded in the bundle (concept provenance and
     .lokf/knowledge/playbooks/knowledge-sources.md).
  2. Reconcile the .lokf/ knowledge bundle with the repository: add missing
     concepts, correct stale facts (refreshing each changed concept's
     \`generated\` provenance, which supersedes the v0.1 \`timestamp\`), wire
     typed relations, and prepend dated entries to
     .lokf/knowledge/log.md - but only when the bundle content actually
     changed. If nothing changed, leave the bundle (including log.md)
     untouched; do not log administrative no-op runs.
  3. Only edit files under .lokf/knowledge/. Do NOT run git, open PRs, or touch
     any other path. Cite sources for any claim whose authority is outside the
     repository.
  4. Mark concepts you create, and claims you cannot settle from the
     repository, as \`status: draft\` (with a plain-prose "## Open questions"
     section for the latter), exactly as the skill says. End your reply with a
     short "For the curator" summary: how many concepts are drafts, which
     carry open questions, and how many are confirmed by a person.
EOF
)"

# Security rationale (for human and automated reviewers): AGENT_CLI is trusted
# configuration, not untrusted input - a repo admin sets it in Settings (the
# operator naming their own agent command); it is never derived from repo
# contents, PR data, or model output. It is parsed into a quoted argv array and
# run directly (see below), so bash does NOT re-evaluate it as source: shell
# metacharacters (; | & $() ``) are passed as inert arguments, not executed -
# there is no eval and no `bash -c`. This step runs only in the workflow's
# read-only `refresh` job (contents: read, no persisted credentials), and the
# post-run check further fails if the agent wrote outside .lokf/knowledge/.
# That check, and the AGENT_CLI invocation itself, live inside main() below,
# called only from this file's last line: bash reads a function body in full
# before running any of it, so - unlike the top-level statements this used to
# be - nothing after the agent call can be skipped by an agent that truncates
# this script mid-run (bash otherwise just stops at whatever the file's
# current length on disk is when it gets there).
#
# Split AGENT_CLI into an argv array (whitespace word-split, no globbing) and
# invoke it as a quoted vector rather than a re-expanded string. Handles the
# usual "cmd --flags" form; quotes *inside* AGENT_CLI are not honoured - keep it
# to a plain command plus flags, or wrap richer logic in its own script.
read -r -a agent_cmd <<< "$AGENT_CLI"
if [ "${#agent_cmd[@]}" -eq 0 ]; then
  echo "knowledge-librarian: AGENT_CLI has no command after parsing" >&2
  exit 2
fi

# Defence in depth: the prompt asks the agent to edit only .lokf/knowledge/, but
# nothing forces it. Record paths already dirty outside the bundle (e.g. a
# uv.lock the workflow refreshed) so the agent is held to account only for *new*
# ones. Allowed: the bundle under either of its two names - .lokf/knowledge/,
# and knowledge_bundle/, which is ktl-sidecar's doorway link by default (then
# the pathspec matches nothing) but a real folder on a host rearranged by hand
# with .lokf/knowledge a link onto it (git pathspecs do not traverse a symlink,
# so both must be named) - plus ktl-docent's .lokf/feedback.md.
outside_bundle() {
  git status --porcelain -- '.' \
    ':(exclude).lokf/knowledge' ':(exclude)knowledge_bundle' ':(exclude).lokf/feedback.md' \
    | cut -c4- | sort -u
}

# Snapshots of .git/config and .git/hooks/ taken by main() before the agent
# runs. File-scope, not local, so the EXIT trap below can reach them.
config_snapshot=""
hooks_snapshot=""

# Put .git/config and .git/hooks/ back as they were before the agent ran, then
# forget the snapshot so a second call is a no-op. Called explicitly right after
# the agent returns, and again from the EXIT trap for every other way out: the
# agent exiting non-zero (which `set -e` turns into this script's exit), the job
# being cancelled (the runner's SIGINT/SIGTERM, handled below by exiting), or an
# error anywhere after the snapshot. Without the trap, a failing agent left its
# poisoned config in the checkout for the workflow's next steps to read.
restore_git_state() {
  [ -n "$config_snapshot" ] || return 0
  cp "$config_snapshot" .git/config
  rm -rf .git/hooks
  mkdir .git/hooks
  cp -a "$hooks_snapshot/." .git/hooks/
  rm -rf "$config_snapshot" "$hooks_snapshot"
  config_snapshot=""
  hooks_snapshot=""
}

main() {
  # A local, well-formed AGENT_CLI can still run code that writes anywhere in
  # this job's checkout - that's what the check above is for. But that check
  # is only as good as the `git status` it reads: an agent that sets
  # core.fsmonitor or core.hooksPath in .git/config, or drops a file in
  # .git/hooks/, gets it run by *this script's own* later git commands (and
  # by the workflow's separate detect/package steps after this script exits,
  # which share this job's checkout). Snapshot both around the agent call and
  # restore them on every exit - success, agent failure, cancellation - so
  # neither this check nor anything the workflow does afterwards can be
  # blinded or hijacked that way. Only SIGKILL escapes this; a runner that
  # kills the step outright also discards the job, so nothing reads the
  # checkout after it. This is defence in depth, not the actual backstop - a
  # human reviewing the PR before merge is.
  config_snapshot="$(mktemp)"
  hooks_snapshot="$(mktemp -d)"
  cp .git/config "$config_snapshot"
  cp -a .git/hooks/. "$hooks_snapshot/"
  trap restore_git_state EXIT
  # A signal caught by a trap does not end the shell, so these turn it into an
  # exit, which runs the EXIT trap above. bash delivers them only once the
  # foreground agent has itself exited, so the restore never races the agent.
  trap 'exit 129' HUP
  trap 'exit 130' INT
  trap 'exit 143' TERM

  local before_outside
  before_outside="$(outside_bundle)"

  echo "knowledge-librarian: refreshing the .lokf/ bundle via AGENT_CLI"
  # The subshell exports the key under the agent's own name and then becomes
  # the agent, so only the agent's environment carries it. The key never
  # appears in a process's argument list.
  (
    if [ -n "$key_name" ]; then export "$key_name=$agent_key"; fi
    exec "${agent_cmd[@]}" -p "$prompt"
  )

  # Restore before the check below reads git, not only at exit.
  restore_git_state

  local stray
  stray="$(comm -13 <(printf '%s\n' "$before_outside") <(outside_bundle))"
  if [ -n "${stray//[$'\n\t ']/}" ]; then
    echo "knowledge-librarian: agent modified paths outside .lokf/knowledge/ - refusing:" >&2
    printf '%s\n' "$stray" | sed '/^$/d; s/^/  /' >&2
    exit 3
  fi
}

main "$@"
