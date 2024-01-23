#!/bin/sh
cp -r off.cpp cork/src/file_formats/off.cpp
cd cork
make -j all
mv bin/cork ../cork_bin
cd ..
