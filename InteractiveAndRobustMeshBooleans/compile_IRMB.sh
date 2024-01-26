#!/bin/sh
cd InteractiveAndRobustMeshBooleans
mkdir -p build
cd build
cmake ..
make -j4
mv mesh_booleans ../..
cd ../..
