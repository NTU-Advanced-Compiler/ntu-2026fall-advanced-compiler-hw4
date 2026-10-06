"""Run the HW4 test cases with the same evaluator the TAs use.

Usage (from the repository root, inside the homework container):

    python3 tools/selfcheck.py [--json] [--case ID] [--timeout SECONDS]

There are no hidden test cases. Every case that decides your grade is in
tests/manifest.json, so the score printed here is the score you get,
provided your submission is packaged correctly.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evaluate  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true',
                        help='print machine-readable results')
    parser.add_argument('--case', action='append', dest='cases',
                        help='run only this case id (repeatable)')
    parser.add_argument('--timeout', type=int, default=evaluate.DEFAULT_TIMEOUT,
                        help='per-stage time limit in seconds')
    parser.add_argument('--manifest',
                        default=os.path.join(REPO_ROOT, 'tests',
                                             'manifest.json'))
    parser.add_argument('--src', default=os.path.join(REPO_ROOT, 'src'),
                        help='directory holding your source files')
    args = parser.parse_args()

    cases = evaluate.load_manifest(args.manifest)
    if args.cases:
        wanted = set(args.cases)
        cases = [c for c in cases if c['id'] in wanted]
        if not cases:
            parser.error('no case matched {}'.format(sorted(wanted)))

    if not os.path.isdir(args.src):
        print('ERROR: {} not found.'.format(args.src), file=sys.stderr)
        return 2

    # The supplied is_ssa.py is always taken from the repository, so the
    # self-check matches grading even if you edited your local copy.
    ta_src = os.path.join(REPO_ROOT, 'src')
    report = evaluate.evaluate_all(cases, REPO_ROOT, args.src, ta_src,
                                   args.timeout)

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write('\n')
        return 0 if report['score'] == report['max_score'] else 1

    print('=' * 68)
    print('ACD HW4 self-check')
    print('=' * 68)
    for res in report['results']:
        status = 'PASS' if res['passed'] else 'FAIL'
        print()
        print('[{}] {:<14} {:>4}/{:<3}'.format(
            status, res['id'], res['points'], res['max_points']))
        for msg in res['messages']:
            print('       {}'.format(msg))

    print()
    print('-' * 68)
    print('TOTAL SCORE: {} / {}'.format(report['score'], report['max_score']))
    print('(This is the full graded suite; there are no hidden cases.)')
    print('=' * 68)
    return 0 if report['score'] == report['max_score'] else 1


if __name__ == '__main__':
    sys.exit(main())
