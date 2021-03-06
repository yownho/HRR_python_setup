"""
GIS setup for Hillslope River Routing Model (HRR) Step 3

Parts:
1. Extract DEM data from longest flow path (LFP), measure the slope of LFP for each model unit in percent rise.

Hydro-Geo-Spatial Research Lab
Website: http://www.northeastern.edu/beighley/home/
By: Yuanhao Zhao
Email: zhao.yua@husky.neu.edu
"""

import arcpy, os, os.path
from arcpy import env
from arcpy.sa import *

#####***** input parameters *****#####
drainageDirection = r"C:\Research\NASA_Decomp\Ohio_GIS_basic\fdirm_ohio" # Raster file of flow direction
targetWorkspace = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1000\GISworking2" #Output workspace
DemRas = r"C:\Research\NASA_Decomp\Ohio_GIS_basic\dem_ohio" # dem raster file for whole basin, must be projected "meters"
#slope_m= r"C:\Research\SWOT\SWOT_OH_snap\HRR_swot_OH\SWOT_GIS\slope_m"
slope_m = os.path.join(targetWorkspace,'slope_m')  # this code will make the slope grid
slpstr_m = os.path.join(targetWorkspace,'slpstr_m') # this code will make the slope grid for channel

hrr3 = "HRR_Table3_OH02.dbf" #HRR3 table in 'GIS_working' folder
#####****************************#####

def main ():
	arcpy.env.overwriteOutput = True
	arcpy.CheckOutExtension("Spatial")

	arcpy.env.workspace = targetWorkspace
	

	catchments = "Catchments.shp" #shapefile of catchments
	lfp = "lfpstrd.shp" #longest flow path shapefile
        
	#####***** part1 *****#####    
	isGDB = checkGDB (targetWorkspace) # True if output workspace a geodatabase

	# Create copy of HRR table to add new field to.    
	if isGDB == False:
		StrslpStat = 'StrslpStat.dbf'
		slopeStat = 'slope_stats.dbf'
		hrr4 = 'HRR_Table4.dbf'
	else:
		StrslpStat = 'StrslpStat'
		slopeStat = 'slope_stats'
		hrr4 = 'HRR_Table4'
   			
	StrslpStat = os.path.join (targetWorkspace, StrslpStat) #Stream (LFP) slope
	slopeStat = os.path.join (targetWorkspace, slopeStat) #Catchment slope
   
        arcpy.env.snapRaster = DemRas # Snap raster - fdir
	print 'Slope for lfp'    
	StrDem = arcpy.sa.ExtractByMask(DemRas, lfp)
	slp_str = arcpy.sa.Slope(StrDem, "PERCENT_RISE")
        #slp_str.save(slpstr_m)

	print 'Slope for Basin'
	CatSlope = arcpy.sa.Slope(DemRas, "PERCENT_RISE")
	#CatSlope.save(slope_m)
    
        # set min slope to 0.001m/m (0.1%)
        G1c = CatSlope > 0.1
        G2c = CatSlope <= 0.1
        CatSlopemod = G1c*CatSlope + G2c*0.1
        #CatSlopemod = CatSlope
        CatSlopemod.save(slope_m)  
    
        G1s = slp_str > 0.1 
        G2s = slp_str <= 0.1
        slp_strmod = G1s*slp_str + G2s*0.1
        #slp_strmod = slp_str
        slp_strmod.save(slpstr_m)  
	
	hrr4 = hrr3

	gridCode = checkGC (catchments)

	print ('zonal stats parameters : ' + catchments, gridCode, slp_strmod, StrslpStat, 'DATA', 'MEAN')
	arcpy.sa.ZonalStatisticsAsTable (catchments, gridCode, slp_strmod, StrslpStat, 'DATA', 'MEAN')

	# Join fields from catchments and slope with HRR
	slopeField (hrr4, StrslpStat)

	print 'slope for catchment'
	print ('zonal stats parameters : ' + catchments, gridCode, CatSlopemod, slopeStat, 'DATA', 'MEAN')
	arcpy.sa.ZonalStatisticsAsTable (catchments, gridCode, CatSlopemod, slopeStat, 'DATA', 'MEAN')
		
	# Join fields from catchments and slope with HRR
	slopeFieldCat (hrr4, slopeStat)

	print 'Success!'

def addFields (table, names):
    for n in names:
        arcpy.AddField_management (table, n[0], n[1])

def checkGC (table):
    """ Returns correct Grid Code field. Can be either GRIDCODE or GRID_CODE """
    fields = arcpy.ListFields (table) 
    #Get correct name for gridcode field
    for f in fields:
        if f.name.upper() == "GRID_CODE":
            return "GRID_CODE"
        elif f.name.upper() == "GRIDCODE":
            return "GRIDCODE"

def checkGDB (workspace):
    """ Returns true if GDB, false if not. """
    desc = arcpy.Describe(workspace) 
    isGDB = desc.workspaceType # FileSystem if not GDB, else type of GDB.

    if isGDB != "FileSystem":
        return True
    return False

# gets slope by stream, joins it to HRR table
def slopeField (hrrTable, StrslpStat):
    print StrslpStat, 'is channel slope stat'
    
    hrrGC = checkGC (hrrTable)
    slopeGC = checkGC(StrslpStat)
    
    f1 = arcpy.ListFields(hrrTable)
    for f in f1:
        if f == 'Slope_str' or f == 'Slope_cat':
            arcpy.DeleteField_management (hrrTable, 'Slope_str')
            
    fields = ['MEAN']
    print 'adding field'
    arcpy.AddField_management (hrrTable, 'Slope_str', 'FLOAT')
    print 'joining mean'
    arcpy.JoinField_management (hrrTable, hrrGC, StrslpStat, slopeGC, fields)
    arcpy.CalculateField_management (hrrTable, 'Slope_str', '!MEAN!', 'PYTHON')
    arcpy.DeleteField_management (hrrTable, fields)

def slopeFieldCat (hrrTable, slopeStat):
    print slopeStat, 'is catchment slope'
    
    hrrGC = checkGC (hrrTable)
    slopeGC = checkGC(slopeStat)
    
    f1 = arcpy.ListFields(hrrTable)
    for f in f1:
        if f == 'Slope_cat':
            arcpy.DeleteField_management (hrrTable, 'Slope_cat')
            
    fields = ['MEAN']
    print 'adding field'
    arcpy.AddField_management (hrrTable, 'Slope_cat', 'FLOAT')
    print 'joining mean'
    arcpy.JoinField_management (hrrTable, hrrGC, slopeStat, slopeGC, fields)
    expression = '!MEAN!'
    arcpy.CalculateField_management (hrrTable, 'Slope_cat', '!MEAN!', 'PYTHON')
    arcpy.DeleteField_management (hrrTable, fields)
	
#if __name__ == "__main__":
#    main ();
main ()
