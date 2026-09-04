# Repository visibility review: public → private

**Status:** waiting for review by @allansene

## Context

During the 2026-09-04 GitHub hygiene pass over the `dadosfera` organization,
this repository was flagged as a candidate to switch from **public** to
**private**:

- it holds project artifacts and assets (Dashboard, PAIRS, analyses, DATASUS
  data, presentations) rather than public-facing examples or utilities;
- it is actively pushed to (last push 2026-09-03);
- it already has 3 external forks, which keep a copy of everything that is
  public today regardless of what we decide.

## Decision needed

- [ ] Keep public (close this PR without merging)
- [ ] Make private (merge this PR, then an org admin flips the setting)

Making the repo private orphans the 3 existing forks and revokes access for
anyone who is not a collaborator or org member.

## Related

- `dadosfera/3d-ddf` and `dadosfera/enrich-ddf-floor-2` were switched to
  private in the same pass.
