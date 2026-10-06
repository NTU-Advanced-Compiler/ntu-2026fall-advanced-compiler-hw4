#!/usr/bin/env bash
# ACD HW4 self-check. Same shape as HW1's verify_hw1.sh.
#
#   bash verify_hw4.sh <student-id> info
#   bash verify_hw4.sh <student-id> test
#
# `info` prints the environment and a checksum of each file in src/.
# `test` runs the public test cases with the same evaluator the TAs use
# and prints a score summary.

set -u
set -o pipefail

usage() {
    echo "Usage:"
    echo "  bash verify_hw4.sh <student_id> info"
    echo "  bash verify_hw4.sh <student_id> test"
}

if [[ $# -ne 2 ]]; then
    usage
    exit 1
fi

STUDENT_ID="$1"
MODE="$2"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTRY="$REPO_ROOT/src/driver.py"

print_identity() {
    echo "============================================================"
    echo "ACD HW4 Verification"
    echo "============================================================"
    echo "Student ID        : $STUDENT_ID"
    echo "Timestamp         : $(date -Iseconds)"
    echo "Working directory : $(pwd)"
    echo
}

print_system_info() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        echo "Operating system  : ${PRETTY_NAME:-unknown}"
    else
        echo "Operating system  : unknown"
    fi
    echo "Architecture      : $(uname -m)"
    echo "Python            : $(python3 --version 2>&1)"
    echo "bril2json         : $(command -v bril2json || echo NOT FOUND)"
    echo "brili             : $(command -v brili || echo NOT FOUND)"
}

require_tools() {
    local missing=0 tool
    for tool in bril2json bril2txt brili python3; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "ERROR: $tool is not on PATH."
            missing=1
        fi
    done
    if [[ "$missing" -ne 0 ]]; then
        echo
        echo "Run this script inside the HW4 container, where the Bril tools"
        echo "are already installed:"
        echo "  docker run -it --rm -v \"\$PWD\":/home/student/hw acd-hw4:2026"
        exit 1
    fi
}

run_info() {
    print_identity
    print_system_info
    echo
    echo "---------------- src/ ----------------"
    if [[ ! -f "$ENTRY" ]]; then
        echo "ERROR: src/driver.py not found."
        exit 1
    fi
    echo
    echo "SHA256:"
    (cd "$REPO_ROOT" && sha256sum src/*.py)
    echo
    echo "---------------- End of info output ----------------"
}

run_test() {
    print_identity
    print_system_info
    require_tools

    if [[ ! -f "$ENTRY" ]]; then
        echo "ERROR: src/driver.py not found."
        exit 1
    fi

    echo
    echo "SHA256:"
    (cd "$REPO_ROOT" && sha256sum src/*.py)

    echo
    python3 "$REPO_ROOT/tools/selfcheck.py"
    exit $?
}

case "$MODE" in
    info) run_info ;;
    test) run_test ;;
    *) usage; exit 1 ;;
esac
