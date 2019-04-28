# Step 4.3 --> process soils data

"""
Hydro-Geo-Spatial Research Lab
Website: http://www.northeastern.edu/beighley/home/
By: Yuanhao Zhao
Email: zhao.yua@husky.neu.edu
"""

import arcpy, os, os.path
from arcpy import env
from arcpy.sa import *

#####***** input parameters CHANGE AS NEEDED*****#####
drainageDirection = r"C:\Research\NASA_Decomp\Ohio_GIS_basic\fdirm_ohio" # Raster file of flow direction
targetWorkspace = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1000\GISworking2" #Output workspace folder
rastPath = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1000\GISworking2" #soils data raster folder path; output from previous step
hrr3 = "HRR_Table3_OH02.dbf" #HRR3 table in 'GIS_working' folder
#####****************************#####

def main ():
	arcpy.env.overwriteOutput = True
	arcpy.CheckOutExtension("Spatial")

	arcpy.env.workspace = targetWorkspace
	arcpy.env.snapRaster = drainageDirection # Snap raster - fdir

	catchments = "Catchments.shp" #shapefile of catchments	

	#####***** Part2 *****#####
	#arcpy.env.cellSize = cellsize
	print 'Soil/Cover properties'
	names = [
		 ["kSat", "FLOAT", "ksat_hm_cm_dp", 1.0],
		 ["effPor", "FLOAT", "thetap", 1.0],
		 ["depth", "FLOAT", "soild_mp", 1.0],
		]

	addFields(hrr3, names)
	fillFields(catchments, hrr3, rastPath, names)

	print 'Success!'


def addFields (table, names):
    #print ("Adding fields")
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

	
def fillFields (fc, outTable, rastPath, names):
    """Performs zonal statistics on all fields"""
    outGC = checkGC(outTable)
    fcGC = checkGC(fc)
    
    for item in names:
        field = item[0]
        file = item[2]
        divisor = item[3]
        
      #  statTable = file
        statTable = "statable"
            
        expression = "(!MEAN!) / " + str (divisor)
        rast = os.path.join (rastPath, file)
        print rast
        desc_rast = arcpy.Describe(rast)
        spatialRef_rast = desc_rast.spatialReference
        print fc, fcGC, rast, statTable
        arcpy.sa.ZonalStatisticsAsTable (fc, fcGC, rast, statTable, "DATA", "MEAN")
        statGC = checkGC (statTable)
    
        arcpy.JoinField_management (outTable, outGC, statTable, statGC, "MEAN")
        print ("calculating field")
        arcpy.CalculateField_management (outTable, field, expression, "PYTHON")
    
        arcpy.DeleteField_management (outTable, "MEAN")
        arcpy.Delete_management(statTable)

if __name__ == "__main__":
    main ();
