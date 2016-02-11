# -*- coding: utf-8 -*-
"""
Created on Wed Feb 10 15:12:44 2016

@author: rstreet
"""


################################################################################
#     	      	      	MICROLENSING EVENT SIMULATION
# 
# Program to test the implementation of Finite Source, Point Lens events
################################################################################

###########################
# IMPORT MODULES
from os import path
from sys import argv, exit
import mulens_class
import numpy as np
from astropy import constants
from astropy import coordinates
from astropy.time import Time, TimeDelta
import matplotlib.pyplot as plt
import copy

def simulate_grid_models( params ):
    """Function to drive a simulation of a grid of microlensing models
    spanning user-defined ranges in u0, tE, phi, Vbase, rho).
    
    For each grid point, the simulation generates two lightcurves: 
    one FSPL including annual parallax
    one FSPL including annual + satellite parallax
    with datapoints which reflect the photometric precision likely from 
    a 1m telescope on Earth and the Swift satellite.
    """
    
    grid = construct_grid( params )

    for grid_point in grid:                    
        event = mulens_class.MicrolensingEvent()
        event.u_o = grid_point[0]
        event.t_E = TimeDelta((grid_point[1] * 24.0 * 3600.0),format='sec')
        event.phi = ( grid_point[2] * np.pi ) / 180.0
        event.mag_base = grid_point[3]
        event.rho = grid_point[4]
        event.M_L = constants.M_sun * params['lens_mass']
        event.D_L = constants.pc * params['lens_distance']
        event.D_S = constants.pc * params['source_distance']
        event.RA = '17:57:34.0'
        event.Dec = '-29:13:15.0'
        event.t_o = Time('2015-01-04T16:00:00', format='isot', scale='utc')
        event.t_p = Time('2015-01-04T06:37:00', format='isot', scale='utc')
        
        # Compute lens essential parameters
        event.calc_D_lens_source()
        event.calc_einstein_radius()
        event.gen_event_timeline(cadence=params['cadence'])
        event.calc_source_lens_rel_motion()
        
        # For ease of handling later, a copy of the basic event
        # is taken and will be used to compute the same event
        # as seen from Swift:
        swift_event = copy.copy( event )
        
        # Ground-based observer:        
        # Calculate the model lightcurve for an FSPL event including
        # annual parallax:
        event.calc_proj_observer_pos(parallax=True,satellite=False)
        event.calc_pspl_impact_param()
        event.calc_magnification(model='fspl')
        event.simulate_data_points(model='fspl', phot_precision='1m')
        
        # Swift observer:
        swift_event.calc_proj_observer_pos(parallax=True,satellite=True)
        swift_event.calc_pspl_impact_param()
        swift_event.calc_magnification(model='fspl')
        swift_event.simulate_data_points(model='pspl_parallax_satellite', \
                            phot_precision='swift')
        
        # Calculate delta chi2:
        

def construct_grid( params ):
    """Function to return a list of gridpoints.  Each list entry consists
    of a list of grid parameters:
    [u0, tE, phi, Vbas, rho]
    """

    (umin, umax, uincr) = params['u0_range']
    (temin, temax, teincr) = params['te_range']
    (phimin, phimax, phiincr) = params['phi_range']
    (vmin, vmax, vincr) = params['v_range']
    (rhomin, rhomax, rhoincr)= params['rho_range']    
    
    grid = []
    for u0 in np.arange( umin, umax, uincr ):
        for te in np.arange( temin, temax, teincr ):
            for phi in np.arange( phimin, phimax, phiincr ):
                for Vbase in np.arange( vmin, vmax, vincr ):
                    for rho in np.arange( rhomin, rhomax, rhoincr ):
                        grid.append( [u0,te,phi,Vbase,rho] )
    return grid

def parse_input_file( file_path ):
    """Function to parse the input file of simulation parameters into a 
    dictionary of the required format.
    Parameters:
        u0_range  min  max  incr    [units of RE]
        te_range  min  max  incr    [days]
        phi_range min  max  incr    [deg]
        v_range   min  max  incr    [mag]
        rho_range min  max  incr    [units of RE]
        cadence   float             [mins]
        lens_mass float             [Msol]
        lens_distance float         [pc]
        source_distance float       [pc]
   
    """
    
    if path.isfile( file_path ) == False:
        print 'Error: Cannot find input parameter file ' + file_path
        exit()
    
    lines = open( file_path, 'r' ).readlines()
    params = {}
    for line in lines: 
        entries = line.split()
        key = str( entries[0] ).lower()
        if 'range' in key:
            rmin = float( entries[1] )
            rmax = float( entries[2] )
            incr = float( entries[3] )
            value = [ rmin, rmax, incr ]
        else:
            value = float( entries[1] )
        params[ key ] = value
    return params

#############################################
# COMMANDLINE RUN SECTION
if __name__ == '__main__':
    
    if len(argv) == 1:
        print """Call sequence:
                python swift_grid_simulation.py [parameter_file]
              """
    else:
        file_path = argv[1]
        params = parse_input_file( file_path )
        simulate_grid_models( params )