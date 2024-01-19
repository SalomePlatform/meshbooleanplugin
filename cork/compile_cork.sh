#!/bin/sh
cd cork
make -j all
mv bin/cork ../cork_bin
cd ..
