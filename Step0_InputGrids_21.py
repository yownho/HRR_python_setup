# Extract input grids (Facc and DEM) with fdir
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy

import sys
print sys.maxsize


arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")


# Local variables:
fdirg = "C:\\Research\\Amazon\\AM_AG_GIS\\grids\\fdir1" #fdir for region, created before this step

facca = "C:\\Research\\NASA_Decomp\\Amazon\\fdiracc\\facca1" #larger than region facc, created before this step
srtm41a = "C:\\Research\\NASA_Decomp\\Amazon\\fdiracc\\srtm41a1" #larger than region facc, created before this step

demg = "C:\\Research\\Amazon\\AM_AG_GIS\\grids\\dem1" #region's facc, will be created in the step
faccg = "C:\\Research\\Amazon\\AM_AG_GIS\\grids\\facc1" #region's facc, will be created in the step

# Process: Extract by Mask
arcpy.env.snapRaster = "fdirg"
arcpy.gp.ExtractByMask_sa(facca, fdirg, faccg)
arcpy.gp.ExtractByMask_sa(srtm41a, fdirg, demg)


