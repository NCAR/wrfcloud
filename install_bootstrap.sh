#!/bin/bash

# Build artifacts and install the wrfcloud software
# Precondition: Runs in AWS CloudShell in us-east-2
# Post-condition: WRF Cloud will be installed in the environment and build artifacts will be available
function main()
{
  ### Check for optional branch name ###
  if [ $# -gt 0 ]; then
    export GIT_CLONE_OPTS="--branch ${1}"
  else
    export GIT_CLONE_OPTS=""
  fi

  ### Setup Build Directory
  time=$(date +%Y%m%d_%H%M%S)
  export build_dir="/tmp/wrfcloud-build-${time}"
  mkdir -p "${build_dir}" && cd "${build_dir}"
  git clone ${GIT_CLONE_OPTS} https://github.com/NCAR/wrfcloud

  ### Configure CloudShell Environment
  install_os_packages
  install_python39
  install_nodejs16

  ### Create WRF Cloud Build Artifacts
  create_wrfcloud_lambda_layer
  create_wrfcloud_lambda_function

  ### Compile angular web application
  install_angular14
  create_wrfcloud_web_application

  ### Install wrfcloud Python package
  install_wrfcloud

  ### Run WRF Cloud Setup Tool
  cd "${build_dir}"
  wrfcloud-setup
}

# Install OS packages with yum
# Precondition: None
# Post-condition: Required os-level packages are installed
function install_os_packages()
{
  sudo yum -y install gcc gcc-c++ bzip2-devel zlib-devel openssl-devel make libffi-devel git sudo wget tar zip
}

# Install python 3.9
# Precondition: C/C++ compilers installed
# Post-condition: Python 3.9 interpreter available in the path as "python3"
function install_python39()
{
  cd "${build_dir}"
  wget https://www.python.org/ftp/python/3.9.13/Python-3.9.13.tgz
  tar -xzf Python-3.9.13.tgz
  cd Python-3.9.13
  ./configure --prefix=/opt/python --enable-optimizations --with-openssl=/usr --enable-loadable-sqlite-extensions
  make -j 4 2>&1 | tee python_build.log
  sudo make install 2>&1 | tee python_install.log
  export PYTHON39="/opt/python"
  export PATH="${PYTHON39}/bin:${PATH}"
  pip3 install wheel
}

# Install node 16
# Precondition: None
# Post-condition: Node 16 interpreter available in the path as "node"
function install_nodejs16()
{
  touch "${HOME}/.bashrc"
  wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.2/install.sh | bash
  source ~/.bashrc
  nvm install 16
  source ~/.bashrc
  export node_version=$(${NVM_BIN}/node --version)
}

# Install Angular 14 command line interface
# Precondition: Node and npm are installed
# Post-condition: Angular CLI is available in the path as "ng"
function install_angular14()
{
  npm install -g @angular/cli@14
  chmod +x ${HOME}/.nvm/versions/node/${node_version}/lib/node_modules/@angular/cli/bin/ng.js
  echo -n 'ewogICIkc2NoZW1hIjogIi4vbm9kZV9tb2R1bGVzL0Bhbmd1bGFyL2NsaS9saWIvY29uZmlnL3NjaGVtYS5qc29uIiwKICAidmVyc2lvbiI6IDEsCiAgImNsaSI6IHsKICAgICJjb21wbGV0aW9uIjogewogICAgICAicHJvbXB0ZWQiOiB0cnVlCiAgICB9CiAgfSwKICAicHJvamVjdHMiOiB7fQp9' | base64 -d > .angular-config.json
  echo -n 'CiMgTG9hZCBBbmd1bGFyIENMSSBhdXRvY29tcGxldGlvbi4Kc291cmNlIDwobmcgY29tcGxldGlvbiBzY3JpcHQpCg==' | base64 -d >> ~/.bashrc
  source ~/.bashrc
}

# Create a zip file for the lambda layer
# Precondition: Git clone of wrfcloud and python 3.9 is installed
# Post-condition: Zip file created to upload as lambda layer code
function create_wrfcloud_lambda_layer()
{
  cd "${build_dir}/wrfcloud/python/src"
  mkdir -p install/python/lib
  pip3 install -t install/python/lib .
  cd install/python/lib
  rm -Rf pygrib pygrib.libs matplotlib numpy numpy.libs pyproj netCDF4 netCDF4.libs Pillow.libs fontTools kiwisolver setuptools cftime PIL contourpy botocore pyproj.libs mpl_toolkits wrfcloud
  cd ../../
  ln -s ~/.nvm/versions/node/${node_version} $(pwd)/node
  rm -f ~/.nvm/versions/node/${node_version}/${node_version}
  zip -r "${build_dir}/lambda_layer.zip" python/lib node/bin node/include node/share node/lib/node_modules/corepack node/lib/node_modules/npm
}

# Create a zip file for the lambda function
# Precondition: Git clone of wrfcloud and python 3.9 is installed
# Post-condition: Zip file created to upload as lambda function code
function create_wrfcloud_lambda_function()
{
  cd "${build_dir}/wrfcloud/python/src"
  zip -r "${build_dir}/lambda_function.zip" lambda_wrapper.py wrfcloud
}

# Build the static web content with Angular CLI
# Precondition: Git clone of wrfcloud and Angular CLI is installed
# Post-condition: Directory created with front-end web content
function create_wrfcloud_web_application()
{
  cd "${build_dir}/wrfcloud/web"
  npm install
  ng build
  mv dist/web "${build_dir}"/
}

# Install wrfcloud Python package
# Precondition: Git clone of wrfcloud
# Post-condition: The wrfcloud package will be installed in the CloudShell environment
function install_wrfcloud()
{
  cd "${build_dir}/wrfcloud/python/src"
  sudo /opt/python/bin/python3 -m pip install .
}

main $@
