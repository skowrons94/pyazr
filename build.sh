mkdir $PREFIX/build && cd $PREFIX/build 
cmake ../AZURE2/ -DBUILD_GUI=ON && make -j4

cp src/AZURE2 "{{ PREFIX }}/lib"

$PYTHON setup.py install