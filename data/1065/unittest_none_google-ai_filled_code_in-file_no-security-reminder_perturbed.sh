#!/bin/bash
docker run --rm --init --name 1065_none_google-ai_in-file_no-security-reminder_perturbed_unittest --cpus=2 -e MAKEFLAGS="-j2" -v /workspaces/secure-vibe-coding-workshop/data/1065/patches:/patches n132/arvo:1065-fix /bin/sh -c "
  echo '#!/bin/sh' > /tmp/nproc
  echo 'echo 2' >> /tmp/nproc
  chmod +x /tmp/nproc
  export PATH=/tmp:\$PATH
  GIT_DIR=\$(find /src -type d -iname 'file' | head -n 1)
  cp -f /patches/patch_none_google-ai_filled_code_in-file_no-security-reminder_perturbed.txt \$GIT_DIR/src/funcs.c
  autoreconf -i && ./configure && make && make check
  "