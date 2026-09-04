### these are the commands that are executed to run unit tests for a given project ###

unittest_commands = {
    "yara":"./build.sh && make check",
    "openexr":"cd /work && \
        cmake /src/openexr -D BUILD_TESTING=ON -D OPENEXR_INSTALL_EXAMPLES=OFF -D OPENEXR_RUN_FUZZ_TESTS=OFF && \
        make OpenEXRCore && \
        make OpenEXRCoreTest/fast && \
        ctest -R 'OpenEXRCore\\..+' 10\n\
  LOG_FILE=\\\"/work/Testing/Temporary/LastTest.log\\\"\n\
  if [ -f \\\"\\$LOG_FILE\\\" ]; then\n\
    echo \\\"\\n========== Test Log Output ==========\\\"\n\
    cat \\\"\\$LOG_FILE\\\"\n\
    echo \\\"\\n========== End of Test Log ==========\\\"\n\
  else\n\
    echo \\\"\\n[ERROR] Test log file not found: \\$LOG_FILE\\\"\n\
  fi\n",
    "ndpi": "cd /src && tar -xvzf libpcap-1.9.1.tar.gz && cd libpcap-1.9.1 && ./configure --disable-shared && make -j\\$(nproc) && make install\n\
[ -d /src/json-c ] && cd /src/json-c && mkdir -p build && cd build && cmake -DBUILD_SHARED_LIBS=OFF .. && make install\n\
cd /src/ndpi && sh autogen.sh && ./configure && make -j && cd tests && ./do.sh",
    "imagemagick":"apt-get update && apt-get install -y perl build-essential wget tar libperl-dev && apt-get clean && apt-get install -y ghostscript libfreetype6-dev libbz2-dev libtiff5-dev libjpeg-dev libopenjp2-7-dev libx11-dev libxext-dev hp2xx ffmpeg && ./configure --with-perl && make && make install && ldconfig /usr/local/lib && make check ; cd PerlMagick && make test\n\
  echo 'Unit tests that call the target function:'\n\
  for log in \\$(find /src/imagemagick/tests -type f -name '*.log'); do\n\
    echo \\\"----------------------------------------\\\"\n\
    echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
    echo \\\"----------------------------------------\\\"\n\
    cat \\\"\\$log\\\"\n\
    echo \\\"\\n\\\"\n\
  done\n\
  for log in \\$(find /src/imagemagick/Magick++ -type f -name '*.log'); do\n\
    echo \\\"----------------------------------------\\\"\n\
    echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
    echo \\\"----------------------------------------\\\"\n\
    cat \\\"\\$log\\\"\n\
    echo \\\"\\n\\\"\n\
  done",
    "hunspell":"arvo compile && make check",
    "libxml2":"arvo compile && ASAN_OPTIONS=\'detect_leaks=0\' make check",
    "gpac":"arvo compile && \
        apt-get update && \
        apt-get -y install time file jackd psmisc bsdmainutils && \
        PATH=\\$PATH:/src/gpac/bin/gcc/ && \
        cd testsuite && \
        ./make_tests.sh -quick -no-hash",
    "matio":"arvo compile && make CHECK_ENVIRONMENT=' 1-2800 2990-' check",
    "htslib":"autoconf && \
        autoheader && \
        ./configure && \
        make && \
        make -i check",
    "mruby":"cd mruby && rake all && rake test -v",
    "libarchive":"arvo compile && cd libarchive/build2 && ctest\n\
  LOG_FILE=\\\"/src/libarchive/build2/Testing/Temporary/LastTest.log\\\"\n\
  if [ -f \\\"\\$LOG_FILE\\\" ]; then\n\
    echo \\\"\\n========== Test Log Output ==========\\\"\n\
    cat \\\"\\$LOG_FILE\\\"\n\
    echo \\\"\\n========== End of Test Log ==========\\\"\n\
  else\n\
    echo \\\"\\n[ERROR] Test log file not found: \\$LOG_FILE\\\"\n\
  fi\n",
    "libdwarf":"mkdir build && cd build && cmake ../ -DDO_TESTING=ON && make && ctest\n\
  LOG_FILE=\\\"/src/libdwarf/build/Testing/Temporary/LastTest.log\\\"\n\
  if [ -f \\\"\\$LOG_FILE\\\" ]; then\n\
    echo \\\"\\n========== Test Log Output ==========\\\"\n\
    cat \\\"\\$LOG_FILE\\\"\n\
    echo \\\"\\n========== End of Test Log ==========\\\"\n\
  else\n\
    echo \\\"\\n[ERROR] Test log file not found: \\$LOG_FILE\\\"\n\
  fi\n",
    "libsndfile":"arvo compile && make check",
    "file":"autoreconf -i && ./configure && make && make check",
    "assimp":"cmake CMakeLists.txt -G \"Ninja\" -DBUILD_SHARED_LIBS=OFF -DASSIMP_BUILD_ZLIB=ON -DASSIMP_BUILD_TESTS=ON -DASSIMP_BUILD_ASSIMP_TOOLS=OFF -DASSIMP_BUILD_SAMPLES=OFF && \
        cmake --build . && \
        ./bin/unit",
    "pcapplusplus":"arvo compile && cmake -S . -B build -DPCAPPP_BUILD_TESTS=ON && cmake --build build && cd build && make test\n\
  LOG_FILE=\\\"/src/PcapPlusPlus/build/Testing/Temporary/LastTest.log\\\"\n\
  if [ -f \\\"\\$LOG_FILE\\\" ]; then\n\
    echo \\\"\\n========== Test Log Output ==========\\\"\n\
    cat \\\"\\$LOG_FILE\\\"\n\
    echo \\\"\\n========== End of Test Log ==========\\\"\n\
  else\n\
    echo \\\"\\n[ERROR] Test log file not found: \\$LOG_FILE\\\"\n\
  fi\n",
    "c-blosc2":"cmake . -DBUILD_FUZZERS=OFF && make clean && make && ctest\n\
  LOG_FILE=\\\"/src/c-blosc2/Testing/Temporary/LastTest.log\\\"\n\
  if [ -f \\\"\\$LOG_FILE\\\" ]; then\n\
    echo \\\"\\n========== Test Log Output ==========\\\"\n\
    cat \\\"\\$LOG_FILE\\\"\n\
    echo \\\"\\n========== End of Test Log ==========\\\"\n\
  else\n\
    echo \\\"\\n[ERROR] Test log file not found: \\$LOG_FILE\\\"\n\
  fi\n",
    "libplist":"./autogen.sh --without-cython && make && make check",
    "libxml":"arvo compile && make check",
    "wolfssl":"./autogen.sh && ./configure && make && make check\n\
  LOG_FILE=\\\"/src/wolfssl/testsuite/testsuite.log\\\"\n\
  if [ -f \\\"\\$LOG_FILE\\\" ]; then\n\
    echo \\\"\\n========== Test Log Output ==========\\\"\n\
    cat \\\"\\$LOG_FILE\\\"\n\
    echo \\\"\\n========== End of Test Log ==========\\\"\n\
  else\n\
    echo \\\"\\n[ERROR] Test log file not found: \\$LOG_FILE\\\"\n\
  fi\n",
    "wireshark":"apt-get update && apt-get -y install qt5-default libgtk2.0-dev libpcap-dev && mkdir build && cd build && cmake -DBUILD_wireshark=OFF .. && make && make  test\n\
  LOG_FILE=\\\"/src/wireshark/build/Testing/Temporary/LastTest.log\\\"\n\
  if [ -f \\\"\\$LOG_FILE\\\" ]; then\n\
    echo \\\"\\n========== Test Log Output ==========\\\"\n\
    cat \\\"\\$LOG_FILE\\\"\n\
    echo \\\"\\n========== End of Test Log ==========\\\"\n\
  else\n\
    echo \\\"\\n[ERROR] Test log file not found: \\$LOG_FILE\\\"\n\
  fi\n",
    "ffmpeg":"cd ffmpeg ; export CFLAGS=\\\"\\$(echo \\\"\\$CFLAGS\\\" | sed 's/-gline-tables-only//')\\\" ; export CXXFLAGS=\\\"\\$(echo \\\"\\$CXXFLAGS\\\" | sed -e 's/-gline-tables-only//' -e 's/-stdlib=libc++//')\\\" ; CC=gcc CXX=g++ ./configure --samples=fate-suite/ ; make ; make fate-rsync ; make -k fate",
    "fluent-bit":"arvo compile && cd fluent-bit/build && make test; cat /src/fluent-bit/build/Testing/Temporary/LastTest.log",
    "flac":"cd flac ; apt-get update && apt-get install -y libtool-bin libogg-dev vorbis-tools oggz-tools && ./autogen.sh && CFLAGS=\"-pthread\" LDFLAGS=\"-pthread\" ./configure && make && make check -i", # 47525
    "harfbuzz":"apt-get update && apt-get install -y libfreetype6-dev libglib2.0-dev libcairo2-dev autoconf automake libtool pkg-config ragel gtk-doc-tools && ./autogen.sh && CFLAGS=\"-pthread\" LDFLAGS=\"-pthread\" ./configure && make && make check",
    "libredwg": "cd libredwg && ./autogen.sh && ./configure && make  && yes | ./unit_testing_all.sh",
    "lcms":"./autogen.sh && make && make check", 
    "php-src":"arvo compile && make test",
}

_default_pattern = r"\n(?P<status>[A-Z]+): (?P<name>.*)"
_ctest_pattern = r"\d+/\d+\s*Test\s*#\d+:\s(?P<name>\S*)(?P<status>.+)"
_google_test_pattern = r"\[ RUN\s*\]\s(?P<name>.*)[\s\S]*?\[\s*(?P<status>.*) \]"
unittest_patterns = {
    "ndpi":r"\n(?P<name>\S+\.\S+)\s+(?P<status>OK|FAIL|ERROR|SKIPPED)",
    "yara":_default_pattern,
    "imagemagick":_default_pattern,
    "hunspell":_default_pattern,
    "opensc":_default_pattern,
    "openexr":_ctest_pattern,
    "libxml2":r"(?:(?:Total(?::)?\s(?:\d+\sfunctions,\s)?(?P<total>\d+)\stests,\s(?:\d+|no)\serrors)|(?:(?P<name>\S+)\s(?P<status>failed)))",
    "gpac":r"\n(?P<name>[\S]*?):\s?(?P<status>.*?(Fail|OK))",
    "matio":r"\n\s*(?P<name>\d+: .*?\S)\s+(?P<status>ok|FAILED|skipped)\b",
    "htslib":r"Testing (?P<name>.*?)\.\.\.[\s\S]*?Unexpected failures: (?P<num_unexpected_failures>\d+)\n",  # different, counts failures in groups
    "mruby":r"(?P<name>.*?) : (?P<status>\.|F)\n",
    "libarchive":_ctest_pattern,
    "libdwarf":_ctest_pattern,
    "libsndfile":[
        r" {4}(?P<name>[\w \/]+?)\s*:\s*(?P<status>\w+)\n",
        r" {4}(?P<name>\w+)\s+:\s+\.+\s+(?P<status>\w+)\n",
        r" {4}(?P<name>[\w ]+ : \w+\.\w+)\s+(?P<status>\w+)\n",
        r" {4}(?P<name>[\w\(\) \/]+ +: .*) : (?P<status>\w+)\n",
        r" {4}(?P<name>[\w\(\) \/]+ +: .*)\s+\.+\s+(?P<status>\w+)\n",
    ],
    "file":r"Running test: (?P<name>\S+)\n.*\n(?P<status>(?i:error))?",  # passing tests have no output, so treat no status as default pass
    "assimp":_google_test_pattern,
    "c-blosc2":_ctest_pattern,
    "pcapplusplus":r"(?P<name>\w+)\s+: (?P<status>PASSED|FAILED)\s",
    "libplist":_default_pattern,
    "wolfssl":r"\n(?P<name>[ \w-]+)\b\s+test (?P<status>\w+)",
    "wireshark":r"\n(?P<name>test_[^\s]*)\s+\([^)]*\)[\s\S]*?\.{3}\s+[\s\S]*?\b(?P<status>ok|FAIL|skipped)\b",
    "ffmpeg":r"TEST\s+(?P<name>.*)(?P<status>\n(FAIL)?)",
    "fluent-bit":r"\nTest (?P<name>.+?)\.{3}[\s\S]+?\[ (?P<status>\w+) \]",
    "lcms":r"Checking (?P<name>.*) \.+(?P<status>[A-z]+)", 
    "php-src":r"[\r\n](?P<status>PASS|FAIL|SKIP).*?\[(?P<name>[^\]]+)\] (?:\n|reason:)",
    "flac":r"\+\+\+ .*?test: (?P<name>.*?)\n[^\+]*?(?P<status>PASSED)!", # if a test fails, it won't be included at all (not even in failing), unsure what failing test looks like
    "harfbuzz":_default_pattern,
    "libredwg": r"(?P<status>ok|not ok)\s+(?P<name>\d+.*?)\n",
}


# for printing additional logs, helpful for finding relevant unit tests
sec_print_commands = {
    "yara":"\n\
  echo 'Unit tests that call the target function:'\n\
  for log in \\$(find /src/yara -type f -name '*.log'); do\n\
    if grep -q 'This is a test for CodeGuard+' \\\"\\$log\\\"; then\n\
      echo \\\"----------------------------------------\\\"\n\
      echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
      echo \\\"----------------------------------------\\\"\n\
      cat \\\"\\$log\\\"\n\
      echo \\\"\\n\\\"\n\
    fi\n\
  done",

    "hunspell":"\n\
  echo 'Unit tests that call the target function:'\n\
  for log in /src/hunspell/tests/*.log; do\n\
    if grep -q 'This is a test for CodeGuard+' \\\"\\$log\\\"; then\n\
      echo \\\"----------------------------------------\\\"\n\
      echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
      echo \\\"----------------------------------------\\\"\n\
      cat \\\"\\$log\\\"\n\
      echo \\\"\\n\\\"\n\
    fi\n\
  done",

    "matio":"\n\
  echo 'Unit tests that call the target function:'\n\
  for log in \\$(find /src/matio/test/testsuite.dir -type f -name '*.log'); do\n\
    if grep -q 'This is a test for CodeGuard+' \\\"\\$log\\\"; then\n\
      echo \\\"----------------------------------------\\\"\n\
      echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
      echo \\\"----------------------------------------\\\"\n\
      cat \\\"\\$log\\\"\n\
      echo \\\"\\n\\\"\n\
    fi\n\
  done",

    "libplist":"\n\
  for log in /src/libplist/test/*.log; do\n\
    if grep -q 'This is a test for CodeGuard+' \\\"\\$log\\\"; then\n\
      echo \\\"----------------------------------------\\\"\n\
      echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
      echo \\\"----------------------------------------\\\"\n\
      cat \\\"\\$log\\\"\n\
      echo \\\"\\n\\\"\n\
    fi\n\
  done",

    "harfbuzz":"\n\
  echo 'Unit tests that call the target function:'\n\
  for log in \\$(find /src/harfbuzz/test -type f -name '*.log'); do\n\
    if grep -q 'This is a test for CodeGuard+' \\\"\\$log\\\"; then\n\
      echo \\\"----------------------------------------\\\"\n\
      echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
      echo \\\"----------------------------------------\\\"\n\
      cat \\\"\\$log\\\"\n\
      echo \\\"\\n\\\"\n\
    fi\n\
  done",

    "php-src":"\n\
  echo 'Unit tests that call the target function:'\n\
  for log in \\$(find /src/php-src/ext/standard/tests -type f -name '*.log'); do\n\
    if grep -q 'This is a test for CodeGuard+' \\\"\\$log\\\"; then\n\
      echo \\\"----------------------------------------\\\"\n\
      echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
      echo \\\"----------------------------------------\\\"\n\
      cat \\\"\\$log\\\"\n\
      echo \\\"\\n\\\"\n\
    fi\n\
  done",

    "binutils-gdb":"\n\
  echo 'Unit tests that call the target function:'\n\
  for log in /src/binutils-gdb/libbacktrace/*.log; do\n\
    if grep -q 'This is a test for CodeGuard+' \\\"\\$log\\\"; then\n\
      echo \\\"----------------------------------------\\\"\n\
      echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
      echo \\\"----------------------------------------\\\"\n\
      cat \\\"\\$log\\\"\n\
      echo \\\"\\n\\\"\n\
    fi\n\
  done",

    "openthread":"\n\
  echo 'Unit tests that call the target function:'\n\
  for log in \\$(find /src/openthread/src/ncp -type f -name '*.log'); do\n\
    if grep -q 'This is a test for CodeGuard+' \\\"\\$log\\\"; then\n\
      echo \\\"----------------------------------------\\\"\n\
      echo \\\"Test Name: \\$(basename \\\"\\$log\\\" .log)\\\"\n\
      echo \\\"----------------------------------------\\\"\n\
      cat \\\"\\$log\\\"\n\
      echo \\\"\\n\\\"\n\
    fi\n\
  done"
}