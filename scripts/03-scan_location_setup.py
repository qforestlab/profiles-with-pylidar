import os
import glob
import laspy
import numpy as np
import pandas as pd
import argparse

from pylidar_tls_canopy import riegl_io

def rotation_matrix_to_yaw_pitch_roll(R):
    pitch = np.arcsin(-R[2, 0])
    yaw = np.arctan2(R[1, 0], R[0, 0])
    roll = np.arctan2(R[2, 1], R[2, 2])
    return np.degrees(yaw), np.degrees(pitch), np.degrees(roll)

def find_azimuth(path_dat_file, path_las_file, angle):
# Calculate azimuth range based on point cloud
    transform_file = riegl_io.read_transform_file(path_dat_file)
    points = laspy.read(path_las_file)
    las_x = np.asarray(points['x'])-transform_file[3,0]
    las_y = np.asarray(points['y'])-transform_file[3,1]
    las_z = np.asarray(points['z'])-transform_file[3,2]
    las_rza = riegl_io.xyz2rza(las_x, las_y, las_z)
    average_azimuth = (np.max(las_rza[-1])+np.min(las_rza[-1]))/2
    return np.degrees(average_azimuth)-angle,np.degrees(average_azimuth)+angle

def process_bis_folder(path_bis_folder, max_dist=1, path_las_file=None, angle=180):
    records = []

    for folder in os.listdir(path_bis_folder):
        folder_path = os.path.join(path_bis_folder, folder)
        if not os.path.isdir(folder_path):
            continue

        rxp_path = glob.glob(os.path.join(folder_path,"*.rxp"))
        if not rxp_path:
            continue
        rxp_file = os.path.basename(rxp_path[0])

        path_dat_file = os.path.join(folder_path, folder + ".DAT")
        if not os.path.exists(path_dat_file):
            continue

        with open(path_dat_file, 'r') as f:
            dat_lines = f.readlines()

        S = np.array(
            [float(val) for i in range(3) for val in dat_lines[i].split()[:4]]
        ).reshape(3, 4)

        R = S[:3, :3]
        t = S[:3, 3]

        y, p, r = rotation_matrix_to_yaw_pitch_roll(R)

        records.append({
            "scanposition": folder,
            "file": rxp_file,
            "x": t[0],
            "y": t[1],
            "z": t[2],
            "yaw": y,
            "pitch": p,
            "roll": r
        })

    df = pd.DataFrame(records)
    if df.empty:
        print("No valid scans found in folder.")
        return pd.DataFrame()

    df["abs_pitch"] = df["pitch"].abs()
    df["orientation"] = np.select(
        [
            df["abs_pitch"] < 10,
            (df["abs_pitch"] > 80) & (df["abs_pitch"] < 100)
        ],
        [
            "upright",
            "tilted"
        ],
        default="other"
    )

    # Assign location IDs
    location_ids = []
    locations_xy = []

    for _, row in df.iterrows():
        assigned = False
        for i, (lx, ly) in enumerate(locations_xy):
            dist = np.sqrt((row.x - lx)**2 + (row.y - ly)**2)
            if dist <= max_dist:
                location_ids.append(i)
                assigned = True
                break
        if not assigned:
            location_ids.append(len(locations_xy))
            locations_xy.append((row.x, row.y))

    df["location_id"] = location_ids

    # Create pairs dataframe
    rows = []
    for loc_id, g in df.groupby("location_id"):
        uprights = g[g["orientation"] == "upright"]
        tilts = g[g["orientation"] == "tilted"]

        upright_scan = uprights.iloc[0] if not uprights.empty else None
        tilt_scan = tilts.iloc[0] if not tilts.empty else None

        # Default azimuth values
        az_min = 0
        az_max = 360

        # Compute azimuth only if requested and possible
        if path_las_file is not None and upright_scan is not None:
            upright_dat = os.path.join(
                path_bis_folder,
                upright_scan.scanposition,
                upright_scan.scanposition + ".DAT"
            )

            if os.path.exists(upright_dat):
                try:
                    az_min, az_max = find_azimuth(
                        path_dat_file=upright_dat,
                        path_las_file=path_las_file,
                        angle=angle
                    )
                except Exception as e:
                    print(f"Azimuth calculation failed for {upright_dat}: {e}")

        rows.append({
            "location_id": loc_id,
            "upright_scanposition": upright_scan.scanposition if upright_scan is not None else pd.NA,
            "tilted_scanposition": tilt_scan.scanposition if tilt_scan is not None else pd.NA,
            "upright_file": upright_scan.file if upright_scan is not None else pd.NA,
            "tilted_file": tilt_scan.file if tilt_scan is not None else pd.NA,
            "upright_pitch": upright_scan.pitch if upright_scan is not None else pd.NA,
            "tilted_pitch": tilt_scan.pitch if tilt_scan is not None else pd.NA,
            "x": g["x"].mean(),
            "y": g["y"].mean(),
            "n_scans": len(g),
            "azimuth_min": az_min,
            "azimuth_max": az_max,
            "skip": "none" if (upright_scan is not None and tilt_scan is not None)
                    else ("tilted" if upright_scan is not None else "all")
        })


    pairs_df = pd.DataFrame(rows)
    return pairs_df

# ------------------- COMMAND LINE INTERFACE -------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process BIS folder and create pairs CSV")
    parser.add_argument("bis_folder", help="Path to the BIS folder containing scan subfolders")
    parser.add_argument("output_csv", help="Path to save the pairs CSV file")
    parser.add_argument("--max_dist", type=float, default=1.0, help="Max distance to consider scans the same location (default=1.0)")
    parser.add_argument("--path_las", type=str, help="Path to the LAS file for azimuth calculation (optional)")
    parser.add_argument("--angle", type=float, default=180.0, help="Angle range for azimuth calculation (default=180)")

    args = parser.parse_args()

    pairs_df = process_bis_folder(args.bis_folder, max_dist=args.max_dist, path_las_file=args.path_las, angle=args.angle)
    if not pairs_df.empty:
        pairs_df.to_csv(args.output_csv, index=False)
        print(f"Pairs CSV saved to: {args.output_csv}")
        print(pairs_df.head())
    else:
        print("No pairs to save.")
