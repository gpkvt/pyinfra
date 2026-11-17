#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "Error: run this script inside a Git repository." >&2
    exit 1
}
readonly REPOSITORY_ROOT
cd "$REPOSITORY_ROOT"

usage() {
    echo "Usage: $0 vMAJOR.MINOR.PATCH"
}

if [[ $# -ne 1 ]]; then
    usage
    exit 2
fi

release_tag="$1"
version_pattern='^v[0-9]+\.[0-9]+\.[0-9]+'
version_pattern+='(-[0-9A-Za-z.-]+)?'
version_pattern+='(\+[0-9A-Za-z.-]+)?'
version_pattern+='$'

if [[ ! "$release_tag" =~ $version_pattern ]]; then
    echo "Error: invalid semantic version: $release_tag" >&2
    exit 1
fi

if [[ "$(git branch --show-current)" != "main" ]]; then
    echo "Error: releases must be published from main." >&2
    exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Error: working tree is not clean." >&2
    exit 1
fi

if [[ ! -s CHANGELOG.md ]] ||
   ! grep -Eq '^## \[[0-9]{2}\.[0-9]{2}\.[0-9]{4}\]$' CHANGELOG.md; then
    echo "Error: CHANGELOG.md has no dated release entry." >&2
    exit 1
fi

git fetch origin '+refs/heads/main:refs/remotes/origin/main' --tags

if ! git merge-base --is-ancestor origin/main HEAD; then
    echo "Error: local main is not based on origin/main." >&2
    exit 1
fi

if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
    echo "Error: local main is not up to date with origin/main." >&2
    exit 1
fi

if git show-ref --verify --quiet "refs/tags/$release_tag"; then
    echo "Error: tag already exists locally: $release_tag" >&2
    exit 1
fi

if ! remote_tags="$(git ls-remote --tags origin \
    "refs/tags/$release_tag" "refs/tags/$release_tag^{}")"; then
    echo "Error: unable to check whether the release tag exists remotely." >&2
    exit 1
fi

if [[ -n "$remote_tags" ]]; then
    echo "Error: tag already exists remotely: $release_tag" >&2
    exit 1
fi

echo "Release: $release_tag"
echo "Commit:  $(git rev-parse --short HEAD)"
echo
read -r -p "Create and push this release tag? [y/N] " confirmation

if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

git tag -a "$release_tag" -m "Release $release_tag"

if ! git push origin "refs/tags/$release_tag"; then
    echo "Error: pushing failed. The local tag was retained." >&2
    echo "Check the remote before retrying." >&2
    exit 1
fi

echo "Release tag pushed successfully."
echo "Create the GitHub Release manually from this tag."
echo "https://github.com/gpkvt/pyinfra/releases/new?tag=$release_tag"
