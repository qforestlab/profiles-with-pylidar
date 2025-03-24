# Data preparation

Here, we describe how to prepare your data for making vegetation profiles. This manual assumes your RIEGL TLS data has already been processed (e.g. co-registered) using these manuals ([VZ400i](https://github.com/qforestlab/riscan_registration/tree/main) & [VZ400](https://github.com/qforestlab/riscan-registration-VZ400)).

## Input files
Making vegetation profiles using pylidar requires 3 files for each scan position: the .rxp, .rdbx and .dat file. These three files (.rxp, .rdbx, .dat) are extracted from the .RiSCAN project. 

### RXP
The .rxp file format is RIEGL’s proprietary raw data format used to store terrestrial LiDAR scan data. It contains detailed point cloud information, including 3D coordinates, intensity, multiple returns, and scanner metadata such as timestamps and instrument settings. 

The .rxp files are created on the scanner when the scanning is done. So they are already present in the raw data (.PROJ) folder. But these files will also be present in the .RiSCAN project folder after importing. 

### RDBX
The .rdbx file in RIEGL’s LiDAR workflow is a project database used within RiSCAN PRO to organize scan data, metadata, and processing steps, including Multiple-Time-Around (MTA) corrections. When working with long-range terrestrial LiDAR data where multiple laser pulses may overlap in time, MTA processing is essential for accurately resolving pulse ambiguities. Once MTA is applied, the corrected point cloud data is stored and managed within the .rdbx structure.

RIEGL's MTA (Multiple Time Around) processing is especially valuable in terrestrial laser scanning (TLS) of forest environments, where complex canopy structures and varying distances can cause overlapping laser pulse returns. The laser scanners may emit new pulses before previous ones have fully returned due to dense vegetation or long-range targets like tall trees or gaps in the canopy. MTA processing ensures that each return is accurately linked to its correct emitted pulse, preventing range ambiguities and ghost points. 

Sometimes during scanning the scanner also produces .rdbx files, which you can find in the raw data but these files are NOT to be used (ignore them) as they have not been fully processed. We want to use the .rdbx files created after importing and converting in RiSCAN PRO. 
To get the right RDBX files it is important that these files were imported & converted with the GPU processing switched off and no filtering. However, during co-registration this is often not the case, therefore it is important to re-convert the scans which re-does the conversion from the .rxp files and thus removes the filtering. Follow these steps:
1. Open the RiSCAN PRO project of interest
2. Switch off the GPU processing by going to tools > settings > general > data acquisition
   
![](./img/gpu_settings.png)

3. Re-convert the scans by right-clicking the scan files. You can select multiple files and right-click to convert them all together.

![](./img/select_all.png)
![](./img/convert.png)

### DAT
The .dat files contain the Sensor's Orientation and Position for each scan position. 

These files are generally created after finishing co-registration of a RiSCAN project for data management purposes (see [this manual](https://github.com/qforestlab/riscan-registration-VZ400/blob/main/8_save_combine.md)). Make sure these individual SOP files are exported to the .RiSCAN folder. 

![](./img/SOP_export.png)

## File organisation
Use this [data preparation script](./scripts/02-data_preparation.py) to copy all the required files from the .RiSCAN project to a folder which you will use as an input for pylidar. 

## Why are we doing this?

Gap-fraction methods use the information regarding the origin of a pulse and all of its returns. 
By linking the two sources of information we can basically get an idea of how the pulse of light traveled through the canopy and, importantly, where it was intercepted by vegetation, as recorded by the pulse returns. 
Therefore, it is essential to have accurate return information. The advancement in scanning systems allows us to scan at high frequencies (upto 1200 kHz in VZ400i). 
Scanning at high speeds necessitates processing the raw lidar signal to correctly identify the pulse returns, which is done by the MTA processing.
RiSCAN PRO uses the GPU for MTA processing, when available, to convert the .rxp to .rdbx. We observed that the use of GPU can result in inconsistent and incorrect handling of the returns. 
Therefore, we only use CPU to make sure the resulting .rdbx files are the same, thereby ensuring reproducibility. 

To check the that you are getting reproducible .rdbx files, you can access the convert logs (found here: "yourproject.RiSCAN\\project.rdb\\SCANS\\ScanPos001\\SINGLESCANS\\yourscan_timestamp\\").
Scroll down to the statistics section and observe the values in each zone. The number of zones increases with higher scan frequencies. The 'echoes' in each zone need to remain constant after conversion for reproducible results. 
We have observed these values to be changing depending on whether the GPU was ON or not and whether the GPU was ON but the conversion tool switched to OFF midway, in each case resulting in a different .rdbx file for the same .rxp file.


![](./img/convert_logs.png)


