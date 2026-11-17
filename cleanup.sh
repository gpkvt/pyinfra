
#!/usr/bin/env bash
set -euo pipefail

REPO="gpkvt/pyinfra"
KEEP=3
APPLY=false

if [[ "${1:-}" == "--apply" ]]; then
    APPLY=true
fi

command -v gh >/dev/null || {
    echo "GitHub CLI (gh) is required."
    exit 1
}

gh auth status

echo "Fetching releases..."
releases=$(gh api --paginate "repos/${REPO}/releases?per_page=100")

mapfile -t release_tags < <(
    jq -r 'sort_by(.published_at // .created_at) | reverse | .[].tag_name' <<< "$releases"
)

if (( ${#release_tags[@]} < KEEP )); then
    echo "Found fewer than ${KEEP} releases; refusing cleanup."
    exit 1
fi

declare -A keep_tags=()
for tag in "${release_tags[@]:0:KEEP}"; do
    keep_tags["$tag"]=1
done

echo
echo "Keeping:"
printf '  %s\n' "${release_tags[@]:0:KEEP}"

echo
echo "Older releases to delete:"
for tag in "${release_tags[@]:KEEP}"; do
    echo "  $tag"
done

echo
echo "Older tags to delete:"
mapfile -t all_tags < <(
    gh api --paginate "repos/${REPO}/tags?per_page=100" |
        jq -r '.[].name'
)

for tag in "${all_tags[@]}"; do
    if [[ -z "${keep_tags[$tag]+x}" ]]; then
        echo "  $tag"
    fi
done

if [[ "$APPLY" != true ]]; then
    echo
    echo "Dry run only. Review the list above."
    echo "Run with --apply to perform deletion."
    exit 0
fi

echo
read -r -p "Type DELETE to confirm: " confirmation
[[ "$confirmation" == "DELETE" ]] || exit 1

for tag in "${release_tags[@]:KEEP}"; do
    echo "Deleting release: $tag"
    release_id=$(jq -r --arg tag "$tag" \
        '.[] | select(.tag_name == $tag) | .id' <<< "$releases")
    gh api --method DELETE "repos/${REPO}/releases/${release_id}"
done

for tag in "${all_tags[@]}"; do
    if [[ -z "${keep_tags[$tag]+x}" ]]; then
        echo "Deleting tag: $tag"
        gh api --method DELETE "repos/${REPO}/git/refs/tags/${tag}"
    fi
done

echo "Cleanup completed."
