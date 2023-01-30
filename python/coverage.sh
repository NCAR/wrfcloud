#! /bin/bash

# get the correct readlink executable
readlink=greadlink
if [[ $(uname -s) == "Linux" ]]; then
  readlink=readlink
fi

# get the root directory of the git repo
root_dir=$(${readlink} -f "$(dirname ${0})/..")

# run test with coverage tracking
cd "${root_dir}/python/test" || exit 1
export PYTHONPATH="../src"
if [[ -e htmlcov ]]; then
    rm -Rf htmlcov
fi
coverage run "$(which py.test)" .
coverage xml --include=../src/wrfcloud/\*.py

coverage html --include=../src/wrfcloud/\*.py

# open results in a browser window if we're on macOS or Linux
if [[ "$(uname -s)" == "Darwin" ]]; then
  open htmlcov/index.html
elif [[ "$(uname -s)" == "Linux" ]]; then
  google-chrome htmlcov/index.html
fi
