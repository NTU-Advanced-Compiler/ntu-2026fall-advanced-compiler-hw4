#!/usr/bin/env bash
# Usage: ./run_test_case.sh <testcase.bril> [program arguments...]
#
# Kept for compatibility with the interface used in previous years. This is
# now a thin wrapper around tools/evaluate.py, which checks that the program
# your driver produces is in SSA form and still behaves like the original.
# Nothing is written into the repository.

set -u

TESTCASE="${1:-}"

if [[ -z "$TESTCASE" ]]; then
  echo "Usage: $0 <testcase.bril> [program arguments...]" >&2
  exit 2
fi

if [[ ! -f "$TESTCASE" ]]; then
  echo "Error: test case '$TESTCASE' not found." >&2
  exit 2
fi
shift

ARGS=()
for a in "$@"; do
  ARGS+=(--arg "$a")
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$REPO_ROOT/tools/run_case.py" --file "$TESTCASE" ${ARGS[@]+"${ARGS[@]}"}
