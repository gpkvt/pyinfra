# Releasing

This repository is an infrastructure configuration project, not a distributable
Python package. Releases are published as GitHub Releases; there is no PyPI
publishing step.

## Create a release

1. Merge the changes intended for the release into `main`.
2. Update `CHANGELOG.md` with a dated entry describing the changes.
3. Ensure your local checkout is clean and up to date, then run the release
   helper from the repository root:

   ```bash
   ./scripts/publish-release.sh v1.2.3
   ```

   The script verifies that:
   - the current branch is `main`;
   - the working tree is clean;
   - local `main` exactly matches the fetched `origin/main`;
   - `CHANGELOG.md` contains a dated release entry; and
   - the requested tag does not already exist locally or remotely.

   It displays the release tag and commit and asks for confirmation before
   creating an annotated tag and pushing it to `origin`. If pushing fails,
   the local tag is retained so you can inspect the remote state before retrying.

4. The `.github/workflows/release.yml` workflow validates the pushed tag and
   creates the GitHub Release with automatically generated notes.
5. Review the published release at
   [GitHub Releases](https://github.com/gpkvt/pyinfra/releases).

Use `vMAJOR.MINOR.PATCH` tags. Pre-release and build metadata are accepted,
for example `v1.1.0-rc.1` and `v1.1.0+build.2`. The workflow does not build
or upload Python distribution artifacts. Merging a pull request does not
publish a release; publishing starts only after a version tag is pushed (or
the workflow is manually dispatched).

A tag is immutable release history: if a release needs correction, publish a
new patch version rather than moving an existing tag.
