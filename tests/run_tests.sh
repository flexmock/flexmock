#!/bin/bash

PYTHON_IMPLEMENTATIONS=${PYTHON_IMPLEMENTATIONS:-"python pypy"}
python_VERSIONS=${PYTHON_VERSIONS:-"3.6 3.7 3.8 3.9 3.10"}
pypy_VERSIONS=${PYPY_VERSIONS:-"nover 3"}

if [ -z "$PYEXECS" ]; then
  for impl in $PYTHON_IMPLEMENTATIONS; do
    IMPL_VERSIONS_VAR=${impl}_VERSIONS
    for ver in ${!IMPL_VERSIONS_VAR}; do
      if [ "$ver" == "nover" ]; then
        PYEXECS="$PYEXECS $impl"
      else
        PYEXECS="$PYEXECS $impl$ver"
      fi
    done
  done
fi

RUNNERS=${RUNNERS:-"unittest pytest"}
SCRIPT=$(cd ${0%/*} && echo $PWD/${0##*/})
TEST_PATH=$(dirname $SCRIPT)
FLEXMOCK_PATH=$(echo $TEST_PATH | sed -e s/tests$//)
export PYTHONPATH=$FLEXMOCK_PATH:$TEST_PATH:$PYTHONPATH

EXIT_CODE=0

for pyexec in $PYEXECS; do
  if [[ "$RUNNERS" =~ unittest ]]; then
    echo unittest for $pyexec
    if test -f "`which $pyexec 2>/dev/null`"; then
      $pyexec $TEST_PATH/flexmock_unittest_test.py
      [[ $? -ne 0 ]] && EXIT_CODE=1
    else
      echo $pyexec NOT FOUND
    fi
  fi

  if [[ "$RUNNERS" =~ pytest ]]; then
    if $pyexec -c 'import pytest' 2>/dev/null; then
      echo pytest for $pyexec
      if [[ "$1" == "--pytest-cov" ]]; then
        $pyexec -m pytest $TEST_PATH/flexmock_pytest_test.py --cov flexmock
      else
        $pyexec -m pytest $TEST_PATH/flexmock_pytest_test.py
      fi
      [[ $? -ne 0 ]] && EXIT_CODE=1
    else
      echo pytest for $pyexec NOT FOUND
    fi
  fi

done

exit $EXIT_CODE
