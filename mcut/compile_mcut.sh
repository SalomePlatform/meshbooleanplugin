#!/bin/sh
cp -r CSGBoolean.cpp mcut/tutorials/CSGBoolean/CSGBoolean.cpp
cd mcut
mkdir -p build
cd build
cmake ..
make -j all
mv bin/CSGBoolean ../..
cd ../..
