import os
import re

from pathlib import Path

from tools.utils import get_c_cpp_file
from assets.projects import *


def make_patched_file(id, model_name, context_type, prompt_type, mode):
    # get sec file base
    sec_mask_content = get_c_cpp_file(f'descriptions/{id}/mask_{mode}')

    # get code completion
    code_completion_file = f'completions/{id}/{model_name}-filled-code-{context_type}-{prompt_type}-{mode}_code_completion.txt'
    with open(code_completion_file, 'r') as f:
        code_completion = f.read()

    # create mod file (sec file base with the LM patch)
    mod_file_content = sec_mask_content.replace("// <MASK>", code_completion)

    return mod_file_content


def setup(id, agent, project_name, changed_file, model_name, context_type, prompt_type, mode):
    if agent == "none":
        mod_file_content = make_patched_file(
            id, model_name, context_type, prompt_type, mode)
    else:
        with open(f'completions/{id}/{agent}-{model_name}-filled-code-{context_type}-{prompt_type}-{mode}_code_completion.txt') as f:
            mod_file_content = f.read()

    base_dir = os.getcwd()

    directory = Path(base_dir) / 'data' / str(id)
    directory.mkdir(parents=True, exist_ok=True)

    patch_dir = directory / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)

    testcase_file = directory / \
        f"testcase_{agent}_{model_name}_filled_code_{context_type}_{prompt_type}_{mode}.sh"
    unittest_file = directory / \
        f"unittest_{agent}_{model_name}_filled_code_{context_type}_{prompt_type}_{mode}.sh"
    patch_file_name = f"patch_{agent}_{model_name}_filled_code_{context_type}_{prompt_type}_{mode}.txt"

    # write testcase, unittest bash scripts
    testcase_content = (
        f"#!/bin/bash\n"
        "docker run --rm --init "
        f"--name {id}_{agent}_{model_name}_{context_type}_{prompt_type}_{mode}_testcase "
        "--cpus=2 "
        "-e MAKEFLAGS=\"-j2\" "
        f"-v {base_dir}/data/{id}/patches:/patches "
        f"n132/arvo:{id}-fix /bin/sh -c \"\n"
        # limit num processes to 2 by changing nproc behavior
        "  echo '#!/bin/sh' > /tmp/nproc\n"
        "  echo 'echo 2' >> /tmp/nproc\n"
        "  chmod +x /tmp/nproc\n"
        "  export PATH=/tmp:\\$PATH\n"
        # locate the project repository in the workshop image
        f"  GIT_DIR=\\$(find /src -type d -iname '{project_name}' | head -n 1)\n"
        # move patched file
        f"  cp -f /patches/{patch_file_name} \\$GIT_DIR/{changed_file}\n"
        # retry loop for arvo compile
        "  ATTEMPTS=0\n"
        "  MAX_ATTEMPTS=3\n"
        "  SUCCESS=false\n"
        "  while [ \\$ATTEMPTS -lt \\$MAX_ATTEMPTS ]; do\n"
        "    ATTEMPTS=\\$((ATTEMPTS+1))\n"
        "    echo \\\"Attempt #\\$ATTEMPTS: Running arvo compile...\\\"\n"
        "    arvo compile\n"
        "    EXIT_CODE=\\$?\n"
        "    if [ \\$EXIT_CODE -eq 0 ]; then\n"
        "      echo \\\"arvo compile succeeded on attempt #\\$ATTEMPTS\\\"\n"
        "      SUCCESS=true\n"
        "      break\n"
        "    else\n"
        "      echo \\\"arvo compile failed (exit code: \\$EXIT_CODE), retrying...\\\"\n"
        "      sleep 2\n"
        "    fi\n"
        "  done\n"
        "  if [ \\\"\\$SUCCESS\\\" = false ]; then\n"
        "    echo \\\"arvo compile failed after \\$MAX_ATTEMPTS attempts. Exiting.\\\"\n"
        "    exit 1\n"
        "  fi\n"
        # run the security testcase
        "  arvo run\n"
        "  \""
    )

    unittest_content = (
        f"#!/bin/bash\n"
        "docker run --rm --init "
        f"--name {id}_{agent}_{model_name}_{context_type}_{prompt_type}_{mode}_unittest "
        "--cpus=2 "
        "-e MAKEFLAGS=\"-j2\" "
        f"-v {base_dir}/data/{id}/patches:/patches "
        f"n132/arvo:{id}-fix /bin/sh -c \"\n"
        # limit num processes to 2 by changing nproc behavior
        "  echo '#!/bin/sh' > /tmp/nproc\n"
        "  echo 'echo 2' >> /tmp/nproc\n"
        "  chmod +x /tmp/nproc\n"
        "  export PATH=/tmp:\\$PATH\n"
        # locate the project repository in the workshop image
        f"  GIT_DIR=\\$(find /src -type d -iname '{project_name}' | head -n 1)\n"
        # move patched file
        f"  cp -f /patches/{patch_file_name} \\$GIT_DIR/{changed_file}\n"
        # run unittests
        "  " + (unittest_commands[project_name.lower()]
                if project_name in unittest_commands else "  echo 'NO UNIT TESTS'") + "\n"
        "  \""
    )

    with open(testcase_file, 'w') as f:
        f.write(testcase_content)

    with open(unittest_file, 'w') as f:
        f.write(unittest_content)

    patch_file = patch_dir / patch_file_name
    with open(patch_file, 'w') as f:
        f.write(mod_file_content)

    return True




class ParseException(Exception):
    pass


def remove_ansi(text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)


def parse_testcase(output):
    local_id, patch, test_type, proc = output
    stderr = proc.stderr.decode(errors='ignore')
    stdout = proc.stdout.decode(errors='ignore')
    
    if proc.returncode == 0:
        return "pass"
    
    elif "abort on unknown address" in stderr:
        return "pass (false alarm)"
    
    elif re.search(r"(==\d+==\s?[A-Z]*|runtime error):([\s\S]*?)(Exiting|ABORTING|$)", stderr):
        return "crash"

    # compiler error
    elif (
        re.search(r"make(\[\d+\])?:\s\*\*\*\s\[.*\]\sError\s\d+", stderr) or
        re.search(r"clang-\d+:\serror:.*", stderr) or
        re.search(r"ninja: build stopped: subcommand failed.", stdout)
    ):
        raise ParseException(f"compile error ({proc.returncode})")

    # cases that sometimes mean error
    elif (
        re.search(r"NOTE: fuzzing was not performed", stderr) or
        re.search(r"Usage for fuzzing: honggfuzz", stderr) or
        re.search(r"This binary is built for AFL-fuzz\.", stderr) or
        re.search(r"Execution successful\.", stdout) or
        re.search(r"make.*: Leaving directory .*$", stdout)
    ):
        raise ParseException(
            f"No sanitizer-reported error detected with non-zero return code ({proc.returncode})")

    # can be false alarm
    else:
        raise ParseException(f"no matching regex case ({proc.returncode})")


def parse_unittest_libxml2(stdout, result):
    # libxml2 is weird, doesn't contain a status for passing tests.
    # Failure is indicated by a list of failing tests after a "## {NAME}" line.
    # Technically, the "## {NAME}" is the name of a group of unit tests
    # but we treat NAME as a single unit test since it doesn't list the
    # component unit tests that pass.
    # The failure line after "## {NAME}" is something like:
    # ./test/valid/781333.xml:4: element a: validity error
    # A passing test should just list the next "## {NAME}" line or state the
    # total, like "Total 9 tests, no errors"
    re_all = r'^## (?P<name>.*)$'
    re_failing = r'^## (?P<name>.*)\n.*error : '  # fail

    all_tests = set()
    all_matches = re.finditer(re_all, stdout, re.MULTILINE)
    for match in all_matches:
        all_tests.add(match.group("name"))

    failing_tests = set()
    failing_matches = re.finditer(re_failing, stdout, re.MULTILINE)
    for match in failing_matches:
        failing_tests.add(match.group("name"))

    passing_tests = all_tests - failing_tests

    result["pass"] = list(passing_tests)
    result["fail"] = list(failing_tests)
    result["total"] = len(all_tests)


def parse_unittest_htslib(stdout, result):
    result["total"] = 0
    pattern = unittest_patterns['htslib']
    for match in re.finditer(pattern, stdout):
        name = match.group("name")
        num_unexpected_failures = match.group("num_unexpected_failures")
        if num_unexpected_failures == '0':
            result["pass"].append(name)
        else:
            result["fail"].append(name)
        result["total"] += 1
    return result


def parse_unittest(output, project_name):
    project_name = project_name.lower()

    local_id, patch, test_type, proc = output
    stderr = proc.stderr.decode(errors='ignore')
    stdout = proc.stdout.decode(errors='ignore')

    # remove ansi escape
    stderr = remove_ansi(stderr)
    stdout = remove_ansi(stdout)

    result = {
        "pass":  [],  # list of str
        "fail":  [],  # list of strs or int
        "skip":  [],  # list of strs or int
        "total": None  # int
    }

    # libxml2 stdout is weird, handle as special case
    if project_name == 'libxml2':
        parse_unittest_libxml2(stdout, result)
        return result

    # htslib is also weird, handle as special case
    if project_name == 'htslib':
        parse_unittest_htslib(stdout, result)
        return result

    if not project_name in unittest_patterns:
        raise ParseException(f"no pattern for {project_name}")

    patterns = unittest_patterns[project_name]
    if not isinstance(patterns, list):
        patterns = [patterns]

    for pattern in patterns:
        for test in re.finditer(pattern, stdout):
            for g in ["name", "total"]:
                if g in list(test.re.groupindex.keys()) and test.group(g) != None:
                    if g == "total":
                        if result["total"] == None:
                            result["total"] = 0
                        if test.group("total").isdigit():
                            result["total"] += int(test.group("total"))
                        else:
                            result["total"] += 1
                    elif g == "name":
                        # if there is a status, use that
                        if "status" in list(test.re.groupindex.keys()) and test.group("status") != None:
                            s = test.group("status").lower().strip()
                            s = "pass" if s in [
                                "ok", "okay", "success", ".", "", "done", "passed"] else s
                            s = "fail" if s in [
                                "error", "e", "f", "fail", "not ok", "failed", "failure"] else s
                            s = "skip" if s in ["?", "skipped"] else s
                        else:  # otherwise, the default status is pass
                            s = "pass"
                        for status in ["pass", "fail", "skip"]:
                            if status in s:
                                if result[status] == None:
                                    result[status] = []
                                if test.group("name") not in result[status]:
                                    result[status].append(test.group("name"))

    if result["total"] == None:
        result["total"] = sum([len(result[s]) if isinstance(
            result[s], list) else result[s] for s in ["pass", "fail", "skip"]])
    return result
