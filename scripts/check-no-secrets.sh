#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_FILE="$(mktemp)"
trap 'rm -f "${TMP_FILE}"' EXIT

patterns=(
  'ghp_[A-Za-z0-9]{20,}'
  'sbp_[A-Za-z0-9]{20,}'
  'AIza[0-9A-Za-z_-]{20,}'
  'sk-[A-Za-z0-9_-]{20,}'
  'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
  'https?://100\.'
  'https?://10\.'
)

user_path_pattern="/Users/""nico/"
home_path_pattern="/home/""nico/"
root_path_pattern="/ro""ot/"
patterns+=("${user_path_pattern}" "${home_path_pattern}" "${root_path_pattern}")

scan_failed=0

for pattern in "${patterns[@]}"; do
  if grep -RInE --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude='*.pyc' "${pattern}" "${REPO_ROOT}" >"${TMP_FILE}"; then
    printf 'FAIL: matched sensitive pattern %s\n' "${pattern}" >&2
    cat "${TMP_FILE}" >&2
    scan_failed=1
  fi
done

if [[ ${scan_failed} -ne 0 ]]; then
  exit 1
fi

printf 'PASS: no secret-like or machine-specific patterns detected\n'
