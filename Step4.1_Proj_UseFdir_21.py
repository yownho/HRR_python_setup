# Step 4.1 --> setup soils and LC data

"""
Note: Please extract soil raster files based on catchment before this step (see R codes). 
In: soil and LC raster files, project them using flow direction raster file.
Out: Projected soil and LC raster files have same coordinate system as flow direction raster

@author: Yuanhao
"""

import arcpy, os, os.path
from arcpy import env
from arcpy.sa import *

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

#####***** input parameters CHANGE AS NEEDED *****#####
targetWorkspace = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1000\GISworking2" # Working folder (soils data from R code there too)
drainageDirection = r"C:\Research\NASA_Decomp\Ohio_GIS_basic\fdirm_ohio" # Raster file of flow direction
global_rastPath = r"C:\Research\HRR_0326\GlobalData\GlobalData\LandCover2012" # Folder, contains all origin golbal LC raster file
rast_global = ['lc2012']   # Landcover raster file in global raster path folder (above) that you want to extract 
                             
# need to run two R codes first
# Names of raster files for catchments will be projected using flow direction raster
# *.asc files made with R codes
rast_cat = ['ksat_hm_cm_d.asc', 'theta.asc', 'soilD_m.asc', 'lc2012_ex']

#####**********DO NOT CHANGE BELOW******************#####

arcpy.env.workspace = targetWorkspace
arcpy.env.snapRaster = drainageDirection # Snap raster - fdir
arcpy.env.extent = drainageDirection
inRectangle = arcpy.env.extent

#%% Part 1: extract soil property raster files by flow direction raster of basin
for name in rast_global:
    print name
    rast = os.path.join(global_rastPath, name)
    rastoutn = name+'_ex'
    rastout = os.path.join(targetWorkspace, rastoutn)
    
#    outras = ExtractByMask(rast, drainageDirection)
#    outras.save(targetWorkspace+'\\'+name+'_cat')
    
    rectExtract = ExtractByRectangle(rast, inRectangle, "INSIDE")
    rectExtract.save(rastout)
    
    
#%% Part 2: Project the soil raster files which are not in projection of flow direction 
fdircellsize = arcpy.GetRasterProperties_management(drainageDirection, "CELLSIZEX") # cell size
desc_fdir = arcpy.Describe(drainageDirection)
coor_system = desc_fdir.spatialReference

print 'Start to project...'
for name in rast_cat:
    print name
    rast = os.path.join (targetWorkspace, name)
    desc_rast = arcpy.Describe(rast)
    
    if desc_rast.extension == 'asc':
        rastN = rast[:-4]
        arcpy.ASCIIToRaster_conversion(rast, rastN, "FLOAT")
        
        desc_rastN = arcpy.Describe(rastN)
        spatialRef_rastN = desc_rastN.spatialReference
        if spatialRef_rastN.Name == 'Unknown':
            arcpy.DefineProjection_management(rastN, '4326')
            
        rastp = rastN+'p' # p means projected
        arcpy.ProjectRaster_management(rastN, rastp, drainageDirection, 'BILINEAR', fdircellsize)
    else:
        rastp = rast+'p'
        if rast[-9:] == 'lc2012_ex':
            print 'Nearest'
            arcpy.ProjectRaster_management(rast, rastp, drainageDirection, 'NEAREST', fdircellsize)
        else:
            arcpy.ProjectRaster_management(rast, rastp, drainageDirection, 'BILINEAR', fdircellsize)
        
print 'Success!'
