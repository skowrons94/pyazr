import os
import time

import numpy as np

from .api import api

from iminuit import Minuit

class minuit:

    def __init__( self, params, data, fixed, limits, labels, port, nuisances, screen, 
                  ignored_segments=[], e1_segments=[], e2_segments=[], ratio_segments=[], sum_segments=[],
                  radius = 0, is_scale = False, is_sivia=False ):
        
        self.data, self.params, self.labels = data, params, labels
        self.PORT, self.nuisances, self.radius = port, nuisances, radius
        self.is_scale, self.is_sivia = is_scale, is_sivia
        self.ignored_segments, self.e1_segments, self.e2_segments = ignored_segments, e1_segments, e2_segments
        self.ratio_segments, self.sum_segments = ratio_segments, sum_segments

        self.m = Minuit( self.func, self.params )

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
    
    def print( self, residue ):
        dt = time.time( ) - self.start_time
        if( self.screen ):
            self.screen.addstr( "Process: {} ---- {:3.2f} it/s Chi2: {:15.4f}".format( self.PORT - 20000, self.iter/dt, residue) )
            self.screen.refresh()
        else:
            print( "Process: {} ---- {:3.2f} it/s Chi2: {:15.4f}".format( self.PORT - 20000, self.iter/dt, residue) )
    
    def calculate( self, params ):
        calc, nsegments = {}, api( ).update_segments( params, self.PORT )
        for idx in range( nsegments ):
            if( idx in self.ignored_segments ): continue
            elif( idx in self.e1_segments ): calc[idx] = np.asarray( api( ).get_calculated_segment_e1( self.PORT, idx ) )
            elif( idx in self.e2_segments ): calc[idx] = np.asarray( api( ).get_calculated_segment_e2( self.PORT, idx ) )
            elif( idx in self.sum_segments ): calc[idx] = np.asarray( api( ).get_calculated_segment( self.PORT, idx ) ) #+ np.asarray( api( ).get_calculated_segment( self.PORT, idx - 1 ) )
            elif( idx in self.ratio_segments ): calc[idx] = np.asarray( api( ).get_calculated_segment( self.PORT, idx ) ) / np.asarray( api( ).get_calculated_segment( self.PORT, idx - 1 ) )
            else: calc[idx] = np.asarray( api( ).get_calculated_segment( self.PORT, idx ) )
        return calc, nsegments

    def sivia( self, model, norms ):
        residue = 0
        for key in self.data.keys( ):
            if( key in self.ignored_segments ): continue
            elif( key in self.ratio_segments ):
                data = self.data[key][:,1]/self.data[key-1][:,1]
                data_err = np.sqrt( pow( self.data[key][:,2]/self.data[key][:,1], 2 ) + pow( self.data[key-1][:,2]/self.data[key-1][:,1], 2 ) )
                chi2 = pow( (model[key] - data*norms[key])/(norms[key]*data_err), 2 )
            else: chi2     = pow( (model[key] - self.data[key][:,1]*norms[key])/(norms[key]*self.data[key][:,2]), 2 )
            residue += sum( -1.0 * np.log( (1.0 - np.exp( -0.5 * chi2 ))  / chi2 ) )
        return residue

    def least_square( self, model, norms ):
        residue = 0
        for key in self.data.keys( ):
            if( key in self.ignored_segments ): continue
            if( key in self.sum_segments ): continue
            elif( key in self.ratio_segments ):
                data = self.data[key][:,1]/self.data[key-1][:,1]
                data_err = np.sqrt( pow( self.data[key][:,2]/self.data[key][:,1], 2 ) + pow( self.data[key-1][:,2]/self.data[key-1][:,1], 2 ) )
                chi2 = pow( (model[key] - data*norms[key])/(norms[key]*data_err), 2 )
            else: chi2 = pow( (model[key] - self.data[key][:,1]*norms[key])/(norms[key]*self.data[key][:,2]), 2 )
            residue = sum( chi2 )
        return residue

    def func( self, params ):
        
        norms = params[len(params)-len(self.data):len(params)]
        model, nsegments = self.calculate( params[:len(params)-len(self.data)] )
        
        if( nsegments == 0 ): return np.inf
        
        if( self.is_sivia ): residue = self.sivia( model, norms )
        else: residue = self.least_square( model, norms )
        
        if( np.isnan( residue ) ): return np.inf
        
        for idx in self.nuisances.keys( ):
            if( self.nuisances[idx][1] == 0 ): continue
            residue += pow( (self.nuisances[idx][0] - params[idx])/self.nuisances[idx][1], 2 )
        
        self.iter += 1
        self.print( residue )
        
        return residue / self.scale
    
    def run( self ):
        
        self.start_time, self.iter = time.time( ), 0
        self.m.migrad( )
        
        if( self.is_scale ):
            self.scale = self.m.fval / self.nfree
            self.m.migrad( )
        
        if( self.screen ):
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
