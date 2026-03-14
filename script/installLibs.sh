#!/bin/bash
# Dependencies for CHIME experiments. Tested on Ubuntu 18.04 (CloudLab r650).
# On Ubuntu 22+: if pip fails with "externally managed environment", run:
#   export PIP_BREAK_SYSTEM=1
# before this script, or add --break-system-packages to pip3 install commands.

if [ ! -d "tmp" ]; then
	mkdir tmp
fi

cd tmp

# apt-get: -y is sufficient for install; --force-yes was deprecated
sudo apt-get -y update
sudo apt-get -y install cmake

# memcached
sudo apt-get -y install memcached libmemcached-dev

# numa
sudo apt-get -y install libnuma-dev

# cityhash
git clone https://github.com/google/cityhash.git
cd cityhash
./configure
make all check CXXFLAGS="-g -O3"
sudo make install
cd ..

# boost (paper uses 1.53; archives.boost.io is more reliable than SourceForge)
(wget -q "https://archives.boost.io/release/1.53.0/source/boost_1_53_0.tar.bz2" -O boost_1_53_0.tar.bz2 && tar -xjf boost_1_53_0.tar.bz2) || \
  (wget -q "https://sourceforge.net/projects/boost/files/boost/1.53.0/boost_1_53_0.zip/download" -O boost_1_53_0.zip && unzip -o boost_1_53_0.zip)
cd boost_1_53_0
./bootstrap.sh
./b2 install --with-system --with-coroutine --layout=versioned threading=multi
sudo apt-get -y install libboost-all-dev || true
cd ..

# paramiko and Python deps
sudo apt-get -y install python3-pip
PIP_OPTS=""
[ -n "$PIP_BREAK_SYSTEM" ] && PIP_OPTS="--break-system-packages"
pip3 install $PIP_OPTS --upgrade pip
pip3 install $PIP_OPTS paramiko gdown func_timeout matplotlib
pip3 install $PIP_OPTS --upgrade --no-cache-dir gdown

# tbb
git clone https://github.com/wjakob/tbb.git
cd tbb/build
cmake ..
make -j
sudo make install
cd ../..

# gflag
git clone https://github.com/gflags/gflags.git
mkdir gflags/build
cd gflags/build
cmake ..
make -j
sudo make install
cd ../..

# gtest
wget https://github.com/google/googletest/archive/refs/tags/release-1.12.1.zip
unzip release-1.12.1.zip
mkdir googletest-release-1.12.1/build
cd googletest-release-1.12.1/build
cmake ..
make -j
sudo make install
cd ../..

sudo ldconfig

# openjdk-8 (YCSB)
sudo apt-get -y install openjdk-8-jdk || sudo apt-get -y install openjdk-11-jdk

cd ..
rm -rf tmp
