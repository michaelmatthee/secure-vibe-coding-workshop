#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import os
import re
import resource
import shutil
import signal
import subprocess
import sys
import traceback

from pathlib import Path, PurePosixPath

from tools.evaler import (
    ParseException,
    parse_unittest,
    setup,
)

from tools.utils import get_c_cpp_file


# ---------------------------------------------------------------------------
# Workshop configuration
# ---------------------------------------------------------------------------

ALLOWED_IDS = {
    "910",
    "1065",
    "9847",
}

AGENT = "none"
MODEL = "google-ai"
CONTEXT = "in-file"
PROMPT = "no-security-reminder"
MODE = "perturbed"

TIMEOUT_SECONDS = 300

MAX_LOG_BYTES = (
    5
    * 1024
    * 1024
)

MAX_COMPLETION_BYTES = (
    64
    * 1024
)

ROOT = (
    Path(__file__)
    .resolve()
    .parent
)

RESULTS = (
    ROOT
    / "workshop-results"
)


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class PlatformError(RuntimeError):
    """
    The runner cannot produce a trustworthy
    PASS/FAIL result.
    """


class SubmissionError(RuntimeError):
    """
    The participant's submitted completion
    is invalid.
    """


def require(
    condition: bool,
    message: str,
) -> None:

    if not condition:
        raise PlatformError(
            message
        )


def load_json(
    path: Path,
):

    try:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(
                file
            )

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:

        raise PlatformError(
            f"Cannot read {path.name}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Exercise selection
# ---------------------------------------------------------------------------

def selected_id() -> str:

    try:

        lines = [
            line.strip()
            for line in (
                ROOT
                / "assets"
                / "ids.txt"
            )
            .read_text(
                encoding="utf-8"
            )
            .splitlines()
            if line.strip()
        ]

    except (
        OSError,
        UnicodeDecodeError,
    ) as exc:

        raise PlatformError(
            "Cannot read assets/ids.txt: "
            f"{exc}"
        ) from exc

    require(
        bool(lines)
        and lines[0].lower() == "id",
        "assets/ids.txt must begin "
        "with the header 'id'.",
    )

    ids = lines[1:]

    require(
        len(ids) == 1,
        "Exactly one exercise must be "
        f"selected; found {len(ids)}.",
    )

    exercise_id = ids[0]

    require(
        exercise_id
        in ALLOWED_IDS,
        f"Exercise {exercise_id!r} "
        "is not enabled for this workshop.",
    )

    return exercise_id


# ---------------------------------------------------------------------------
# Metadata validation
# ---------------------------------------------------------------------------

def validated_metadata(
    exercise_id: str,
) -> tuple[
    str,
    str,
]:

    metadata = load_json(
        ROOT
        / "workshop_metadata.json"
    )

    require(
        isinstance(
            metadata,
            dict,
        ),
        "workshop_metadata.json is invalid.",
    )

    require(
        isinstance(
            metadata.get(
                exercise_id
            ),
            dict,
        ),
        "Metadata for exercise "
        f"{exercise_id} is missing.",
    )

    entry = (
        metadata[
            exercise_id
        ]
    )

    project = entry.get(
        "project_name"
    )

    changed_file = entry.get(
        "changed_file"
    )

    safe_project = re.compile(
        r"^[A-Za-z0-9_.+-]+$"
    )

    safe_path = re.compile(
        r"^[A-Za-z0-9_./+-]+$"
    )

    require(
        isinstance(
            project,
            str,
        )
        and safe_project.fullmatch(
            project
        )
        is not None,
        "Invalid project_name in "
        "workshop_metadata.json.",
    )

    require(
        isinstance(
            changed_file,
            str,
        )
        and safe_path.fullmatch(
            changed_file
        )
        is not None,
        "Invalid changed_file in "
        "workshop_metadata.json.",
    )

    changed_path = (
        PurePosixPath(
            changed_file
        )
    )

    require(
        not changed_path.is_absolute()
        and ".."
        not in changed_path.parts,
        "changed_file must be a "
        "safe relative path.",
    )

    return (
        project,
        changed_file,
    )


# ---------------------------------------------------------------------------
# Completion validation
# ---------------------------------------------------------------------------

def completion_path(
    exercise_id: str,
) -> Path:

    return (
        ROOT
        / "completions"
        / exercise_id
        / (
            f"{MODEL}-filled-code-"
            f"{CONTEXT}-{PROMPT}-{MODE}_"
            "code_completion.txt"
        )
    )


def validate_completion(
    exercise_id: str,
) -> None:

    completion = (
        completion_path(
            exercise_id
        )
    )

    require(
        completion.is_file()
        and not completion.is_symlink(),
        "Completion file is missing "
        "or invalid: "
        f"{completion.relative_to(ROOT)}",
    )

    try:

        data = (
            completion.read_bytes()
        )

    except OSError as exc:

        raise PlatformError(
            "Could not read completion "
            f"file: {exc}"
        ) from exc

    if (
        len(data)
        > MAX_COMPLETION_BYTES
    ):

        raise SubmissionError(
            "Completion is too large "
            f"({len(data)} bytes; "
            "maximum "
            f"{MAX_COMPLETION_BYTES})."
        )

    if b"\x00" in data:

        raise SubmissionError(
            "Completion contains "
            "invalid NUL bytes."
        )

    try:

        text = data.decode(
            "utf-8"
        )

    except UnicodeDecodeError as exc:

        raise SubmissionError(
            "Completion must contain "
            "valid UTF-8 text."
        ) from exc

    # Treat zero bytes, spaces,
    # tabs and blank lines identically.
    if not text.strip():

        raise SubmissionError(
            "Completion is empty."
        )


# ---------------------------------------------------------------------------
# Mask validation
# ---------------------------------------------------------------------------

def validate_mask(
    exercise_id: str,
) -> None:

    try:

        source = get_c_cpp_file(
            "descriptions/"
            f"{exercise_id}/"
            f"mask_{MODE}"
        )

    except Exception as exc:

        raise PlatformError(
            "Could not read masked "
            f"source: {exc}"
        ) from exc

    require(
        isinstance(
            source,
            str,
        ),
        "Masked source file is missing.",
    )

    count = source.count(
        "// <MASK>"
    )

    require(
        count == 1,
        "Masked source must contain "
        "exactly one // <MASK>; "
        f"found {count}.",
    )


# ---------------------------------------------------------------------------
# Functional baseline
# ---------------------------------------------------------------------------

def required_tests(
    exercise_id: str,
) -> set[str]:

    report = load_json(
        ROOT
        / "workshop_baseline.json"
    )

    try:

        passing = (
            report[
                exercise_id
            ][
                "unittest_sec"
            ][
                "pass"
            ]
        )

    except (
        KeyError,
        TypeError,
    ) as exc:

        raise PlatformError(
            "Functional baseline "
            "is missing."
        ) from exc

    # Prevent:
    #
    # set().issubset(anything) == True
    #
    # from creating an accidental pass.
    require(
        isinstance(
            passing,
            list,
        )
        and len(passing) > 0,
        "Functional baseline contains "
        "no passing tests.",
    )

    require(
        all(
            isinstance(
                name,
                str,
            )
            and bool(name)
            for name in passing
        ),
        "Functional baseline contains "
        "invalid test names.",
    )

    return set(
        passing
    )


# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

def docker_preflight(
    exercise_id: str,
) -> None:

    require(
        shutil.which(
            "docker"
        )
        is not None,
        "Docker is not installed "
        "or is not on PATH.",
    )

    try:

        result = subprocess.run(
            [
                "docker",
                "info",
                "--format",
                "{{.ServerVersion}}",
            ],
            stdout=(
                subprocess.DEVNULL
            ),
            stderr=(
                subprocess.DEVNULL
            ),
            stdin=(
                subprocess.DEVNULL
            ),
            timeout=10,
            check=False,
        )

    except subprocess.TimeoutExpired as exc:

        raise PlatformError(
            "Docker daemon check "
            "timed out."
        ) from exc

    require(
        result.returncode == 0,
        "Docker daemon is unavailable.",
    )

    image = (
        f"n132/arvo:"
        f"{exercise_id}-fix"
    )

    try:

        result = subprocess.run(
            [
                "docker",
                "image",
                "inspect",
                image,
            ],
            stdout=(
                subprocess.DEVNULL
            ),
            stderr=(
                subprocess.DEVNULL
            ),
            stdin=(
                subprocess.DEVNULL
            ),
            timeout=10,
            check=False,
        )

    except subprocess.TimeoutExpired as exc:

        raise PlatformError(
            "Docker image check "
            f"timed out: {image}"
        ) from exc

    require(
        result.returncode == 0,
        "Required Docker image is "
        "not available locally: "
        f"{image}",
    )


def functional_container_name(
    exercise_id: str,
) -> str:

    return (
        f"{exercise_id}_"
        f"{AGENT}_"
        f"{MODEL}_"
        f"{CONTEXT}_"
        f"{PROMPT}_"
        f"{MODE}_"
        "unittest"
    )


def cleanup_container(
    name: str,
) -> None:

    try:

        subprocess.run(
            [
                "docker",
                "rm",
                "-f",
                name,
            ],
            stdout=(
                subprocess.DEVNULL
            ),
            stderr=(
                subprocess.DEVNULL
            ),
            stdin=(
                subprocess.DEVNULL
            ),
            timeout=10,
            check=False,
        )

    except (
        OSError,
        subprocess.TimeoutExpired,
    ):

        pass


# ---------------------------------------------------------------------------
# Process/resource handling
# ---------------------------------------------------------------------------

def child_limits() -> None:

    resource.setrlimit(
        resource.RLIMIT_FSIZE,
        (
            MAX_LOG_BYTES,
            MAX_LOG_BYTES,
        ),
    )


def run_script(
    script: Path,
    stdout_log: Path,
    stderr_log: Path,
) -> tuple[
    int,
    bool,
]:

    with (
        stdout_log.open(
            "wb"
        ) as out,
        stderr_log.open(
            "wb"
        ) as err,
    ):

        proc = subprocess.Popen(
            [
                "/bin/bash",
                str(script),
            ],
            stdout=out,
            stderr=err,
            stdin=(
                subprocess.DEVNULL
            ),
            start_new_session=True,
            preexec_fn=child_limits,
        )

        try:

            proc.wait(
                timeout=(
                    TIMEOUT_SECONDS
                )
            )

            timed_out = False

        except subprocess.TimeoutExpired:

            timed_out = True

            try:

                os.killpg(
                    proc.pid,
                    signal.SIGKILL,
                )

            except ProcessLookupError:

                pass

            try:

                proc.wait(
                    timeout=5
                )

            except subprocess.TimeoutExpired:

                pass

        except BaseException:

            try:

                os.killpg(
                    proc.pid,
                    signal.SIGKILL,
                )

            except ProcessLookupError:

                pass

            raise

    stdout_log.chmod(
        0o600
    )

    stderr_log.chmod(
        0o600
    )

    return (
        (
            proc.returncode
            if proc.returncode
            is not None
            else -1
        ),
        timed_out,
    )


def looks_like_docker_error(
    stderr: bytes,
) -> bool:

    text = stderr.decode(
        "utf-8",
        errors="ignore",
    ).lower()

    indicators = (
        "cannot connect to "
        "the docker daemon",
        "error response from daemon",
        "unable to find image",
        "docker: ",
    )

    return any(
        marker in text
        for marker in indicators
    )


def looks_like_compiler_error(
    stdout: bytes,
    stderr: bytes,
) -> bool:
    """
    Detect a genuine compiler/linker failure without
    treating an ordinary failing unit test as a
    compilation failure.
    """

    text = (
        stdout
        + b"\n"
        + stderr
    ).decode(
        "utf-8",
        errors="ignore",
    )

    patterns = (
        r"(?mi)^.*\.(?:c|cc|cpp|cxx|h|hpp):"
        r"\d+(?::\d+)?:\s*(?:fatal\s+)?error:",
        r"(?mi)^(?:clang(?:-\d+)?|gcc|g\+\+|cc|c\+\+):"
        r"\s*(?:fatal\s+)?error:",
        r"(?mi)undefined reference to",
        r"(?mi)^collect2:\s*error:",
        r"(?mi)^(?:ld|ld\.lld):\s*error:",
        r"(?mi)^ninja:\s*build stopped:\s*subcommand failed\.?$",
    )

    return any(
        re.search(
            pattern,
            text,
        )
        is not None
        for pattern in patterns
    )


# ---------------------------------------------------------------------------
# Shared concurrency protection
# ---------------------------------------------------------------------------

def acquire_lock():

    lock_path = (
        RESULTS
        / "workshop-test.lock"
    )

    fd = os.open(
        lock_path,
        (
            os.O_CREAT
            | os.O_RDWR
        ),
        0o600,
    )

    try:

        fcntl.flock(
            fd,
            (
                fcntl.LOCK_EX
                | fcntl.LOCK_NB
            ),
        )

    except BlockingIOError as exc:

        os.close(
            fd
        )

        raise PlatformError(
            "Another workshop test "
            "is already running."
        ) from exc

    return fd

def extract_participant_completion() -> None:

    extractor = (
        ROOT
        / "workshop_extract_completion.py"
    )

    if (
        extractor.is_symlink()
        or not extractor.is_file()
    ):

        raise PlatformError(
            "Workshop completion extractor "
            "is missing or invalid."
        )

    try:

        result = subprocess.run(
            [
                sys.executable,
                str(extractor),
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )

    except subprocess.TimeoutExpired as exc:

        raise PlatformError(
            "Workshop completion extraction "
            "timed out."
        ) from exc

    except OSError as exc:

        raise PlatformError(
            "Unable to run workshop "
            "completion extractor."
        ) from exc

    if result.returncode == 0:

        return

    message = (
        result.stderr
        or result.stdout
        or ""
    ).strip()

    prefix = "❌ FAIL - "

    if message.startswith(prefix):

        message = message[
            len(prefix):
        ].strip()

    if (
        result.returncode == 2
        and message
    ):

        raise SubmissionError(
            message
        )

    raise PlatformError(
        "Workshop completion extraction "
        "failed unexpectedly."
    )

# ---------------------------------------------------------------------------
# Functional test
# ---------------------------------------------------------------------------

def run_functional_test() -> int:

    safe_root = re.compile(
        r"^[A-Za-z0-9_./+-]+$"
    )

    require(
        safe_root.fullmatch(
            str(ROOT)
        )
        is not None,
        "Repository path contains "
        "unsupported characters.",
    )

    exercise_id = (
        selected_id()
    )

    (
        project,
        changed_file,
    ) = validated_metadata(
        exercise_id
    )

    validate_completion(
        exercise_id
    )

    validate_mask(
        exercise_id
    )

    baseline = required_tests(
        exercise_id
    )

    docker_preflight(
        exercise_id
    )

    print()
    print(
        "════════════════════════════════════════"
    )
    print(
        " Functional Test — "
        f"Exercise {exercise_id}"
    )
    print(
        "════════════════════════════════════════"
    )
    print()
    print(
        "Preparing current completion..."
    )

    try:

        prepared = setup(
            exercise_id,
            AGENT,
            project,
            changed_file,
            MODEL,
            CONTEXT,
            PROMPT,
            MODE,
        )

    except Exception as exc:

        raise PlatformError(
            "Could not prepare test: "
            f"{exc}"
        ) from exc

    require(
        prepared is True,
        "SecRepoBench setup did not "
        "complete successfully.",
    )

    script = (
        ROOT
        / "data"
        / exercise_id
        / (
            f"unittest_{AGENT}_"
            f"{MODEL}_filled_code_"
            f"{CONTEXT}_{PROMPT}_"
            f"{MODE}.sh"
        )
    )

    require(
        script.is_file()
        and not script.is_symlink(),
        "Generated functional-test "
        "script is missing or invalid.",
    )

    stdout_log = (
        RESULTS
        / (
            f"function-{exercise_id}"
            ".stdout.txt"
        )
    )

    stderr_log = (
        RESULTS
        / (
            f"function-{exercise_id}"
            ".stderr.txt"
        )
    )

    name = (
        functional_container_name(
            exercise_id
        )
    )

    cleanup_container(
        name
    )

    print(
        "Running functional tests..."
    )

    try:

        (
            returncode,
            timed_out,
        ) = run_script(
            script,
            stdout_log,
            stderr_log,
        )

    finally:

        cleanup_container(
            name
        )

    if timed_out:

        raise PlatformError(
            "Functional test exceeded "
            f"{TIMEOUT_SECONDS} seconds. "
            "No PASS/FAIL result "
            "was produced."
        )

    if (
        stdout_log.stat().st_size
        >= MAX_LOG_BYTES
        or
        stderr_log.stat().st_size
        >= MAX_LOG_BYTES
    ):

        raise PlatformError(
            "Functional test produced "
            "too much output. "
            "No PASS/FAIL result "
            "was produced."
        )

    try:

        stdout = (
            stdout_log.read_bytes()
        )

        stderr = (
            stderr_log.read_bytes()
        )

    except OSError as exc:

        raise PlatformError(
            "Could not read functional "
            f"test logs: {exc}"
        ) from exc

    if looks_like_docker_error(
        stderr
    ):

        raise PlatformError(
            "Docker failed while running "
            "the functional test."
        )

    # Do not fail solely because the project's overall
    # unit-test command returned non-zero. Parse the
    # individual test results first, then compare them
    # with the required workshop baseline below.

    proc_view = type(
        "Proc",
        (),
        {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": (
                returncode
            ),
        },
    )()

    try:

        parsed = parse_unittest(
            (
                exercise_id,
                "sec",
                "unittest",
                proc_view,
            ),
            project,
        )

    except ParseException as exc:

        raise PlatformError(
            "Could not parse functional "
            f"test output: {exc}"
        ) from exc

    except Exception as exc:

        raise PlatformError(
            "Unexpected functional-test "
            f"parser error: {exc}"
        ) from exc

    require(
        isinstance(
            parsed,
            dict,
        ),
        "Functional-test parser "
        "returned invalid data.",
    )

    passing = parsed.get(
        "pass"
    )

    failing = parsed.get(
        "fail"
    )

    total = parsed.get(
        "total"
    )

    require(
        isinstance(
            passing,
            list,
        )
        and isinstance(
            failing,
            list,
        ),
        "Functional-test parser "
        "returned malformed "
        "pass/fail data.",
    )

    no_recognizable_tests = (
        (
            total is None
            or total == 0
        )
        and not passing
        and not failing
    )

    if no_recognizable_tests:

        if (
            returncode != 0
            and looks_like_compiler_error(
                stdout,
                stderr,
            )
        ):

            print()
            print(
                "❌ FAIL - submitted "
                "code does not compile"
            )

            print()
            print(
                "Run ./function-debug "
                "for details."
            )

            return 1

        raise PlatformError(
            "Functional-test output "
            "contained no recognizable "
            "tests."
        )

    missing = (
        baseline
        - set(passing)
    )

    print()

    if not missing:

        print(
            "✅ PASS - functionality works"
        )

        return 0

    print(
        "❌ FAIL - functionality "
        "does not work"
    )

    print(
        f"   {len(missing)} required "
        "baseline test(s) did not pass."
    )

    print()
    print(
        "Run ./function-debug "
        "for details."
    )

    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:

    os.chdir(
        ROOT
    )

    os.umask(
        0o077
    )

    RESULTS.mkdir(
        mode=0o700,
        parents=True,
        exist_ok=True,
    )

    if RESULTS.is_symlink():

        print()
        print(
            "⚠️ ERROR - workshop-results "
            "must not be a symbolic link."
        )

        return 2

    lock_fd = None

    try:

        lock_fd = acquire_lock()

        extract_participant_completion()

        return run_functional_test()

    except SubmissionError as exc:

        print()
        print(
            f"❌ FAIL - {exc}"
        )

        return 1

    except PlatformError as exc:

        print()
        print(
            f"⚠️ ERROR - {exc}"
        )

        print(
            "   No trustworthy "
            "PASS/FAIL result "
            "was produced."
        )

        return 2

    except KeyboardInterrupt:

        print()
        print(
            "⚠️ INTERRUPTED - "
            "functional test stopped."
        )

        return 130

    except Exception:

        log = (
            RESULTS
            / (
                "function-"
                "internal-error.log"
            )
        )

        try:

            log.write_text(
                traceback.format_exc(),
                encoding="utf-8",
            )

            log.chmod(
                0o600
            )

        except OSError:

            pass

        print()
        print(
            "⚠️ ERROR - unexpected "
            "internal runner failure."
        )

        return 2

    finally:

        if lock_fd is not None:

            try:

                fcntl.flock(
                    lock_fd,
                    fcntl.LOCK_UN,
                )

            except OSError:

                pass

            os.close(
                lock_fd
            )


if __name__ == "__main__":

    sys.exit(
        main()
    )