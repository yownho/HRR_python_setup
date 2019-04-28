###########################
#read the nc file of hydraulic conductivity 
# and make the raster of harmonic mean.
#By Yuanhao Zhao
###########################

rm(list = ls())

require(ncdf4)
require(maps)
require(raster)
require(rgdal)

#--------- INPUT Change below as needed ------------#
# Set netCDF folder path, put all nc files and this R code in fdir folder
fncdir <- "C:\\Research\\HRR_0326\\GlobalData\\GlobalData\\theta_s" #, Data source folder, Must use '\\'

# working directory
wkdir <- 'C:\\Research\\Scale_RC_aveVel_0316\\HRRSetup\\1000\\GISworking2' #Must use '\\'
# Note: copy Catchments.shp to this wkdir folder before you run if not there already!!!!!!

#----------------------------#

#####***** MAIN *****#####

# Names of all nc files
names_theta <- list.files(fncdir, pattern = '.nc')

# Read catchments shapefile, dsn is the folder name, layer is the shapefile name
catch <- readOGR(dsn = wkdir, layer = "Catchments")

prj <- "+proj=longlat +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0"

#Project catchment to wgs84
catch <- spTransform(catch, prj)

# loop to generate ascii raster
for (i in 1:length(names_theta)){
  # Generate the name of the nc file
  nc_f <- paste(fncdir, names_theta[i], sep='\\')
  
  # Make the nc file to raster
  ras_nc<-raster(nc_f, varname="theta_s")
  # ras_nc<- projectExtent(ras_nc, crs = prj_m)
  
  # If want to write the raster to a tiff file, uncomment next line
  # writeRaster(rast, filename = f_tiff, format = 'GTiff', overwrite = T)

  # Extract the nc raster by catchments
  nc_extr <- crop(ras_nc, extent(catch), snap="out")   
  
  #theta raster
  theta_lay <- paste('theta',i,sep='_')
  assign(theta_lay, nc_extr)
  
  #Name of the output raster, in ascii format
  ext_ncras <- paste("ext_ncras",i,sep="_")
  ext_nc <- paste(wkdir, ext_ncras,sep = "\\")
  
  #Save the raster of each layer, comment next line if unnecessary
  writeRaster(nc_extr, filename = ext_nc, format = 'ascii', overwrite = TRUE)
}

# theta mean
# The vertical variation of soil property was captured by eight layers to the depth of 2.3 m 
# (i.e. 0- 0.045, 0.045- 0.091, 0.091- 0.166, 0.166- 0.289, 0.289- 0.493, 0.493- 0.829, 
# 0.829- 1.383 and 1.383- 2.296 m).
theta_hm <- (0.045*theta_1 + 0.046*theta_2 + 0.075*theta_3 + 0.123*theta_4 +
                               0.204*theta_5 + 0.336*theta_6 + 0.554*theta_7 + 0.913*theta_8)/2.962

SoilD <- 0.045*theta_1/theta_1 + 0.046*theta_2/theta_2 + 0.075*theta_3/theta_3 + 0.123*theta_4/theta_4 +
  0.204*theta_5/theta_5 + 0.336*theta_6/theta_6 + 0.554*theta_7/theta_7 + 0.913*theta_8/theta_8

# Name of output theta raster
name_kshm <- paste(wkdir,"theta", sep="\\")
name_soilD <- paste(wkdir, "soilD_m", sep="\\")

# Write raster, harmonic mean of theta and soil depth
# Seems all layers have depth (2.296)
writeRaster(theta_hm, filename = name_kshm, format = 'ascii', overwrite = TRUE)
writeRaster(SoilD, filename = name_soilD, format = 'ascii', overwrite = TRUE)

print('Done!')





