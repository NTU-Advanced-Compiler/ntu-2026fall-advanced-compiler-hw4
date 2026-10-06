# Homework 4: SSA Construction for Bril

## Overview

In this homework, you will implement the SSA construction algorithm for the Bril intermediate representation (IR). The goal is to transform a given non-SSA Bril program into its SSA form with considering the optimization of eliminating redundant ϕ-functions. You will work through several modular components, each building upon the previous to achieve the final SSA-form program.

## Prerequisites

- Docker
- The homework image, which already contains Python 3, Deno and the Bril toolchain

## Getting Started

1. Clone the repository recursively, so that you get the Bril submodule:
   ```bash
   git clone --recursive https://github.com/NTU-Advanced-Compiler/ntu-2026fall-advanced-compiler-hw4.git
   cd ntu-2026fall-advanced-compiler-hw4
   ```

2. Pull the homework image and start a container with the repository mounted:
   ```bash
   docker pull ghcr.io/ntu-advanced-compiler/acd-hw4:2026
   docker run -it --rm -v "$PWD":/home/student/hw ghcr.io/ntu-advanced-compiler/acd-hw4:2026
   ```

   The repository appears inside the container at `/home/student/hw`. `bril2json`, `bril2txt` and `brili` are already installed.

## Project Structure
```
homework-directory/
├── src/
│   ├── driver.py
│   ├── bril.py
│   ├── cfg.py
│   ├── dominance.py
│   ├── is_ssa.py
│   └── ssa_construct.py
├── tests/
│   ├── simple.bril
│   ├── [additional test cases]
│   └── manifest.json
├── tools/
├── bril/
├── run_test_case.sh
├── verify_hw4.sh
├── Dockerfile
└── README.md
```

## Implementation Tasks

1. CFG Construction (`cfg.py`)
2. Dominator Computation (`dominance.py`)
3. Phi-Function Insertion (`ssa_construct.py`)
4. Variable Renaming (`ssa_construct.py`)

## Running and Testing

Run these inside the container.

1. To check your work the way it is graded:
```bash
bash verify_hw4.sh <student-id> test
```
All graded test cases are in this repository, so this reports the score you will receive. `tests/manifest.json` lists each case and the arguments it is run with.

2. To check a single test case, optionally with program arguments:
```bash
bash run_test_case.sh ./tests/[your_test_program].bril [arguments]
```
3. To generate the SSA form of your program:
```bash
bril2json < ./tests/[your_test_program].bril | python3 ./src/driver.py | bril2txt > output.bril
```
4. To check if the generated program is in SSA form:
```bash
bril2json < ./output.bril | python3 src/is_ssa.py
```
5. To compare the execution output of the original and transformed programs:
```bash
# Original program
bril2json < ./tests/[your_test_program].bril | brili [arguments] > original.out

# Transformed SSA program
bril2json < ./output.bril | brili [arguments] > transformed.out

# Compare outputs
diff original.out transformed.out
```

## Submission Instructions

1. Implement all required functionalities in the `src/` directory.
2. Test your implementation thoroughly.
3. Put your whole `src/` directory in a directory named after your student ID, with the first character in lower case, and compress it into a zip archive with the same name:
   ```
   r14922000.zip
   └── r14922000/
       └── src/
   ```
4. Upload the archive to NTU COOL. Do not include `bril/`, screenshots or test output.

You may submit more than once. **Only your last submission is graded.**

A late submission loses 10 points for each day it is late, and a submission more than five days late receives zero.

## Do and Don't

- You are allowed to modify any part of the starter code within the src/ directory, except for is_ssa.py, to suit your approach. While the current structure serves as a guideline, ensuring the driver script functions properly is key for grading.
- Make sure you have a solid understanding of the algorithm before starting your implementation.
- Grading runs `python3 src/driver.py`, which must read one Bril JSON program from stdin and write exactly one Bril JSON program to stdout, then exit 0. This applies to all code it imports: debugging output belongs on stderr.
- DO NOT import third-party packages or use features newer than Python 3.10. Grading runs under Python 3.10 with only the standard library and no network access, so either fails every test case.
- DO NOT rely on modifications to `src/is_ssa.py` or to anything outside the `src/` directory. Grading uses a pristine copy of `is_ssa.py`, and only your `src/` directory is collected, so such changes have no effect.
- DO NOT special-case a particular test case. The test cases are given to you to develop against, not to hard-code.

## Additional Resources

- Engineering a Compiler
- [Bril Language Reference](https://capra.cs.cornell.edu/bril/lang/index.html)
- Course lecture notes on SSA form and related algorithms
