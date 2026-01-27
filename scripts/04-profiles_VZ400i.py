import os
import numpy as np
import csv
import pandas as pd
import glob

import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.ticker import MaxNLocator

from pylidar_tls_canopy import riegl_io, plant_profile, grid

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import argparse

def get_folders(directory):
    folders_unsorted = [
        name for name in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, name)) and name.startswith("ScanPos")
    ]
    folders_sorted = sorted(folders_unsorted, key=lambda x: int(x.split("ScanPos")[-1]))
    return folders_sorted

def profile_vz400i(input_dir, input_file, output_dir = None, overwrite = False):
    """function to calculate vertical profiles from RIEGL VZ400i data"""
    # input_dir = "/path/to/your/bis-folder/"
    # input_file = "/path/to/your/input-location.csv"
    # output_dir = "/path/to/your/output-folder/"
    # overwrite = False  # Overwrite existing output files

    # Read locations file
    locations = pd.read_csv(input_file)
    if output_dir is None:
        output_dir = input_dir

    for i in range(0, len(locations)):
        print(f"Processing location {i+1} of {len(locations)}: {locations.loc[i,'upright_scanposition']} / {locations.loc[i,'tilted_scanposition']}")
        # Define input files
        if locations.loc[i,'skip'] == "all":    
            print(f"Skipping location {i} as per 'skip = all' flag in locations file.")
        else:
            upright_rxp_fn = glob.glob(os.path.join(input_dir,locations.loc[i,'upright_scanposition'],"*.rxp"))[0]
            upright_rdbx_fn = glob.glob(os.path.join(input_dir,locations.loc[i,'upright_scanposition'],"*.rdbx"))[0]
            upright_transform_fn = glob.glob(os.path.join(input_dir,locations.loc[i,'upright_scanposition'],"*.DAT"))[0]
            if locations.loc[i,'skip'] == "tilted":
                print(f"Skipping tilted scanposition as per 'skip = tilted' flag in locations file. Calculating profile from upright scan only...")
                csv_file_path = output_dir + locations.loc[i,'upright_scanposition'] + '_NA.csv'
            else:  
                tilt_rxp_fn = glob.glob(os.path.join(input_dir,locations.loc[i,'tilted_scanposition'],"*.rxp"))[0]
                tilt_rdbx_fn = glob.glob(os.path.join(input_dir,locations.loc[i,'tilted_scanposition'],"*.rdbx"))[0]
                tilt_transform_fn = glob.glob(os.path.join(input_dir,locations.loc[i,'tilted_scanposition'],"*.DAT"))[0]
                # Define output files   
                csv_file_path = output_dir + locations.loc[i,'upright_scanposition'] + '_' + locations.loc[i,'tilted_scanposition'] + '.csv'
            if not os.path.exists(csv_file_path) or overwrite == True:
                # Determine the origin coordinates to use
                transform_matrix = riegl_io.read_transform_file(upright_transform_fn)
                x0,y0,z0,_ = transform_matrix[3,:]
                grid_extent = 60
                grid_resolution = 10
                grid_origin = [x0,y0]
                # If using RXP files only as input, set rxp to True:
                x,y,z,r = plant_profile.get_min_z_grid([upright_rdbx_fn,tilt_rdbx_fn], 
                                        [upright_transform_fn,tilt_transform_fn], 
                                        grid_extent, grid_resolution, grid_origin=grid_origin,
                                        rxp=False)
                # Optional weighting of points by 1 / range
                planefit = plant_profile.plane_fit_hubers(x, y, z, w=1/r)
                planefit['Summary']
                # If the ground plane is not defined then set ground_plane to None
                # and use the sensor_height argument whe adding scan positions
                vpp = plant_profile.Jupp2009(hres=0.5, zres=5, ares=360, 
                                            min_z=5, max_z=70, min_h=0, max_h=100,
                                            ground_plane=planefit['Parameters'])
                # If using RXP files only as input, set rdbx_file to None (the default)
                query_str = ['reflectance > -20','range > 1.5']
                vpp.add_riegl_scan_position(upright_rxp_fn, upright_transform_fn, sensor_height=None,
                    rdbx_file=upright_rdbx_fn, method='WEIGHTED', min_zenith=35, max_zenith=70,
                    query_str=query_str)
                # If using RXP files only as input, set rdbx_file to None (the default)
                if locations.loc[i,'skip'] == "tilted":
                    pass
                else:
                    query_str = ['reflectance > -20','range > 1.5']
                    vpp.add_riegl_scan_position(tilt_rxp_fn, tilt_transform_fn, sensor_height=None,
                        rdbx_file=tilt_rdbx_fn, method='WEIGHTED', min_zenith=5, max_zenith=35,
                        query_str=query_str)
                    vpp.get_pgap_theta_z()

                hinge_idx = np.argmin(abs(vpp.azimuth_bin - 57.5))
                pgap_phi_z = []
                for az in range(0, 360, vpp.ares):
                    # Set invert to True if min_azimuth and max_azimuth specify the range to exclude
                    vpp.get_pgap_theta_z(min_azimuth=az, max_azimuth=az+vpp.ares, invert=False)
                    pgap_phi_z.append(vpp.pgap_theta_z[hinge_idx])

                vpp.get_pgap_theta_z(min_azimuth=0, max_azimuth=360)
                hinge_pai = vpp.calcHingePlantProfiles()
                weighted_pai = vpp.calcSolidAnglePlantProfiles()
                linear_pai = vpp.calcLinearPlantProfiles()
                hinge_pavd = vpp.get_pavd(hinge_pai)
                linear_pavd = vpp.get_pavd(linear_pai)
                weighted_pavd = vpp.get_pavd(weighted_pai)
                linear_pai,linear_mla = vpp.calcLinearPlantProfiles(calc_mla=True)
                # Transpose arrays into columns and add "height" column
                rows = zip(vpp.height_bin, *vpp.pgap_theta_z, hinge_pai, weighted_pai, linear_pai, hinge_pavd, weighted_pavd, linear_pavd)
                # Write to CSV file
                with open(csv_file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    # Write header (adding "height" as the first column)
                    writer.writerow(["# height"] + [f'vz{int(b*100):05d}' for b in vpp.zenith_bin] + ['hingePAI', 'weightedPAI', 'linearPAI', 'hingePAVD', 'weightedPAVD', 'linearPAVD'])
                    # Write rows
                    writer.writerows(rows)

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="My pylidar script")
    parser.add_argument("input_dir", type=str, help="Path to input directory file")
    parser.add_argument("input_file", type=str, help="Path to input locations CSV file")
    parser.add_argument("--output_dir", type=str, help="path to directory where to save results")
    parser.add_argument("--overwrite", action='store_true', help="Overwrite existing output files")
    args = parser.parse_args()

    # You can put the rest of your code here or call other functions
    profile_vz400i(args.input_dir, args.input_file, args.output_dir, args.overwrite)

if __name__ == "__main__":
    main()