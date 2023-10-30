import os
import emcee

import numpy as np

from .api import api

from scipy import stats
from multiprocessing import Pool, current_process

class mcmc:

    def __init__( self, nprocs, params, fixed_params, fixed_index, data, priors, labels, nsteps = 1000, nthin = 10 ):

        self.params, self.fixed_params, self.fixed_index, self.labels = params, fixed_params, fixed_index, labels
        self.data, self.priors = data, priors
        self.nsteps, self.nthin = nsteps, nthin
        self.nprocs = nprocs

        self.nd = len(self.params) - len(self.fixed_params)
        self.nw = 4*self.nd

        if not os.path.exists("mcmc"): os.makedirs("mcmc")
        if not os.path.exists("mcmc/calc"): os.makedirs("mcmc/calc")
        if not os.path.exists("mcmc/params"): os.makedirs("mcmc/params")

        self.backend = emcee.backends.HDFBackend("mcmc/mcmc.h5")
        self.backend.reset(self.nw, self.nd)

    def prepare( self ):
        for idx in range( nprocs ):
            api( ).set_data_mode( 20000 + idx )

        self.p0 = np.zeros((self.nw, self.nd))
        params = np.delete( self.params, self.fixed_index )
        for i in range(self.nw):
            for k in range( len( params ) ):
                if( "E" in self.labels[k] ): self.p0[i][k] = stats.norm( params[k], abs( 0.001*params[k] ) ).rvs()
                else: self.p0[i][k] = stats.norm( params[k], abs( 0.05*params[k] ) ).rvs()

    def calculate( self, params ):
        port = 20000 + current_process()._identity[0] - 1
        calc, nsegments = {}, api().update_segments( params, port )
        if nsegments == 0:
            return calc, nsegments
        for idx in range( nsegments ):
            calc[idx] = np.asarray( api( ).get_calculated_segment( port, idx ) )
        return calc, nsegments

    def lnPi( self, params ):
        return np.sum([pi.logpdf(t) for (pi, t) in zip(self.priors, params)])

    def lnL( self, params ):
        norms = params[len(params)-len(self.data):len(params)]
        model, nsegments = self.calculate( params[:len(params)-len(self.data)] )
        if nsegments == 0:
            return -np.inf
        lnl = 0
        for key in model.keys( ):
            lnl += np.sum(-0.5*np.log(2*np.pi*pow(self.data[key][:,2],2)) - 0.5*pow((model[key] - self.data[key][:,1]*norms[key])/(norms[key]*self.data[key][:,2]),2))
        return lnl

    def lnP( self, params ):
        lnpi = self.lnPi( params )
        if not np.isfinite( lnpi ):
            return -np.inf
        for idx in range( len( self.fixed_params ) ):
            params = np.insert( params, self.fixed_index[idx], self.fixed_params[idx] )
        lnl = self.lnL(params)
        if not np.isfinite( lnl ):
            return -np.inf
        return self.lnL(params) + lnpi
    
    def start( self ):

        self.prepare( )
        
        with Pool( processes = self.nprocs ) as pool:
            sampler = emcee.EnsembleSampler(self.nw, self.nd, self.lnP, pool=pool, backend=self.backend )
            sampler.run_mcmc(self.p0, self.nsteps, thin_by=self.nthin, progress=True, tune=True)