from datetime import datetime
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
import riegl_rdb

from tqdm import tqdm

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import argparse

from itertools import repeat
import json

def get_folders(directory):
    folders_unsorted = [
        name for name in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, name)) and name.startswith("ScanPos")
    ]
    folders_sorted = sorted(folders_unsorted, key=lambda x: int(x.split("ScanPos")[-1]))
    return folders_sorted

def profile_vz(input_dir, input_file, output_dir=None, overwrite=False, datetime_now=None):
    locations = pd.read_csv(input_file)
    if output_dir is None:
        output_dir = input_dir

    for i in tqdm(range(len(locations)), desc="Processing locations", unit="location"):
        tqdm.write(
            f"Processing location {i+1} of {len(locations)}: "
            f"{locations.loc[i,'upright_scanposition']} / {locations.loc[i,'tilted_scanposition']}"
        )

        if locations.loc[i, 'skip'] == "all":
            tqdm.write(f"Skipping location {i} as per 'skip = all' flag.")
            continue

        # Inputs
        upright_rxp_fn = glob.glob(os.path.join(input_dir, locations.loc[i,'upright_scanposition'], "*.rxp"))[0]
        upright_rdbx_fn = glob.glob(os.path.join(input_dir, locations.loc[i,'upright_scanposition'], "*.rdbx"))[0]
        upright_transform_fn = glob.glob(os.path.join(input_dir, locations.loc[i,'upright_scanposition'], "*.DAT"))[0]

        use_tilted = (locations.loc[i, 'skip'] != "tilted")
    
        
        if use_tilted:
            tilt_rxp_fn = glob.glob(os.path.join(input_dir, locations.loc[i,'tilted_scanposition'], "*.rxp"))[0]
            tilt_rdbx_fn = glob.glob(os.path.join(input_dir, locations.loc[i,'tilted_scanposition'], "*.rdbx"))[0]
            tilt_transform_fn = glob.glob(os.path.join(input_dir, locations.loc[i,'tilted_scanposition'], "*.DAT"))[0]
            out_name = f"{locations.loc[i,'upright_scanposition']}_{locations.loc[i,'tilted_scanposition']}.txt"
        else:
            tqdm.write("Skipping tilted scanposition (skip=tilted). Calculating profile from upright only.")
            out_name = f"{locations.loc[i,'upright_scanposition']}_NA.txt"

        txt_file_path = os.path.join(output_dir, out_name)

        if os.path.exists(txt_file_path) and not overwrite:
            tqdm.write(f"Output exists, skipping (use --overwrite): {txt_file_path}")
            continue

        # Ground plane
        transform_matrix = riegl_io.read_transform_file(upright_transform_fn)
        x0, y0, z0, _ = transform_matrix[3, :]
        grid_extent = 60
        grid_resolution = 10
        grid_origin = [x0, y0]

        # IMPORTANT: build lists conditionally (prevents crash when skip=tilted)
        rdbx_list = [upright_rdbx_fn]
        tfm_list = [upright_transform_fn]
        if use_tilted:
            rdbx_list.append(tilt_rdbx_fn)
            tfm_list.append(tilt_transform_fn)

        x, y, z, r = plant_profile.get_min_z_grid(
            rdbx_list, tfm_list,
            grid_extent, grid_resolution,
            grid_origin=grid_origin,
            rxp=False
        )

        planefit = plant_profile.plane_fit_hubers(x, y, z, w=1 / r)
        
        param_a = planefit['Parameters'][1]
        param_b = planefit['Parameters'][2]
        param_c = planefit['Parameters'][0]
        plane_slope = planefit['Slope']
        plane_aspect = planefit['Aspect']

        vpp = plant_profile.Jupp2009(
            hres=0.5, zres=5, ares=360,
            min_z=5, max_z=70, min_h=0, max_h=100,
            ground_plane=planefit['Parameters']
        )

        query_str = ['reflectance > -20', 'range > 1.5']
        vpp.add_riegl_scan_position_scanline(
            upright_rxp_fn, upright_transform_fn, sensor_height=None,
            rdbx_file=upright_rdbx_fn, method='WEIGHTED',
            min_zenith=35, max_zenith=70,
            query_str=query_str
        )
        
        dev_min_v = pd.DataFrame(vpp.points)['deviation'].min()
        dev_max_v = pd.DataFrame(vpp.points)['deviation'].max()
        ref_min_v = pd.DataFrame(vpp.points)['reflectance'].min()
        ref_max_v = pd.DataFrame(vpp.points)['reflectance'].max()
        upright_transform = riegl_io.read_transform_file(upright_transform_fn)
        utransform_one_line = " ".join(" ".join(f"{v:.6f}" for v in upright_transform[row]) for row in range(4))


        if use_tilted:
            vpp.add_riegl_scan_position_scanline(
                tilt_rxp_fn, tilt_transform_fn, sensor_height=None,
                rdbx_file=tilt_rdbx_fn, method='WEIGHTED',
                min_zenith=5, max_zenith=35,
                query_str=query_str)
            dev_min_t = pd.DataFrame(vpp.points)['deviation'].min()
            dev_max_t = pd.DataFrame(vpp.points)['deviation'].max()
            ref_min_t = pd.DataFrame(vpp.points)['reflectance'].min()
            ref_max_t = pd.DataFrame(vpp.points)['reflectance'].max()
            tilt_transform = riegl_io.read_transform_file(tilt_transform_fn)
            ttransform_one_line = " ".join(" ".join(f"{v:.6f}" for v in tilt_transform[row]) for row in range(4))


        # Profiles
        vpp.get_pgap_theta_z(min_azimuth=0, max_azimuth=360)
        hinge_pai = vpp.calcHingePlantProfiles()
        weighted_pai = vpp.calcSolidAnglePlantProfiles()
        linear_pai = vpp.calcLinearPlantProfiles()
        hinge_pavd = vpp.get_pavd(hinge_pai)
        weighted_pavd = vpp.get_pavd(weighted_pai)
        linear_pavd = vpp.get_pavd(linear_pai)

        # Metadata
        pattern_v = json.loads(riegl_rdb.readHeader(upright_rdbx_fn)['riegl.scan_pattern'])
        freq_v = pattern_v['rectangular']['program']['name']
        res_v = round(pattern_v['rectangular']['phi_increment'], 2)
        
        pattern_t = json.loads(riegl_rdb.readHeader(tilt_rdbx_fn)['riegl.scan_pattern'])
        freq_t = pattern_t['rectangular']['program']['name']
        res_t = round(pattern_t['rectangular']['phi_increment'], 2)

        vrdbfn = os.path.split(upright_rdbx_fn)[1]
        vrxpfn = os.path.split(upright_rxp_fn)[1]
        trxpfn = os.path.split(tilt_rxp_fn)[1]
        trdbfn = os.path.split(tilt_rdbx_fn)[1]

        # Paired (upright " " tilted) values for header
        rxp_pair = vrxpfn + (" " + trxpfn if use_tilted else " NA")
        rdbx_pair = vrdbfn + (" " + trdbfn if use_tilted else " NA")
        res_pair = f"{res_v} {res_t}" if use_tilted else f"{res_v} NA"
        freq_pair = f"{freq_v} {freq_t}" if use_tilted else f"{freq_v} NA"
        dev_min_max_pair = (f"{dev_min_v} {dev_max_v} " +
                            (f"{dev_min_t} {dev_max_t}" if use_tilted else " NA NA"))
        ref_min_max_pair = (f"{ref_min_v} {ref_max_v} " +
                            (f"{ref_min_t} {ref_max_t}" if use_tilted else " NA NA"))

        # Build table: height + pgap columns + profile columns 
        table = pd.DataFrame({"height": vpp.height_bin})
        for j, b in enumerate(vpp.zenith_bin):
            table[f"vz{int(b*100):05d}"] = vpp.pgap_theta_z[j]

        table["hingePAI"] = hinge_pai
        table["weightedPAI"] = weighted_pai
        table["linearPAI"] = linear_pai
        table["hingePAVD"] = hinge_pavd
        table["weightedPAVD"] = weighted_pavd
        table["linearPAVD"] = linear_pavd

        # Write ASCII file: header block + fixed-width table
        header_lines = [
            f"# location_index : {i}",
            f'# hres_zres_ares  : {vpp.hres} {vpp.zres} {vpp.ares}',
            f"# scanpositions  : {locations.loc[i,'upright_scanposition']} {locations.loc[i,'tilted_scanposition']}",
            f"# rxp_file       : {rxp_pair}",
            f"# rdbx_file      : {rdbx_pair}",
            f"# resolution     : {res_pair}",
            f"# frequency      : {freq_pair}",
            f"# deviation_min_max  : {dev_min_max_pair}",
            f"# reflectance_min_max: {ref_min_max_pair}",
            f"# upright_transform : {utransform_one_line}",
            f"# tilted_transform  : {ttransform_one_line if use_tilted else 'NA'}",
            f"# skip_flag      : {locations.loc[i,'skip']}",
            f"# grid_extent_m  : {grid_extent}",
            f"# grid_res_m     : {grid_resolution}",
            f"# grid_origin_xy : {x0} {y0}",
            f"# plane_abc      : {param_a} {param_b} {param_c}",
            f"# plane_slope_aspect : {plane_slope} {plane_aspect}",
            f"# query_str      : {' ; '.join(query_str)}",
            f"# timestamp      : {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}",
            f"# processed   : {datetime_now}",
            "#",
            "# " + "  ".join(table.columns),
            ""
        ]
        with open(txt_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(header_lines))
            f.write(table.to_string(index=False))
            f.write("\n")

        tqdm.write(f"Wrote: {txt_file_path}")

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="My pylidar script")
    parser.add_argument("input_dir", type=str, help="Path to input directory file")
    parser.add_argument("input_file", type=str, help="Path to input locations CSV file")
    parser.add_argument("--output_dir", type=str, help="path to directory where to save results")
    parser.add_argument("--overwrite", action='store_true', help="Overwrite existing output files")
    args = parser.parse_args()
    
    datetime_now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    # You can put the rest of your code here or call other functions
    profile_vz(args.input_dir, args.input_file, args.output_dir, args.overwrite, datetime_now)

if __name__ == "__main__":
    main()