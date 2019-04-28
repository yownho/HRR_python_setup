"""
GIS setup for Hillslope River Routing Model (HRR) step 1

Parts:
1. Creation of Flow Accumulation Threshold Grid, Stream Link, Watershed, Watershed Polygon,
   and Derived River Network;
2. Create longest flow path shapefile. Unlike stream shapefile, the lfp is based on 10sqkm (or even smaller
   drainage area).

Hydro-Geo-Spatial Research Lab
Website: http://www.northeastern.edu/beighley/home/
By: Yuanhao Zhao
Email: zhao.yua@husky.neu.edu
"""
import arcpy, os.path
from arcpy import env
from arcpy.sa import *
from operator import itemgetter, attrgetter
import sys

arcpy.ResetEnvironments()

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")
arcpy.env.parallelProcessingFactor = "100%"

#####***** input parameters *****#####

#If based on hydrosheds 3-sec data use below; most cases
unit = 'Degree'                 # Unit for DEM grid, Meter or Degree
DEMcellSize = 0.00083333333     # Grid size of DEM data, Meters or decimal degrees for pixels

targetWorkspace = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1000\GISworking2" # Folder; Output workspace (lots of files will be saved here)
flowAccumulation = r"C:\Research\NASA_Decomp\Ohio_GIS_basic\faccm_ohio"  # Raster file of flow accumulation
drainageDirection = r"C:\Research\NASA_Decomp\Ohio_GIS_basic\fdirm_ohio" # Raster file of flow direction

# Threshold area to determine stream network tip area, sqkm
# adjust this value to increase or decrease number of streams/catchments
A_thrhld = 1000      

# Threshold area for longest flow path, sqkm 
# A value of 10 is good unless, A_thrhld is 50 or less
A_thrhold_lfp = 1.0

# Threshold to determine longest flow path (LFP) for headwater catchments. Here the number is
# number of pixels, determined by user (please check lfpstr.shp in GIS after)
# Mostly will not need to change below
num_tip = 10.0                                            
                                                        
#####****************************#####

#####*****First part*****#####
if unit == 'Meter':
	lngThreshold = int(A_thrhld/(DEMcellSize*0.001)/(DEMcellSize*0.001)) + 1
	lfpThreshold = int(A_thrhold_lfp/(DEMcellSize*0.001)/(DEMcellSize*0.001)) + 1
	lfptip = num_tip*DEMcellSize
elif unit == 'Degree':
	lngThreshold = int(A_thrhld/(DEMcellSize*60*60*30*0.001)/(DEMcellSize*60*60*30*0.001)) + 1
	lfpThreshold = int(A_thrhold_lfp/(DEMcellSize*60*60*30*0.001)/(DEMcellSize*60*60*30*0.001)) + 1
	lfptip = num_tip*DEMcellSize
else:
    print 'Error: Units are not set'
    sys.exit()

print lngThreshold, lfpThreshold, lfptip

arcpy.env.workspace = targetWorkspace
arcpy.env.extent = drainageDirection
arcpy.env.scratchWorkspace = targetWorkspace

# Set output variables, no need to modify 
strGrid = "StrGrid"
streamLink = "StrLink"
streams = "Streams.shp"  #stream network feature
watershed = "Watersheds"
catchmentsAll = "Catch_many.shp"
catchments = "Catchments.shp" #catchments feature
maxFacc = "MaxFAcc.dbf"
rivPt = "River_Pts.shp"
lfpTable = "lfp.dbf"
maxfl = "maxfl"
outlfp = "lfp"
lfp_str = "lfpstr.shp" #longest flow path for headwater catchments. Same for inter basin catchments.

desc = arcpy.Describe(targetWorkspace)
isGDB = desc.workspaceType # FileSystem if not GDB, else type of GDB.

if isGDB != "FileSystem":
    catchments = catchments [:-4]
    streams = streams [:-4]
    catchmentsAll = catchmentsAll [:-4]
    maxFacc = maxFacc [:-4]
    rivPt = rivPt [:-4]

# Execute and Save Stream Grid file of all streams in catchments greater than lngThreshold
outFlowAccumulationRC = Raster(flowAccumulation) >= lngThreshold
outFlowAccumulationRC.save(strGrid)
print 'Stream Grid grid created successfully'

# Execute and Save Stream Link Grid
outStreamLink = StreamLink(strGrid, drainageDirection)
outStreamLink.save(streamLink)
print 'Stream link grid created successfully'

# Execute Stream to Feature
StreamToFeature(streamLink, drainageDirection, streams, "NO_SIMPLIFY")
print 'Derived streams feature class created successfully'

# Execute and Save Watershed Grid
outWatershed = Watershed(drainageDirection, streamLink)
outWatershed.save(watershed)
print 'Watershed grid created successfully'

# Convert watershed grid to polygons
arcpy.RasterToPolygon_conversion(watershed, catchmentsAll, "NO_SIMPLIFY", "VALUE")
print 'Watershed grid converted to polygons successfully'

# Dissolve Watershed polygons
arcpy.Dissolve_management(catchmentsAll, catchments, "GRIDCODE")
print 'Watershed polygons dissolved successfully'

arcpy.RasterToPoint_conversion (streamLink, rivPt, "VALUE")
print 'Created stream link point file'

arcpy.sa.ZonalStatisticsAsTable (catchments, "GRIDCODE", flowAccumulation, maxFacc, "DATA", "MAXIMUM" )
print 'Max Flow Accumulation table created'

#####*****Goal 2*****#####
print 'Create upd raster'
fdir1 = SetNull(flowAccumulation <= lfpThreshold,drainageDirection)
downl = FlowLength(fdir1, "DOWNSTREAM", "")
upl = FlowLength(fdir1, "UPSTREAM", "")
upd = downl + upl

print 'zonal'
ZonalStatisticsAsTable(catchments, "GRIDCODE", upd, lfpTable, "DATA", "MAXIMUM")
arcpy.JoinField_management (catchments, "GRIDCODE", lfpTable, "GRIDCODE")

print 'Get maxfl raster'
arcpy.PolygonToRaster_conversion(catchments, "MAX", maxfl, "CELL_CENTER", "NONE", DEMcellSize)

print 'Get LFP raster'
lfp = (upd + lfptip) > maxfl 

#lfp.save(outlfp) #LFP grid

#Create LFP feature shapefile
print 'make raster to feature'
lfpR = SetNull(lfp, lfp, "Value = 0")
arcpy.RasterToPolyline_conversion(lfpR, lfp_str,"ZERO","","NO_SIMPLIFY","")

print 'Success!'
