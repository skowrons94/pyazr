mkdir ./build && cd ./build && 
cmake ./AZURE2/ && make -j4 && cd -

$PYTHON setup.py install