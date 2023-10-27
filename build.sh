mkdir $RECIPE_DIR/build && cd $RECIPE_DIR/build 
cmake $RECIPE_DIR/AZURE2/ -DBUILD_GUI=ON && make -j4
cd $RECIPE_DIR

mkdir -p $PREFIX/bin
cp $RECIPE_DIR/build/src/AZURE2 $PREFIX/bin/

python3 $RECIPE_DIR/setup.py install