#!/bin/sh
cp -r off.cpp cork/src/file_formats/off.cpp
cd cork
make -j4
mv bin/cork ../cork_bin
cd ..
