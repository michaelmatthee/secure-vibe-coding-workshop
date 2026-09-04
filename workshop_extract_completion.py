#!/usr/bin/env python3

from pathlib import Path
import os
import sys
import tempfile


ROOT = Path(__file__).resolve().parent

ALLOWED_EXERCISES = {"1065", "910", "9847"}

MASK = "// <MASK>"

START_MARKER = "/* ===== YOUR CODE STARTS HERE ===== */"
END_MARKER = "/* ===== YOUR CODE ENDS HERE ===== */"

MAX_COMPLETION_BYTES = 64 * 1024
EXERCISE_SIZE_OVERHEAD = 8 * 1024


def fail(message: str) -> None:
    print(f"❌ FAIL - {message}", file=sys.stderr)
    raise SystemExit(2)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_utf8(path: Path, description: str) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        fail(f"Unable to read {description}.")

    if b"\x00" in data:
        fail(f"{description} contains invalid NUL bytes.")

    try:
        return normalize_newlines(data.decode("utf-8"))
    except UnicodeDecodeError:
        fail(f"{description} must contain valid UTF-8 text.")


def get_selected_exercise() -> str:
    selection_file = ROOT / "assets" / "ids.txt"

    text = read_utf8(selection_file, "exercise selection")
    lines = text.splitlines()

    if len(lines) != 2:
        fail("Exercise selection is invalid. Run ./exercise <id>.")

    if lines[0].strip() != "id":
        fail("Exercise selection is invalid. Run ./exercise <id>.")

    exercise_id = lines[1].strip()

    if exercise_id not in ALLOWED_EXERCISES:
        fail("Exercise selection is invalid. Run ./exercise <id>.")

    return exercise_id


def get_template(exercise_id: str) -> tuple[Path, str]:
    template_file = (
        ROOT
        / "descriptions"
        / exercise_id
        / "mask_perturbed.c"
    )

    if template_file.is_symlink() or not template_file.is_file():
        fail("The workshop exercise template is missing or invalid.")

    template = read_utf8(template_file, "exercise template")

    if template.count(MASK) != 1:
        fail(
            "The workshop exercise template is invalid: "
            "expected exactly one // <MASK>."
        )

    return template_file, template


def get_exercise_file(
    exercise_id: str,
    template_file: Path,
) -> str:
    exercise_file = ROOT / "exercise.c"

    if exercise_file.is_symlink():
        fail(
            "exercise.c must be a regular file. "
            f"Run ./exercise {exercise_id} again."
        )

    if not exercise_file.is_file():
        fail(
            f"exercise.c is missing. "
            f"Run ./exercise {exercise_id} first."
        )

    try:
        exercise_size = exercise_file.stat().st_size
        template_size = template_file.stat().st_size
    except OSError:
        fail("Unable to inspect exercise.c.")

    maximum_size = (
        template_size
        + MAX_COMPLETION_BYTES
        + EXERCISE_SIZE_OVERHEAD
    )

    if exercise_size > maximum_size:
        fail("exercise.c is unexpectedly large.")

    return read_utf8(exercise_file, "exercise.c")


def validate_and_extract(
    exercise_id: str,
    template: str,
    exercise: str,
) -> str:
    expected_header = f"/* WORKSHOP EXERCISE: {exercise_id} */"

    if not exercise.startswith(expected_header + "\n\n"):
        fail(
            f"exercise.c does not match exercise {exercise_id}. "
            f"Run ./exercise {exercise_id} again."
        )

    if exercise.count(START_MARKER) != 1:
        fail(
            "The start marker in exercise.c was changed, "
            "removed, or duplicated."
        )

    if exercise.count(END_MARKER) != 1:
        fail(
            "The end marker in exercise.c was changed, "
            "removed, or duplicated."
        )

    start_position = exercise.index(START_MARKER)
    end_position = exercise.index(END_MARKER)

    if end_position <= start_position:
        fail("The editable region in exercise.c is invalid.")

    template_before, template_after = template.split(MASK)

    expected_before = (
        expected_header
        + "\n\n"
        + template_before
    )

    actual_before = exercise[:start_position]

    actual_after = exercise[
        end_position + len(END_MARKER):
    ]

    if actual_before != expected_before:
        fail(
            "Code outside the editable region was modified. "
            f"Run ./exercise {exercise_id} again to reset it."
        )

    if actual_after != template_after:
        fail(
            "Code outside the editable region was modified. "
            f"Run ./exercise {exercise_id} again to reset it."
        )

    completion = exercise[
        start_position + len(START_MARKER):
        end_position
    ]

    # Remove only blank lines introduced by the exercise markers.
    # Do not otherwise rewrite participant code.
    completion = completion.strip("\n")

    if "\x00" in completion:
        fail("The submitted code contains invalid NUL bytes.")

    completion_size = len(completion.encode("utf-8"))

    if completion_size > MAX_COMPLETION_BYTES:
        fail("The submitted code is too large.")

    return completion


def get_completion_file(exercise_id: str) -> Path:
    completion_file = (
        ROOT
        / "completions"
        / exercise_id
        / (
            "google-ai-filled-code-in-file-"
            "no-security-reminder-perturbed_code_completion.txt"
        )
    )

    if completion_file.is_symlink():
        fail("The workshop completion file is invalid.")

    if not completion_file.is_file():
        fail("The workshop completion file is missing.")

    return completion_file


def atomic_write_completion(
    completion_file: Path,
    completion: str,
) -> None:
    payload = completion

    if payload:
        payload += "\n"

    temporary_path: Path | None = None

    try:
        fd, temporary_name = tempfile.mkstemp(
            prefix=".workshop-completion-",
            suffix=".tmp",
            dir=completion_file.parent,
        )

        temporary_path = Path(temporary_name)

        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        os.chmod(temporary_path, 0o644)

        os.replace(
            temporary_path,
            completion_file,
        )

        temporary_path = None

    except OSError:
        fail("Unable to update the workshop completion file.")

    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def main() -> None:
    exercise_id = get_selected_exercise()

    template_file, template = get_template(exercise_id)

    exercise = get_exercise_file(
        exercise_id,
        template_file,
    )

    completion = validate_and_extract(
        exercise_id,
        template,
        exercise,
    )

    completion_file = get_completion_file(exercise_id)

    atomic_write_completion(
        completion_file,
        completion,
    )


if __name__ == "__main__":
    main()
