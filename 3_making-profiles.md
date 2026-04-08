---
title: "Making Vegetation Profiles (RIEGL TLS)"

---

# Overview
This guide briefly explains how to make vegetation profiles for RIEGL VZ data using the **03-scan_location_setup.py** and **04-profiles_VZ400i.py** scripts.

# Step 1: Setup
Make sure you copy the bis folder you created during the data preparation step to your WSL workspace or the linux machine (for QFL'ers use the Stor drives) your working on. Think about a good folder structure to work efficiently (e.g. make a **code** folder to store scripts, **data** folder where you put the bis folder(s), an **output** folder with subfolders to put your profiles).

Download and copy the **03-scan_location_setup.py** and **04-profiles_VZ400i.py** scripts to your code folder and navigate to this folder:
```bash
# Navigate to your code folder
cd name/of/code/folder 
```

> **Tip**: Clone the profiles-with-pylidar repository from GitHub.

Activate your pylidar environment:
```bash
# Activate conda environment
conda activate <env-name>   # e.g., conda activate pylidar-tls-canopy
```

# Step 2: Get scan locations
Before actually generating the profiles we make a .csv file which links the upright an tilt scans. This .csv file then feeds into the next step. The script determines whether a scan is upright or tilted based on the pitch of the scan and whether scans are done at the same location based on the distance between the scans. 

Run the **03-scan_location_setup.py** script:
```bash
# Activate it
python 03-scan_location_setup.py '/path/to/folder-bis' '/path/to/store/input-locations.csv' 

#e.g., python 03-scan_location_setup.py '/Stor2/louise/EucFACE/data/2012/2012.ring1.RiSCAN-bis' '/Stor2/louise/EucFACE/data/2012/2012.ring1.RiSCAN-bis/input-locations-test.csv'
```
This will generate an output csv with the columns:
| Field | Description |
|---|---|
| `location_id` | Unique number assigned to each scan location |
| `upright_scanposition` | Name of the upright scan position |
| `tilted_scanposition` | Name of the tilted scan position |
| `upright_file` | Name of the upright `.rxp` file |
| `tilted_file` | Name of the tilted `.rxp` file |
| `upright_pitch` | Pitch angle of the upright scan position |
| `tilted_pitch` | Pitch angle of the tilted scan position |
| `x` | X coordinate of the upright scan position |
| `y` | Y coordinate of the upright scan position |
| `n_scans` | Number of scan positions at the location |
| `azimuth_start` | Start azimuth angle defined relative to a given angle and focal point |
| `azimuth_stop` | Stop azimuth angle defined relative to a given angle and focal point |
| `skip` | Indicates whether to skip the full location (`all`), the tilted scan only (`tilted`), or neither (`none`) |

The default settings in the script assume you want a 360 azimuth profile, however, there's an option to input a las/laz point cloud and angle if you want to focus the profile in a certain direction. For example, if I only want scans pointed towards the centre of my circular plot, I can provide the point cloud of an object (for example measuring/flux tower) and an angle of 45 to get the profile 45° left and right of that object. 

```bash
# Activate it
python 03-scan_location_setup.py '/path/to/folder-bis' '/path/to/store/input-locations.csv' --path_las '/path/to/las/file.las' --angle 45

#e.g., python 03-scan_location_setup.py '/Stor2/louise/EucFACE/data/2012/2012.ring1.RiSCAN-bis' '/Stor2/louise/EucFACE/data/2012/2012.ring1.RiSCAN-bis/input-locations-test.csv' --path_las '/Stor2/louise/EucFACE/data/2012/pointclouds/tower/tower_ring1_2012.laz' --angle 45
```

# Step 3: Run profiles
Now everything is ready to produce the vegetation profiles. 

>[!Note]
> See section at the end of the page to understand different methods available in pylidar.

Run the **04-profiles_VZ400i.py** script:
```bash
# Activate it
python 04-profiles_VZ400i.py '/path/to/folder-bis' '/path/to/input-locations.csv' --output_dir '/path/to/output/folder' --overwrite True
```

This will generate a txt file for each scan location with a header and body. The header contains the following information:


| Field | Description |
|---|---|
| `location_index` | Row index of the scan location in the input CSV file |
| `hres_zres_ares` | Height resolution (m), zenith resolution (°), and azimuth resolution (°) used to bin the profile |
| `scanpositions` | Names of the upright and tilted scan positions as defined in the input CSV |
| `rxp_file` | Names of the upright and tilted `.rxp` raw waveform files |
| `rdbx_file` | Names of the upright and tilted `.rdbx` point cloud files |
| `resolution` | Angular step size (°) of the scan pattern for the upright and tilted positions |
| `frequency` | Pulse repetition frequency programme name for the upright and tilted positions |
| `deviation_min_max` | Minimum and maximum pulse deviation values for the upright and tilted positions |
| `reflectance_min_max` | Minimum and maximum target reflectance (dB) for the upright and tilted positions |
| `range_min_max` | Minimum and maximum target range (m) for the upright and tilted positions |
| `upright_transform` | 4×4 transformation matrix registering the upright scan to the site coordinate system |
| `tilted_transform` | 4×4 transformation matrix registering the tilted scan to the site coordinate system |
| `skip_flag` | Indicates whether the tilted position or full location was skipped |
| `grid_extent_m` | Spatial extent (m) of the ground grid used for plane fitting |
| `grid_res_m` | Cell resolution (m) of the ground grid |
| `grid_origin_xy` | x and y coordinates of the grid origin |
| `plane_abc` | Coefficients of the fitted ground plane equation |
| `plane_slope_aspect` | Slope (°) and aspect (°) of the fitted ground plane |
| `query_str` | Point filters applied during processing |
| `timestamp` | UTC time at which the output file was written |
| `processed` | UTC time at which the processing run was initiated |


The body contains the following columns:

| Field | Description |
|---|---|
| `height` | Height bin (m) above ground |
| `vz*****` | Gap fraction (pgap) per zenith angle bin. Each column corresponds to a zenith angle in degrees, encoded as an integer (e.g. `vz03750` = 37.5°, `vz04250` = 42.5°) | |
| `hingePAI` | Cumulative plant area index estimated using the hinge angle method |
| `weightedPAI` | Cumulative plant area index estimated using the solid angle weighted method |
| `linearPAI` | Cumulative plant area index estimated using the linear method |
| `hingePAVD` | Plant area volume density derived from the hinge angle PAI profile |
| `weightedPAVD` | Plant area volume density derived from the solid angle weighted PAI profile |
| `linearPAVD` | Plant area volume density derived from the linear PAI profile |

## Additional information on methods in pylidar 

## Additional information on methods in pylidar

### Background: gap fraction estimation

The gap fraction at each zenith angle and height bin is computed as:

$$
P_{gap}(\theta, z) = 1 - \frac{\text{cumulative interceptions}}{\text{total shots}}
$$

Two sources of bias can affect this estimate:

> [!WARNING]
> **Inflated numerator — orphan returns:** If returns present in the `.rdbx` file have no matching pulse in the `.rxp` file, they contribute to the interception count without a corresponding shot in the denominator. This drives the cover fraction above 1, producing negative pgap values.

> [!WARNING]
> **Inflated denominator — pulse filtering:** If pulses whose returns were all removed by `query_str` are not removed from the shot count (`pulse_filter=False`), the denominator grows. This reduces the cover fraction and underestimates PAI, as pulses that were intercepted by the canopy but failed the query filter are counted as gaps instead of interceptions.

---

### 1) `add_riegl_scan_position` vs `add_riegl_scan_position_scanline`

The `_scanline` variant is an extended version of the original method that introduces two additional capabilities.

**Orphan return removal**
It uses the scanline index to correctly join the `.rdbx` and `.rxp` files via an inner merge on `scanline` and `scanline_idx`. This discards orphan returns — points present in the `.rdbx` file that have no matching pulse in the `.rxp` file — ensuring only returns with a valid corresponding pulse are used in the profile calculation. This option cannot be adjusted in `add_riegl_scan_position_scanline`. To not use this option, use the classical `add_riegl_scan_position`.

**Additional arguments**
- `pulse_filter`: By default (`pulse_filter=False`), pulses are retained in the shot denominator even if none of their returns passed the `query_str` filter. Setting `pulse_filter=True` removes these pulses from the denominator as well, so that only pulses with at least one valid return contribute to the gap fraction calculation.

> [!WARNING]
> This can affect PAI estimates and should be used with caution, as it affects the definition of what constitutes a gap.

- `point_data`: Setting `point_data=True` stores the full point cloud in memory for downstream diagnostics, and additionally records the minimum and maximum values of reflectance, deviation, and range for each scan position.

> [!WARNING]
> Retaining point clouds could result in very large objects. It is advised to use this option sparingly to diagnose the data that was used to compute Pgap.

> [!NOTE]
> These methods and arguments are not available in the classical `add_riegl_scan_position`. The script **04-profiles_VZ400i.py** is written to run `add_riegl_scan_position_scanline` by default.

---

### 2) `get_pgap_theta_z` vs `get_pgap_theta_z_sector`

Both methods compute the gap fraction by zenith angle and height bin, averaged over a specified azimuth range. The difference is in how the azimuth range is defined.

- `get_pgap_theta_z` takes a centre-based range (`min_azimuth`, `max_azimuth`) and selects all bins within that window.
- `get_pgap_theta_z_sector` takes explicit start and stop edges and correctly handles **wrap-around sectors** that cross 0°/360° — for example, a sector from 350° to 30° is handled by selecting bins above 350° or below 30°, rather than treating it as an empty or invalid range.

`get_pgap_theta_z_sector` is the preferred method when scan positions cover a restricted or asymmetric azimuth range.