import os
import time

import numpy as np

from .api import api

from iminuit import Minuit

class minuit:

    def __init__( self, params, data, fixed, limits, labels, port, nuisances, screen, scale, radius ):
        
        self.data, self.params, self.labels, self.PORT, self.nuisances, self.is_scale, self.radius = data, params, labels, port, nuisances, scale, radius

        self.m = Minuit( self.chi2, self.params )

        self.m.errordef = self.m.LEAST_SQUARES
        self.m.fixed = fixed
        self.m.limits = limits

        self.ndata = 0
        for key in self.data.keys( ): self.ndata += len( self.data[key] )

        self.nparams = 0
        for idx in range( len(fixed) ): 
            if not fixed[idx]: self.nparams += 1

        self.nfree = self.ndata - self.nparams

        self.scale = 1
        
        if not os.path.exists("minuit"): os.makedirs("minuit")
        if not os.path.exists("minuit/calc"): os.makedirs("minuit/calc")
        if not os.path.exists("minuit/params"): os.makedirs("minuit/params")
        if not os.path.exists("minuit/covariance"): os.makedirs("minuit/covariance")

        self.screen = screen

        if( radius != 0 ): api( ).set_channel_radius( self.PORT, self.radius[0], self.radius[1] )
        api( ).set_data_mode( self.PORT )

    def calculate( self, params ):
        calc, nsegments = {}, api( ).update_segments( params, self.PORT )
        for idx in range( nsegments ):
            calc[idx] = np.asarray( api( ).get_calculated_segment( self.PORT, idx ) )
        return calc, nsegments

    def chi2( self, params ):
        norms = params[len(params)-len(self.data):len(params)]
        model, nsegments = self.calculate( params[:len(params)-len(self.data)] )
        if nsegments == 0:
            return np.inf
        residue = 0
        for key in model.keys( ):
            residue += sum( pow( (model[key] - self.data[key][:,1]*norms[key])/(norms[key]*self.data[key][:,2]), 2 ) )
        if( np.isnan( residue ) ): return np.inf
        for idx in self.nuisances.keys( ):
            if( self.nuisances[idx][1] == 0 ): continue
            residue += pow( (self.nuisances[idx][0] - params[idx])/self.nuisances[idx][1], 2 )
        self.iter += 1
        dt = time.time( ) - self.start_time
        if( screen ):
            self.screen.addstr( "Process: {} ---- {:3.2f} it/s Chi2: {:15.4f}".format( self.PORT - 20000, self.iter/dt, residue) )
            self.screen.refresh()
        else:
            print( "Process: {} ---- {:3.2f} it/s Chi2: {:15.4f}".format( self.PORT - 20000, self.iter/dt, residue) )
        return residue / self.scale
    
    def run( self ):
        self.start_time, self.iter = time.time( ), 0
        self.m.migrad( )
        
        if( self.is_scale ):
            self.scale = self.m.fval / self.nfree
            self.m.migrad( )
        
        if( screen ):
            self.screen.addstr( "Process: {} ---- Iter: {} it Chi2: {:15.4f} Done!".format( self.PORT - 20000, self.iter, self.m.fval) )
            self.screen.refresh()
        else:
            print( "Process: {} ---- Iter: {} it Chi2: {:15.4f} Done!".format( self.PORT - 20000, self.iter, self.m.fval) )

        self.params_errors = self.params.copy( )
        for idx in range( len( self.params ) ):
            self.params[idx] = self.m.values[idx]
            self.params_errors[idx] = self.m.errors[idx]

        table = self.m.covariance.to_table( )[0]
        self.covariance = np.empty( shape=(len(table),len(table)) )
        for idx in range( len( table ) ):
            self.covariance[idx] = np.asarray( table[idx][1:] )

        return self.params, self.params_errors, self.covariance
