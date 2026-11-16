# Releasing

This repository is an infrastructure configuration project, not a distributable
Python package. Releases are published as GitHub Releases; there is no PyPI
publishing step.

## Create a release

1. Merge the changes intended for the release into `main`.
2. Update `CHANGELOG.md` with a dated entry describing the changes.
3. Create and push an annotated semantic-version tag from the release commit:

   ```bash
   git switch main
   git pull --ff-only
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

4. The `.github/workflows/release.yml` workflow validates the tag and creates
   the GitHub Release with automatically generated notes.
5. Review the published release at
   [GitHub Releases](https://github.com/gpkvt/pyinfra/releases).

Use `vMAJOR.MINOR.PATCH` tags. Pre-release and build metadata are accepted,
for example `v1.1.0-rc.1` and `v1.1.0+build.2`. The workflow does not build
or upload Python distribution artifacts.

A tag is immutable release history: if a release needs correction, publish a
new patch version rather than moving an existing tag.
