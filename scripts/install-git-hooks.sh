#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

chmod +x .githooks/pre-commit
git config core.hooksPath .githooks

printf 'Installed git hooks at %s/.githooks\n' "${REPO_ROOT}"
