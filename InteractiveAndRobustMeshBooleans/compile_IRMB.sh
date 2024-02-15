#!/bin/sh
cd InteractiveAndRobustMeshBooleans
mkdir -p build
cd build
cmake ..
make -j all
mv mesh_booleans ../..
cd ../..
