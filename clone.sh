 #!/bin/sh

cd cgal && [ ! -d "cgal" ] && git clone git@github.com:CGAL/cgal.git ||
    echo 'cgal already here: skipping...'
cd ../libigl && [ ! -d "libigl" ] && git clone git@github.com:libigl/libigl.git ||
    echo 'libigl already here: skipping...'
cd ../cork && [ ! -d "cork" ] && git clone git@github.com:gilbo/cork.git ||
    echo 'cork already here: skipping...'
cd ../InteractiveAndRobustMeshBooleans && [ ! -d "InteractiveAndRobustMeshBooleans" ] && git clone git@github.com:gcherchi/InteractiveAndRobustMeshBooleans.git ||
    echo 'InteractiveAndRobustMeshBooleans already here: skipping...'
cd ../mcut && [ ! -d "mcut" ] && git clone git@github.com:cutdigital/mcut.git ||
    echo 'mcut already here: skipping...'
cd ..
