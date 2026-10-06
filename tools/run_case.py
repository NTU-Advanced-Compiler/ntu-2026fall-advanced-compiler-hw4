"""Evaluate a single ad-hoc test case. Used by run_test_case.sh."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', required=True)
    parser.add_argument('--arg', action='append', default=[],
                        help='an argument to pass to the program')
    parser.add_argument('--timeout', type=int,
                        default=evaluate.DEFAULT_TIMEOUT)
    parser.add_argument('--src', default=os.path.join(REPO_ROOT, 'src'))
    args = parser.parse_args()

    case = {
        'id': os.path.basename(args.file),
        'file': os.path.relpath(os.path.abspath(args.file), REPO_ROOT),
        'category': 'ad_hoc',
        'points': 1,
        'arg_sets': [args.arg],
    }
    res = evaluate.evaluate_case(case, REPO_ROOT, args.src,
                                 os.path.join(REPO_ROOT, 'src'), args.timeout)

    print('PASS' if res['passed'] else 'FAIL')
    for msg in res['messages']:
        print(msg)
    return 0 if res['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
