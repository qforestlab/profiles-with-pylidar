# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 15:36:21 2025

@author: lmterryn
"""


import os
import glob
import shutil


#path to riscan project (*.RiSCAN)
#path_riscan = "path/to/.RiSCAN/project"
path_riscan = r"D:\AmazonFACE\2016-09\RiSCAN\2016-09-17_AF_PLOT8.RiSCAN"


#path and name of folder that goes into the pylidar pipeline = project name (without .RiSCAN)
#path_out = "path/to/data/folder"
path_out = r"F:\AF\2016-09-17_AF_PLOT8.RiSCAN-bis" #r"H:\AF\2025-11-18_AF_PLOT7.RiSCAN-bis" #

pathin_exist = os.path.exists(path_riscan)
if pathin_exist:
    print("input path exists")
else:
    print("input path does not exist!")
    
pathout_exist = os.path.exists(path_out)
if pathout_exist:
    print("output path exists")
else:
    print("output path does not exist, making a folder...")
    os.makedirs(path_out)


scanpos_list = []#['ScanPos035','ScanPos036','ScanPos039','ScanPos040']


### RXP FILES ###
# when PROJ folder was copied during import
# loop over all ScanPosXXX folders in .Riscan/SCANS/ and copy rpx files
# for folder in glob.glob(os.path.join(path_riscan, "2025-07-10_ForSe_Gontrode.PROJ", "*.SCNPOS"), recursive = True):
    
#     # create output folders if not exists (ScanPosxxx)
#     path_scanpos = os.path.join(path_out,os.path.basename(os.path.normpath(folder)).split(".")[0])
#     if not os.path.exists(path_scanpos):
#         os.mkdir(path_scanpos)

#     # copy all rxp files (not .residual.rxp) to output folder
#     for file in glob.glob(os.path.join(folder,"scans","*.rxp")):
#         if len(os.path.basename(file)) == 17:
#             if not (os.path.exists(os.path.join(path_scanpos, os.path.basename(file)))):
#                 shutil.copyfile(file, os.path.join(path_scanpos, os.path.basename(file)))
                
# loop over all ScanPosXXX folders in .Riscan/SCANS/ and copy rpx files


for folder in glob.glob(os.path.join(path_riscan, "SCANS", "*"), recursive = True):
    if len(scanpos_list) != 0:
        if os.path.basename(os.path.normpath(folder)) in scanpos_list:
            # create output folders if not exists (ScanPosxxx)
            path_scanpos = os.path.join(path_out,os.path.basename(os.path.normpath(folder)))
            if not os.path.exists(path_scanpos):
                os.mkdir(path_scanpos)
        
            # copy all rxp files (not .residual.rxp) to output folder
            for file in glob.glob(os.path.join(folder,"SINGLESCANS","*.rxp")):
                if len(os.path.basename(file)) == 17:
                    if not (os.path.exists(os.path.join(path_scanpos, os.path.basename(file)))):
                        shutil.copyfile(file, os.path.join(path_scanpos, os.path.basename(file)))
    else:
        # create output folders if not exists (ScanPosxxx)
        path_scanpos = os.path.join(path_out,os.path.basename(os.path.normpath(folder)))
        if not os.path.exists(path_scanpos):
            os.mkdir(path_scanpos)
    
        # copy all rxp files (not .residual.rxp) to output folder
        for file in glob.glob(os.path.join(folder,"SINGLESCANS","*.rxp")):
            if len(os.path.basename(file)) == 17:
                if not (os.path.exists(os.path.join(path_scanpos, os.path.basename(file)))):
                    shutil.copyfile(file, os.path.join(path_scanpos, os.path.basename(file)))


### RDBX FILES ####
# loop over all ScanPosXXX folders in project.rdb/SCANS/ and copy rdbx files
for folder in glob.glob(os.path.join(path_riscan,"project.rdb", "SCANS", "*"), recursive = True):
    if len(scanpos_list) != 0:
        if os.path.basename(os.path.normpath(folder)) in scanpos_list:
            # create output folders if not exists (ScanPosxxx)
            path_scanpos = os.path.join(path_out,os.path.basename(os.path.normpath(folder)))
            if not os.path.exists(path_scanpos):
                os.mkdir(path_scanpos)
                
            # in .rdb folders, there is a directory per scan, so loop over those
            # and copy all rdbx files to output folders
            for scanfolder in glob.glob(os.path.join(folder, "SINGLESCANS", "*")):
                for file in glob.glob(os.path.join(scanfolder,"*.rdbx")):
                    if "@" not in os.path.basename(file):
                        if not (os.path.exists(os.path.join(path_scanpos, os.path.basename(file)))):
                            shutil.copyfile(file, os.path.join(path_scanpos, os.path.basename(file)))
    else:
        # create output folders if not exists (ScanPosxxx)
        path_scanpos = os.path.join(path_out,os.path.basename(os.path.normpath(folder)))
        if not os.path.exists(path_scanpos):
            os.mkdir(path_scanpos)
            
        # in .rdb folders, there is a directory per scan, so loop over those
        # and copy all rdbx files to output folders
        for scanfolder in glob.glob(os.path.join(folder, "SINGLESCANS", "*")):
            for file in glob.glob(os.path.join(scanfolder,"*.rdbx")):
                if "@" not in os.path.basename(file):
                    if not (os.path.exists(os.path.join(path_scanpos, os.path.basename(file)))):
                        shutil.copyfile(file, os.path.join(path_scanpos, os.path.basename(file)))

## DAT FILES ##
# copy the SOPs (DAT files) assuming they are just in the RiSCAN PRO main folder
# therefore manually export the .dat files from the riscan project 
# (registration>multiple SOP export> in the project.rdb>scans folder)

# loop over all ScanPosXXX folders in project.rdb/SCANS/ and copy rdbx files
for dat_file in glob.glob(os.path.join(path_riscan, "ScanPos*.DAT")):
    scanpos_name = os.path.splitext(os.path.basename(dat_file))[0]
    if len(scanpos_list) != 0:
        if os.path.basename(os.path.normpath(folder)) in scanpos_list:
            # create output folders if not exists (ScanPosxxx)
            path_scanpos = os.path.join(path_out, scanpos_name)
            if not os.path.exists(path_scanpos):
                os.mkdir(path_scanpos)
        
            # copy all dat files to output folder
            if not (os.path.exists(os.path.join(path_scanpos, os.path.basename(dat_file)))):
                shutil.copyfile(dat_file, os.path.join(path_scanpos, os.path.basename(dat_file)))
    else:
        # create output folders if not exists (ScanPosxxx)
        path_scanpos = os.path.join(path_out, scanpos_name)
        if not os.path.exists(path_scanpos):
            os.mkdir(path_scanpos)

        # copy all dat files to output folder
        if not (os.path.exists(os.path.join(path_scanpos, os.path.basename(dat_file)))):
            shutil.copyfile(dat_file, os.path.join(path_scanpos, os.path.basename(dat_file)))












