#!/bin/sh
cp main.cpp libigl/tutorial/609_Boolean/main.cpp
cd libigl
mkdir -p build
cd build
cmake ..
make -j all
cp -r ./bin/609_Boolean ./../../.
cd ../..
