<!-- A sidecar sync. The lines above this template are the sync's: the release, the files it changed and the pin. The workflow leaves the sidecar's checks to this pull request's own checks; a sync opened by hand with .lokf/scripts/knowledge-sync.sh --pr <tag> writes its check lines above too. -->

## Reviewer checklist

- [ ] The diff touches only the sidecar's copies, the site's copies, the skills pin and `CHANGELOG.md`.
- [ ] `TRUST_LADDER_SKILLS_REF` names the release, and `TRUST_LADDER_SKILLS_SHA` the commit that tag names.
- [ ] The release notes of Knowledge Trust Ladder ask nothing of this repository that the diff leaves undone.
- [ ] `CHANGELOG.md` has the entry under `## [Unreleased]` and `### Security`, and the title carries `security(sidecar):`, so the merge releases.
