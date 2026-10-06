"""Strict evaluator for the HW4 SSA construction pipeline.

This module is the single authority for whether a test case passes. It is
used by the student self-check (`verify_hw4.sh`) and by the TA batch
grader, so both agree on every decision.

A case passes only if the transformed program is in SSA form and behaves
exactly like the original on every argument set.

Each stage of the pipeline runs as its own subprocess, and every stage is
checked independently for exit status, timeout, output size, and complete
parseable JSON. Nothing is written to the repository; each case runs in
its own temporary directory.
"""
import json
import os
import shutil
import subprocess
import tempfile

# Modules that belong to the TAs. The SSA check always runs against
# pristine copies of these, so a student's edits can never change what
# counts as SSA form.
TA_MODULES = ('is_ssa.py', 'bril.py')

# The entry point of the student's implementation.
STUDENT_ENTRY = 'driver.py'

DEFAULT_TIMEOUT = 10          # seconds per stage
MAX_OUTPUT_BYTES = 8 << 20    # 8 MiB per stage


class StageError(Exception):
    """A pipeline stage failed. The message is shown to the student."""

    def __init__(self, stage, detail):
        super(StageError, self).__init__('{}: {}'.format(stage, detail))
        self.stage = stage
        self.detail = detail


def _run(cmd, stdin_bytes, timeout=DEFAULT_TIMEOUT, cwd=None, stage='stage'):
    """Run one stage. Returns (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        raise StageError(stage, 'exceeded the {}s time limit'.format(timeout))
    except FileNotFoundError:
        raise StageError(stage, 'command not found: {}'.format(cmd[0]))
    if len(proc.stdout) > MAX_OUTPUT_BYTES:
        raise StageError(stage, 'produced more than {} bytes of output'
                         .format(MAX_OUTPUT_BYTES))
    return proc.returncode, proc.stdout, proc.stderr


def _decode(data):
    return data.decode('utf-8', errors='replace')


def _checked(cmd, stdin_bytes, stage, timeout, cwd=None):
    """Run a stage that must exit 0 and return its stdout."""
    rc, out, err = _run(cmd, stdin_bytes, timeout, cwd=cwd, stage=stage)
    if rc != 0:
        raise StageError(stage, 'exit status {} (stderr: {})'
                         .format(rc, _decode(err).strip()[-400:] or 'empty'))
    return out


def bril2json(bril_path, timeout=DEFAULT_TIMEOUT):
    """Convert a Bril text program to canonical JSON bytes."""
    with open(bril_path, 'rb') as fh:
        source = fh.read()
    return _checked(['bril2json'], source, 'bril2json', timeout)


def run_driver(module_dir, json_bytes, timeout=DEFAULT_TIMEOUT):
    """Run the student's driver and return its output JSON bytes.

    The driver must read exactly one Bril JSON object from stdin and
    write exactly one Bril JSON object to stdout. Anything it writes to
    stderr is ignored, so debugging output there is harmless.
    """
    stage = 'your driver.py'
    out = _checked(['python3', STUDENT_ENTRY], json_bytes, stage, timeout,
                   cwd=module_dir)
    if not out.strip():
        raise StageError(stage, 'wrote nothing to stdout')
    try:
        parsed = json.loads(out.decode('utf-8'))
    except UnicodeDecodeError:
        raise StageError(stage, 'stdout was not valid UTF-8')
    except json.JSONDecodeError as exc:
        raise StageError(stage, 'stdout was not one complete JSON object ({})'
                         .format(exc))
    if not isinstance(parsed, dict) or 'functions' not in parsed:
        raise StageError(stage, 'stdout was not a Bril program '
                                '(no "functions" key)')
    return out


def roundtrip(json_bytes, timeout=DEFAULT_TIMEOUT):
    """Print the program as Bril text and parse it back.

    This rejects output that is JSON but not a well-formed Bril program.
    """
    text = _checked(['bril2txt'], json_bytes,
                    'bril2txt on your output', timeout)
    return _checked(['bril2json'], text,
                    'bril2json on your output', timeout)


def is_ssa(ta_exec, json_bytes, timeout=DEFAULT_TIMEOUT):
    """Run the supplied SSA check. Returns True if the program is SSA."""
    rc, _, _ = _run(['python3', 'is_ssa.py'], json_bytes, timeout,
                    cwd=ta_exec, stage='supplied is_ssa.py')
    return rc == 0


def interpret(json_bytes, args, timeout=DEFAULT_TIMEOUT):
    """Run a Bril program under the interpreter.

    Returns a dict with the program's stdout and its exit status. A
    program that exits nonzero is a valid observation, not an evaluator
    error: the original and the transformed program simply have to agree.
    """
    cmd = ['brili'] + [str(a) for a in args]
    rc, out, err = _run(cmd, json_bytes, timeout, stage='brili')
    return {
        'stdout': _decode(out),
        'status': rc,
        'stderr': _decode(err),
    }


def build_exec_dirs(student_src, ta_src, workdir):
    """Create the two directories the pipeline stages run in.

    `ta_exec` holds pristine TA modules and is where the supplied SSA
    check runs, so it behaves identically for every submission.

    `student_exec` starts from the starter files in the repository and
    is then overlaid with the student's files, including any helper
    modules they added. A submission therefore only has to contain the
    files the student changed.
    """
    if not os.path.isdir(student_src):
        raise StageError('submission layout',
                         'source directory not found: {}'.format(student_src))
    ta_exec = os.path.join(workdir, 'ta_exec')
    student_exec = os.path.join(workdir, 'student_exec')
    os.makedirs(ta_exec, exist_ok=True)
    os.makedirs(student_exec, exist_ok=True)

    for name in TA_MODULES:
        shutil.copy2(os.path.join(ta_src, name), os.path.join(ta_exec, name))

    # Subdirectories are copied too, so a submission may organize its
    # helper modules into packages.
    for source_dir in (ta_src, student_src):
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = sorted(d for d in dirs if d != '__pycache__')
            target = os.path.join(student_exec,
                                  os.path.relpath(root, source_dir))
            os.makedirs(target, exist_ok=True)
            for name in sorted(files):
                if name.endswith('.py'):
                    shutil.copy2(os.path.join(root, name),
                                 os.path.join(target, name))
    return ta_exec, student_exec


def evaluate_case(case, repo_root, student_src, ta_src, timeout=DEFAULT_TIMEOUT):
    """Evaluate one case and return a result dict.

    `points` is awarded only if the output is in SSA form and behaves
    like the original on every argument set.
    """
    result = {
        'id': case['id'],
        'category': case.get('category', 'uncategorized'),
        'max_points': case['points'],
        'points': 0,
        'passed': False,
        'messages': [],
        'runs': [],
    }
    bril_path = os.path.join(repo_root, case['file'])
    arg_sets = case.get('arg_sets') or [[]]

    workdir = tempfile.mkdtemp(prefix='hw4case.')
    try:
        try:
            ta_exec, student_exec = build_exec_dirs(student_src, ta_src,
                                                    workdir)
            original = bril2json(bril_path, timeout)
            transformed = roundtrip(
                run_driver(student_exec, original, timeout), timeout)
            if not is_ssa(ta_exec, transformed, timeout):
                result['messages'].append(
                    'NOT SSA: the transformed program assigns some '
                    'variable more than once')
                return result
        except StageError as exc:
            result['messages'].append('FAILED in {}'.format(exc))
            return result

        all_match = True
        for args in arg_sets:
            try:
                base = interpret(original, args, timeout)
                new = interpret(transformed, args, timeout)
            except StageError as exc:
                result['messages'].append('FAILED in {}'.format(exc))
                return result

            result['runs'].append({
                'args': args,
                'original_stdout': base['stdout'],
                'transformed_stdout': new['stdout'],
                'original_status': base['status'],
                'transformed_status': new['status'],
            })

            label = 'args {}'.format(args) if args else 'no arguments'
            if base['stdout'] != new['stdout']:
                all_match = False
                result['messages'].append(
                    'WRONG OUTPUT with {}: original printed {!r}, '
                    'your SSA program printed {!r}'.format(
                        label, base['stdout'], new['stdout']))
            elif base['status'] != new['status']:
                all_match = False
                result['messages'].append(
                    'WRONG COMPLETION STATUS with {}: original exited {}, '
                    'your SSA program exited {} (stderr: {})'.format(
                        label, base['status'], new['status'],
                        new['stderr'].strip()[-200:] or 'empty'))

        if all_match:
            result['messages'].append('OK: SSA form, behavior preserved')
            result['passed'] = True
            result['points'] = case['points']
        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def load_manifest(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)['cases']


def evaluate_all(cases, repo_root, student_src, ta_src,
                 timeout=DEFAULT_TIMEOUT):
    results = [evaluate_case(c, repo_root, student_src, ta_src, timeout)
               for c in cases]
    return {
        'results': results,
        'score': sum(r['points'] for r in results),
        'max_score': sum(r['max_points'] for r in results),
    }
