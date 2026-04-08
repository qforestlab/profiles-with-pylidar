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
* location_id: a number for each separate location is assigned,
* upright_scanposition: name of the upright ScanPos,
* tilted_scanposition: name of the tilted ScanPos,
* upright_file: name of the upright rxp file,
* tilted_file: name of the tilted rxp file,
* upright_pitch: pitch of the upright ScanPos,
* tilted_pitch: pitch of the tilted ScanPos,
* x: x coordinate of the upright ScanPos,
* y: y coordinate of the upright ScanPos,
* n_scans: number of ScanPos at the location,
* azimuth_start: start azimuth angle based on a given angle and focal point (cloud),
* azimuth_stop: stop azimuth angle based on a given angle and focal point (cloud),
* skip: indicates whether this scan location ('all'), or tilt ('tilted') scan should be skipped when making profiles; default 'none'.

The default settings in the script assume you want a 360 azimuth profile, however, there's an option to input a las/laz point cloud and angle if you want to focus the profile in a certain direction. For example, if I only want scans pointed towards the centre of my circular plot, I can provide the point cloud of an object (for example measuring/flux tower) and an angle of 45 to get the profile 45° left and right of that object. 

```bash
# Activate it
python 03-scan_location_setup.py '/path/to/folder-bis' '/path/to/store/input-locations.csv' --path_las '/path/to/las/file.las' --angle 45

#e.g., python 03-scan_location_setup.py '/Stor2/louise/EucFACE/data/2012/2012.ring1.RiSCAN-bis' '/Stor2/louise/EucFACE/data/2012/2012.ring1.RiSCAN-bis/input-locations-test.csv' --path_las '/Stor2/louise/EucFACE/data/2012/pointclouds/tower/tower_ring1_2012.laz' --angle 45
```

# Step 3: Run profiles
Now everything is ready to produce the vegetation profiles. 

Run the **04-profiles_VZ400i.py** script:
```bash
# Activate it
python 04-profiles_VZ400i.py '/path/to/folder-bis' '/path/to/input-locations.csv' --output_dir '/path/to/output/folder' --overwrite True
```

This will generate a txt file for each scan location which contains information on ...