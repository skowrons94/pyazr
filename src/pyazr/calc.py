import os
import time
import h5py

import numpy as np

from .api import api

class calc:

    def __init__( self, params, port, screen ):
        
        self.params, self.PORT, self.screen = params, port, screen

        api( ).set_extrap_mode( self.PORT )
        api( ).initialize( self.PORT )
    
        self.create( )

    def create( self ):
        if not os.path.exists("extrap"): os.makedirs("extrap")
        nsegments = api( ).update_segments( self.params[0], self.PORT )
        dtype = h5py.special_dtype(vlen=np.dtype('float64'))
        f = h5py.File( "extrap/sample_{}.hdf5".format(self.PORT - 20000), "w" )
        f.create_dataset('Parameters', (0,), compression="gzip", compression_opts=9, dtype=dtype, maxshape=(None,))
        for idx in range( nsegments ):
            f.create_dataset('Segment_{}'.format(idx), (0,), compression="gzip", compression_opts=9, dtype=dtype, maxshape=(None,))
            f.create_dataset('Energies_{}'.format(idx), (0,), compression="gzip", compression_opts=9, dtype=dtype, maxshape=(None,))
        f.close( )
    
    def save( self, par, calc, energies ):
        with h5py.File("extrap/sample_{}.hdf5".format(self.PORT - 20000), "a") as f:
                f["Parameters"].resize((f["Parameters"].shape[0] + 1), axis = 0)
                f['Parameters'][-1] = par
                for key, segment in calc.items( ): 
                    f["Segment_{}".format(key)].resize((f["Segment_{}".format(key)].shape[0] + 1), axis = 0)
                    f["Segment_{}".format(key)][-1] = segment
                    f["Energies_{}".format(key)].resize((f["Energies_{}".format(key)].shape[0] + 1), axis = 0)
                    f["Energies_{}".format(key)][-1] = segment

    def calculate( self, params ):
        energies, calc, nsegments = {}, {}, api( ).update_segments( params, self.PORT )
        for idx in range( nsegments ):
            calc[idx] = np.asarray( api( ).get_calculated_segment( self.PORT, idx ) )
            energies[idx] = np.asarray( api( ).get_calculated_energies( self.PORT, idx ) )
        self.iter += 1
        return calc, energies, nsegments
    
    def run( self ):
        self.start_time, self.iter, bucket = time.time( ), 0, []
        for par in self.params:
            self.iter += 1
            calc, energies, nsegments = self.calculate( par )
            if( nsegments == 0 ): continue
            self.save( par, calc, energies )
            dt = time.time( ) - self.start_time
            #screen.addstr( self.PORT - 20000, 0, "Extrapolating: {} ---- {:3.2f} it/s".format( self.PORT - 20000, self.iter/dt) )
            #screen.refresh()
        #screen.addstr( self.PORT - 20000, 0, "Extrapolating: {:3.2f} it/s {}".format( self.iter/dt, "Completed!" ) )
        #screen.refresh()