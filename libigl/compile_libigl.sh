#!/bin/sh
cp main.cpp libigl/tutorial/609_Boolean/main.cpp
cd libigl
mkdir -p build
cd build
cmake ..
cd tutorial
make tutorial/CMakeFiles/609_Boolean.dir/rule -j2
cp -r ./bin/609_Boolean ./../../.
cd ../..
