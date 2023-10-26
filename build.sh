mkdir ./build && cd ./build && 
cmake ../AZURE2/ && make -j4 && cd -

mkdir -p $PREFIX/bin
cp ./build/src/AZURE2 $PREFIX/bin/

$PYTHON setup.py install