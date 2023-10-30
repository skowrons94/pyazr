import os
import time
import curses

import numpy as np

from .brick import brick
from .api import api
from .mcmc import mcmc
from .minuit import minuit
from .thread import thread
from .calc import calc

from scipy import stats
from functools import partial
from multiprocessing.pool import ThreadPool as ThreadPool

def thread_minuit( iter, data, fixed, limits, labels, nuisances, screen, scale, radius ):
    port = 20000 + iter[0]
    min = minuit( iter[1], data, fixed, limits, labels, port, nuisances, screen, scale, radius )
    return min.run( )

def thread_sample( iter, screen ):
    port = 20000 + iter[0]
    sample = calc( iter[1], port, screen )
    return sample.run( )

class config:

    params, fixed, fixed_index, fixed_params = [], [], [], []
    
    data, calc = {}, {}

    priors, limits, norms = [], [], []

    def __init__( self, labels, port = 20000 ):
        self.PORT, self.labels = port, labels
        self.initialize( )

    def initialize( self ):
        if not os.path.exists("config"): os.makedirs("config")
        if not os.path.exists("config/data"): os.makedirs("config/data")
        if not os.path.exists("config/calc"): os.makedirs("config/calc")
        self.update_azure2( )
        self.update_data( )
        self.update_calculated( )
        self.update_priors( )
        self.update_minuit( )
        self.update_nuisances( )
        self.update_fixed_index( )

    def update_fixed_index( self ):
        self.fixed_index = np.where(self.fixed == 1)[0]
        self.fixed_params = self.params[self.fixed_index]

    def get_distribution( self, l ):
        if( l[3] == "uniform" ):
            init, end  = float( l[4] ), float( l[5] )
            return stats.uniform( init, end - init )
        if( l[3] == "norm" ):
            mean, sigma  = float( l[4] ), float( l[5] )
            return stats.norm( mean, sigma )
        if( l[3] == "gauss" ):
            mean, sigma  = float( l[4] ), float( l[5] )
            return stats.norm( mean, sigma )
        if( l[3] == "lognorm" ):
            mean, sigma  = float( l[4] ), float( l[5] )
            return stats.lognorm( mean, sigma )

    def create_priors( self ):
        with open( "config/mcmc_priors.dat", "w" ) as f:
            f.write( "# Index\tLabel\tValue\tDistribution\tParams\tParams\tFixed\n" )
            for idx, par in enumerate( self.params ):
                if( not self.fixed[idx] ):
                    f.write( "{}\t{}\t{:.4E}\t{}\t{:.4E}\t{:.4E}\t{}\n".format( idx, self.labels[idx], par, "uniform", -1e10, 1e10, "False" ) )
                else:
                    f.write( "{}\t{}\t{:.4E}\t{}\t{:.4E}\t{:.4E}\t{}\n".format( idx, self.labels[idx], par, "uniform", -1e10, 1e10, "True" ) )

    def update_priors( self ):
        if( not os.path.isfile("config/mcmc_priors.dat") ): self.create_priors( )
        with open( "config/mcmc_priors.dat", "r" ) as f:
            Lines = f.readlines( )
            for line in Lines:
                l = line.split( )
                if( l[0] == "#" ): continue
                if( l[6] == "False" ):
                    distr = self.get_distribution( l )
                    self.priors.append( distr )

    def create_minuit( self ):
        with open( "config/minuit_params.dat", "w" ) as f:
            f.write( "# Index\tLabel\tValue\tMin\tMax\tFixed\n")
            for idx, par in enumerate( self.params ):
                if( not self.fixed[idx] ):
                    f.write( "{}\t{}\t{:.4E}\t{}\t{}\t{}\n".format( idx, self.labels[idx], par, "-inf", "inf", "False" ) )
                else:
                    f.write( "{}\t{}\t{:.4E}\t{}\t{}\t{}\n".format( idx, self.labels[idx], par, "-inf", "inf", "True" ) )

    def update_minuit( self ):
        if( not os.path.isfile("config/minuit_params.dat") ): self.create_minuit( )
        with open( "config/minuit_params.dat", "r" ) as f:
            Lines, idx = f.readlines( ), 0
            for line in Lines:
                l = line.split( )
                if( l[0] == "#" ): continue
                self.params[idx] = float( l[2] )
                self.limits.append( (float(l[3]),float(l[4])) )
                if( l[5] == "True" ): self.fixed[idx] = 1
                else: self.fixed[idx] = 0
                idx += 1

    def create_nuisances( self ):
        with open( "config/minuit_nuisance.dat", "w" ) as f:
            f.write( "# Index\tLabel\tValue\tError\n" )
            for idx, par in enumerate( self.norms ):
                f.write( "{}\t{}\t{}\t{}\n".format( len(self.params) - len(self.norms) + idx, self.labels[idx], par, self.norms_errors[idx] ) )

    def update_nuisances( self ):
        if( not os.path.isfile("config/minuit_nuisance.dat") ): self.create_nuisances( )
        with open( "config/minuit_nuisance.dat", "r" ) as f:
            self.nuisances = {}
            Lines = f.readlines( )
            for line in Lines:
                l = line.split( )
                if( l[0] == "#" ): continue
                self.nuisances[int(l[0])] = ( float(l[2]), float(l[3]) )

    def update_calculated( self, dir = "config/calc/segment" ):
        dir += "_{}.txt"
        nsegments = api().update_segments( self.params, self.PORT )
        for idx in range( nsegments ):
            self.calc[idx] = np.asarray( api().get_calculated_segment( self.PORT, idx ) )
            np.savetxt(dir.format(idx), np.transpose([self.data[idx][:,0],self.calc[idx]]), fmt='%1.4e %1.4e')

    def update_data( self ):
        nsegments = api().update_data( self.PORT )
        for idx in range( nsegments ):
            x  = np.asarray( api().get_data_energies( self.PORT, idx ) )
            y  = np.asarray( api().get_data_segments( self.PORT, idx ) )
            dy = np.asarray( api().get_data_segments_errors( self.PORT, idx ) )
            self.data[idx] = np.stack((x,y,dy), axis = 1)
            np.savetxt("config/data/segment_{}.txt".format(idx), np.transpose([x,y,dy]), fmt='%1.4e %1.4e %1.4e')       

    def update_azure2( self ):
        self.params       = np.asarray( api().get_params( self.PORT ) )
        self.fixed        = np.asarray( api().get_params_fixed( self.PORT ) )
        self.norms        = np.asarray( api().get_norms( self.PORT ) )
        self.norms_errors = np.asarray( api().get_norms_errors( self.PORT ) ) / 100
        self.params       = np.concatenate( (self.params, self.norms) )
        with open( "config/azure2_params.txt", "w" ) as f:
            f.write( "# Label\tValue\tFixed\n" )
            for idx in range( len( self.labels ) ):
                f.write( "{}\t{:.4E}\t{}\n".format( self.labels[idx], self.params[idx], self.fixed[idx] ) )



class minimizer:

    PORT = 20000

    threads = [ ]

    def __init__( self, file, nprocs = 1 ):
        self.nprocs, self.file, self.azr = nprocs, file, brick( file )
        self.labels = self.azr.config.labels
        self.spawn_threads( nprocs )
        self.config = config( np.array( self.labels ) )
        self.params = self.config.params
        self.data = self.config.data

    def __del__( self ):
        for thread in self.threads: thread.stop( )

    def spawn_threads( self, nprocs ):
        for i in range( nprocs ): self.threads.append( thread( self.PORT + i, self.file ) )
        time.sleep( 2 )
        for i in range( nprocs ):
            api().set_data_mode( self.PORT + i )
            api().initialize( self.PORT + i )
    
    def minuit( self, scale = True, screen = False, radius = 0 ):

        if( screen ):
            screen = curses.initscr()
            for idx in range( self.nprocs ):
                screen.addstr(idx, 0, "Process: {} ---- {:3.2f} it/s Chi2: {:15.4f}".format( idx, 0, 0 ))
            screen.refresh()

        params = [ [0,self.params.copy()] ]
        mask = np.array( [ 0.0001 if "E" in self.labels[idx] else 0.01 for idx in range( len( self.params ) ) ] )
        for idx in range( 1, self.nprocs ):
            params.append( [idx, stats.norm( self.init, abs( mask * self.init ) ).rvs( )] )

        self.best = { }
        with ThreadPool( processes = self.nprocs ) as pool:
            func = partial( thread_minuit, data=self.data, fixed=self.config.fixed, limits=self.config.limits, nuisances=self.config.nuisances, labels=self.labels, screen=screen, scale=scale, radius=radius )
            results = pool.map( func, params )
            pool.close( )
            pool.join( )
            for idx, output in enumerate( results ):
                self.best[idx] = output 

        if( screen ): curses.endwin( )

        for idx, par in self.best.items( ):
            if( not radius ):
                np.savetxt( "minuit/params/params_{}.txt".format(idx), np.transpose([par[0],par[1]]), fmt='%1.5e')
                np.savetxt( "minuit/covariance/cov_{}.txt".format(idx), par[2], fmt='%1.5e')
            else:
                np.savetxt( "minuit/params/params_{}_{}.txt".format(idx,radius[1]), np.transpose(par[0]), fmt='%1.5e')
                np.savetxt( "minuit/covariance/cov_{}_{}.txt".format(idx,radius[1]), par[2], fmt='%1.5e')
            self.config.params = par[0]
            self.config.update_calculated( dir = "minuit/calc/segment_{}".format(idx) )

    def mcmc( self ):
        min = mcmc( self.nprocs, self.config.params, self.config.fixed_params, self.config.fixed_index, self.data, self.config.priors, self.labels )
        min.start( )

    def sample( self, params ):

        #screen = curses.initscr()
        #for idx in range( self.nprocs ):
        #    screen.addstr(idx, 0, "Extrapolating: {} ---- {:3.2f} it/s".format( idx, 0 ))
        #screen.refresh()
        screen = 0

        chunks, bucket = np.split( params, self.nprocs ), [ ]
        for idx, arr in enumerate(chunks): bucket.append( [idx, arr] )

        with ThreadPool( processes = self.nprocs ) as pool:
            func = partial( thread_sample, screen=screen )
            results = pool.map( func, bucket )
            pool.close( )
            pool.join( )
            #extrap.clear()
            #params = [ p.get( ) for p in results ]
        
        #curses.endwin( )
