#!/bin/bash
docker run --rm --init --name 1065_none_google-ai_in-file_no-security-reminder_perturbed_testcase --cpus=2 -e MAKEFLAGS="-j2" -v /workspaces/secure-vibe-coding-workshop/data/1065/patches:/patches n132/arvo:1065-fix /bin/sh -c "
  echo '#!/bin/sh' > /tmp/nproc
  echo 'echo 2' >> /tmp/nproc
  chmod +x /tmp/nproc
  export PATH=/tmp:\$PATH
  GIT_DIR=\$(find /src -type d -iname 'file' | head -n 1)
  cp -f /patches/patch_none_google-ai_filled_code_in-file_no-security-reminder_perturbed.txt \$GIT_DIR/src/funcs.c
  ATTEMPTS=0
  MAX_ATTEMPTS=3
  SUCCESS=false
  while [ \$ATTEMPTS -lt \$MAX_ATTEMPTS ]; do
    ATTEMPTS=\$((ATTEMPTS+1))
    echo \"Attempt #\$ATTEMPTS: Running arvo compile...\"
    arvo compile
    EXIT_CODE=\$?
    if [ \$EXIT_CODE -eq 0 ]; then
      echo \"arvo compile succeeded on attempt #\$ATTEMPTS\"
      SUCCESS=true
      break
    else
      echo \"arvo compile failed (exit code: \$EXIT_CODE), retrying...\"
      sleep 2
    fi
  done
  if [ \"\$SUCCESS\" = false ]; then
    echo \"arvo compile failed after \$MAX_ATTEMPTS attempts. Exiting.\"
    exit 1
  fi
  arvo run
  "