#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import os
import re
import sys
import traceback

from pathlib import Path

from tools.evaler import (
    ParseException,
    parse_testcase,
    setup,
)

from workshop_test_function import (
    AGENT,
    MODEL,
    CONTEXT,
    PROMPT,
    MODE,
    MAX_LOG_BYTES,
    ROOT,
    RESULTS,
    PlatformError,
    SubmissionError,
    require,
    selected_id,
    validated_metadata,
    validate_completion,
    validate_mask,
    docker_preflight,
    cleanup_container,
    run_script,
    looks_like_docker_error,
    acquire_lock,
    extract_participant_completion,
)


# ---------------------------------------------------------------------------
# Security-test configuration
# ---------------------------------------------------------------------------

# Exercise 1065 has shown an intermittent
# harness SIGSEGV (139) without a sanitizer
# diagnostic.
#
# We retry that specific indeterminate result.
TRANSIENT_RETRY_IDS = {
    "1065",
}

# Initial attempt + 2 retries.
MAX_TRANSIENT_RETRIES = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def security_container_name(
    exercise_id: str,
) -> str:

    return (
        f"{exercise_id}_"
        f"{AGENT}_"
        f"{MODEL}_"
        f"{CONTEXT}_"
        f"{PROMPT}_"
        f"{MODE}_"
        "testcase"
    )


def build_proc_view(
    stdout: bytes,
    stderr: bytes,
    returncode: int,
):

    return type(
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


# ---------------------------------------------------------------------------
# Security test
# ---------------------------------------------------------------------------

def run_security_test() -> int:

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

    docker_preflight(
        exercise_id
    )

    print()
    print(
        "════════════════════════════════════════"
    )
    print(
        " Security Test — "
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
            "Could not prepare security "
            f"test: {exc}"
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
            f"testcase_{AGENT}_"
            f"{MODEL}_filled_code_"
            f"{CONTEXT}_{PROMPT}_"
            f"{MODE}.sh"
        )
    )

    require(
        script.is_file()
        and not script.is_symlink(),
        "Generated security-test "
        "script is missing or invalid.",
    )

    stdout_log = (
        RESULTS
        / (
            f"security-{exercise_id}"
            ".stdout.txt"
        )
    )

    stderr_log = (
        RESULTS
        / (
            f"security-{exercise_id}"
            ".stderr.txt"
        )
    )

    name = (
        security_container_name(
            exercise_id
        )
    )

    cleanup_container(
        name
    )

    print(
        "Running security tests..."
    )

    if (
        exercise_id
        in TRANSIENT_RETRY_IDS
    ):

        max_attempts = (
            MAX_TRANSIENT_RETRIES
            + 1
        )

    else:

        max_attempts = 1

    for attempt in range(
        1,
        max_attempts + 1,
    ):

        cleanup_container(
            name
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

        # ---------------------------------------------------------------
        # Platform/resource checks
        # ---------------------------------------------------------------

        if timed_out:

            raise PlatformError(
                "Security test exceeded "
                "the allowed time. "
                "No trustworthy PASS/FAIL "
                "result was produced."
            )

        require(
            stdout_log.is_file()
            and stderr_log.is_file(),
            "Security-test logs "
            "were not created.",
        )

        if (
            stdout_log.stat().st_size
            >= MAX_LOG_BYTES
            or
            stderr_log.stat().st_size
            >= MAX_LOG_BYTES
        ):

            raise PlatformError(
                "Security test produced "
                "too much output. "
                "No trustworthy PASS/FAIL "
                "result was produced."
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
                "Could not read "
                "security-test logs: "
                f"{exc}"
            ) from exc

        if looks_like_docker_error(
            stderr
        ):

            raise PlatformError(
                "Docker failed while "
                "running the security test."
            )

        proc_view = build_proc_view(
            stdout,
            stderr,
            returncode,
        )

        # ---------------------------------------------------------------
        # SecRepoBench classification
        # ---------------------------------------------------------------

        try:

            result = parse_testcase(
                (
                    exercise_id,
                    "sec",
                    "testcase",
                    proc_view,
                )
            )

        except ParseException as exc:

            message = str(
                exc
            )

            combined_output = (
                stdout
                + b"\n"
                + stderr
            ).decode(
                "utf-8",
                errors="replace",
            ).lower()

            # -----------------------------------------------------------
            # Known 1065 instrumented-build crash
            # -----------------------------------------------------------
            #
            # SecRepoBench may classify a make failure as a
            # compile error even when the underlying failure
            # is the magic.mgc build process segfaulting.
            #
            # The generated SecRepoBench script has already
            # retried arvo compile internally, so do not add
            # another outer retry for this condition.

            is_known_build_crash = (
                exercise_id
                in TRANSIENT_RETRY_IDS
                and re.search(
                    (
                        r"(?m)^make(?:\\[\\d+\\])?:"
                        r"\\s+\\*\\*\\*\\s+"
                        r"\\[magic\\.mgc\\]"
                        r"\\s+segmentation fault"
                        r"(?:\\s+\\(core dumped\\))?"
                        r"\\s*$"
                    ),
                    combined_output,
                )
                is not None
            )

            if is_known_build_crash:

                raise PlatformError(
                    "Security test harness crashed "
                    "during the instrumented build."
                ) from exc

            # -----------------------------------------------------------
            # Known transient 1065 runtime harness crash
            # -----------------------------------------------------------
            #
            # This is different from the build crash above.
            # A raw 139 without a sanitizer diagnosis may be
            # transient, so retry it in a bounded manner.

            is_known_transient = (
                exercise_id
                in TRANSIENT_RETRY_IDS
                and returncode == 139
            )

            if (
                is_known_transient
                and attempt < max_attempts
            ):

                print()
                print(
                    "Transient test-harness "
                    "crash detected."
                )

                print(
                    "Retrying security test "
                    f"({attempt}/"
                    f"{MAX_TRANSIENT_RETRIES})..."
                )

                continue

            if is_known_transient:

                raise PlatformError(
                    "Security test harness "
                    "crashed repeatedly without "
                    "producing a sanitizer "
                    "diagnostic."
                ) from exc

            # -----------------------------------------------------------
            # Genuine compilation failure
            # -----------------------------------------------------------

            if (
                "compile error"
                in message.lower()
            ):

                print()
                print(
                    "❌ FAIL - submitted "
                    "code does not compile"
                )

                print()
                print(
                    "Run ./function-test first, "
                    "then ./function-debug "
                    "for details."
                )

                return 1

            raise PlatformError(
                "Could not interpret "
                "security-test output: "
                f"{message}"
            ) from exc

        except Exception as exc:

            raise PlatformError(
                "Unexpected security-test "
                f"parser error: {exc}"
            ) from exc

        # ---------------------------------------------------------------
        # Recognized security result
        # ---------------------------------------------------------------

        print()

        if result in {
            "pass",
            "pass (false alarm)",
        }:

            print(
                "✅ PASS - security test passes"
            )

            return 0

        if result == "crash":

            print(
                "❌ FAIL - security test "
                "detected a vulnerability"
            )

            print()
            print(
                "Run ./security-debug "
                "for details."
            )

            return 1

        raise PlatformError(
            "Unexpected security-test "
            f"result: {result!r}"
        )

    raise PlatformError(
        "Security test ended without "
        "producing a result."
    )


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

        return run_security_test()

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
            "security test stopped."
        )

        return 130

    except Exception:

        log = (
            RESULTS
            / (
                "security-"
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