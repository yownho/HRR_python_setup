# Project DEM to meters 
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

# change the folder\name of the input DEM and output DEM with projected units
demg = r"C:\Research\NASA_Decomp\Ohio_GIS_basic\dem_oh_wgs"
demg_m = r"C:\Research\SWOT\SWOT_OH_snap\HRR_swot_OH\improveOH\swotoh_m"

# change the folder\name of the output cooridnate system for your region
projection = r"C:\Research\HRR_0326\2.1\2.1\Lambert Azimuthal Eq Area N America (Flood).prj" #meters

# Process: Project Raster
# change "90 90" if input dem is not 3 sec resolution; 90 90 represents output pixel size in meters
arcpy.ProjectRaster_management(demg, demg_m, projection, "BILINEAR", "90 90")

print('Done!')
