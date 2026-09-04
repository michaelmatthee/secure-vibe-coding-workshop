#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(git rev-parse --show-toplevel)"

echo
echo "════════════════════════════════════════"
echo " Preparing Secure Vibe Coding Workshop"
echo "════════════════════════════════════════"
echo

echo "Setting workshop file permissions..."

mkdir -p \
  completions/1065 \
  completions/910 \
  completions/9847

touch \
  completions/1065/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt \
  completions/910/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt \
  completions/9847/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt

chmod 755 \
  function-test \
  function-debug \
  security-test \
  security-debug \
  .devcontainer/setup-workshop.sh

chmod 644 \
  workshop_test_function.py \
  workshop_test_security.py \
  workshop_baseline.json \
  .devcontainer/devcontainer.json \
  completions/1065/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt \
  completions/910/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt \
  completions/9847/google-ai-filled-code-in-file-no-security-reminder-perturbed_code_completion.txt

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh \
      | env UV_UNMANAGED_INSTALL="$HOME/.local/bin" sh
fi

export PATH="$HOME/.local/bin:$PATH"

echo "[1/2] Preparing Python environment..."
uv sync --link-mode=copy

echo
echo "[2/2] Preparing workshop Docker images..."

images=(
  "n132/arvo:1065-fix"
  "n132/arvo:910-fix"
  "n132/arvo:9847-fix"
)

for image in "${images[@]}"; do
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "✓ $image already available"
    else
        echo "Pulling $image..."
        docker pull "$image"
    fi
done

echo
echo "════════════════════════════════════════"
echo " Workshop environment ready"
echo "════════════════════════════════════════"
