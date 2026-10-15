#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(git rev-parse --show-toplevel)"

# Prevent two lifecycle hooks running setup simultaneously.
exec 9>/tmp/secure-vibe-workshop-setup.lock
flock -w 600 9

retry() {
    local max="$1"
    shift

    local attempt=1
    local delay=2

    until "$@"; do
        local rc=$?

        if [ "$attempt" -ge "$max" ]; then
            echo "✗ Failed after $attempt attempts: $*" >&2
            return "$rc"
        fi

        echo "Retrying ($attempt/$max): $*"
        sleep "$delay"

        attempt=$((attempt + 1))
        delay=$((delay * 2))
    done
}

echo "Preparing workshop environment..."

mkdir -p \
    completions/1065 \
    completions/910 \
    completions/9847 \
    data/1065/patches \
    data/910/patches \
    data/9847/patches

touch \
    completions/1065/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt \
    completions/910/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt \
    completions/9847/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt

export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."

    installer="$(mktemp)"

    retry 5 curl \
        -fsSL \
        --connect-timeout 15 \
        --max-time 120 \
        -o "$installer" \
        https://astral.sh/uv/install.sh

    env UV_UNMANAGED_INSTALL="$HOME/.local/bin" \
        sh "$installer"

    rm -f "$installer"
fi

echo "Preparing Python environment..."

retry 4 uv sync \
    --locked \
    --link-mode=copy

SPEC_KIT_VERSION="1.2.0"
export UV_TOOL_BIN_DIR="$HOME/.local/bin"

echo "Preparing Spec Kit ${SPEC_KIT_VERSION}..."

retry 4 uv tool install \
    "specify-cli==${SPEC_KIT_VERSION}"

command -v specify >/dev/null 2>&1 || {
    echo "✗ Spec Kit was installed but 'specify' is not on PATH." >&2
    exit 1
}

specify version

# Do not initialize Spec Kit here.
# Initialize once as maintainer and commit its project files.
# Participants inherit the same Copilot skills and templates.

echo "Checking Docker..."

retry 5 docker info >/dev/null

images=(
    "n132/arvo:1065-fix"
    "n132/arvo:910-fix"
    "n132/arvo:9847-fix"
)

for image in "${images[@]}"; do
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "✓ $image"
        continue
    fi

    echo "Pulling $image..."
    retry 4 docker pull "$image"

    docker image inspect "$image" >/dev/null
    echo "✓ $image"
done

echo
echo "✓ Workshop environment prepared (Spec Kit ${SPEC_KIT_VERSION})"
