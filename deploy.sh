#!/usr/bin/env bash
set -euo pipefail

echo "MEX-WarSystem: safe branch validation"

if [[ ! -f "main.py" || ! -f "requirements.txt" || ! -f "render.yaml" ]]; then
  echo "Required application or Render files are missing." >&2
  exit 1
fi

branch="$(git branch --show-current)"
if [[ -z "$branch" || "$branch" == "main" ]]; then
  echo "Refusing to push from main. Use the reviewed repair branch and open a pull request." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree has uncommitted changes. Commit or review them before pushing." >&2
  exit 1
fi

python -m compileall -q .
python -m unittest discover -s tests -v

git push --set-upstream origin "$branch"

echo
echo "Branch pushed without force. Review the pull request and CI before merging."
echo "This script does not deploy to Render or claim production readiness."
