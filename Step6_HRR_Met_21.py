"""
GIS setup for Hillslope River Routing Model (HRR) Step 6

Objectives:
1. Take catchment, met polygon IDs. Calculate area of each part of the catchment, then calculate 
   weight (wt) by percent area for each part of the catchment. Sort by catchment ID (GRID_CODE), small to large. 
2. Output text file contains met data.

Hydro-Geo-Spatial Research Lab
Website: http://www.northeastern.edu/beighley/home/
By: Yuanhao Zhao
Email: zhao.yua@husky.neu.edu
"""

import arcpy, csv, os, os.path, subprocess, shutil, time
from operator import itemgetter, attrgetter

arcpy.CheckOutExtension("Spatial")

#####***** Input parameters *****#####
zone = '07'
region = 'OH'
outputSpace = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1\HRRtxt" #Location for final text files that contain met overlay tables
fortSpace = r"C:\Research\HRR_0326\2.1\2.1\MetCC" # Folder contains origianl met data, location of overlay4.exe                
hrr = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1\GISworking\HRR_Table3_OH07.dbf"   #Location of final HRR 3 table in GIS folder
catchments = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1\GISworking\Catchments.shp" #Fianl catchments shapefile in GIS folder
gridList = ['TRMM'] # Name of met data, must match the met data grid in 'met_bas' folder. 
#For example, 'TRMM' matches 'TRMM_Grid.shp'. If want to use other data source, the format must be ####_Grid.shp
#####*********DO NOT CHANGE ANYTHING BELOW*******************#####

arcpy.env.workspace = outputSpace
arcpy.env.overwriteOutput = True

def main ():
	
	#Start run
    place = '{1}{0}'.format (zone, region)

    for cpcet in gridList:
        # Run code for grid

        cpcName = cpcet + '_Grid.shp'
        cpcPoly = os.path.join(fortSpace,cpcName)
        intTable = os.path.join (outputSpace, "{}_Zones_{}.shp".format (cpcet, place)) #intersected table, output

        print 'working on', place, cpcet

        setup (catchments, cpcPoly, intTable, hrr)
  
        dataRec = getData (intTable, cpcet, cpcPoly)
        dataRec = calcWt (dataRec)

        writeCSV (dataRec, fortSpace, cpcet)

        fortranCall (fortSpace, outputSpace, place, cpcet) 
    print 'success!'


def addFields (table, fields):
    for f in fields:
        arcpy.AddField_management (table, f[0], f[1])
        

def checkGC (table):
    """ Returns correct Grid Code field. Can be either GRIDCODE or GRID_CODE """
    fields = arcpy.ListFields (table)
    #Get correct name for gridcode field
    for f in fields:
        if f.name.upper() == "GRID_CODE":
            return f.name.upper ()
        elif f.name.upper() == "GRIDCODE":
            return f.name.upper ()

def setup (catch, cpc, iTable, hrr):
    """ Creates intersected, projected shapefile, adds and calculates
       weight field, and adds weight (wt) field. """

    arcpy.Intersect_analysis ([catch, cpc], iTable)
    print 'intersect done'

    fields = ['AP_sqkm', "DOUBLE"]
    
    arcpy.AddField_management (iTable, fields[0], fields[1])
    print 'fields added'

    iTableGC = checkGC (iTable)
    hrrGC = checkGC (hrr)

    arcpy.JoinField_management (iTable, iTableGC, hrr, hrrGC, "HRR_ID")
    print "joined hrr"
 
    expression = "!SHAPE.AREA@SQUAREKILOMETERS !"
    arcpy.CalculateField_management (iTable, fields [0], expression, "PYTHON")
    print 'field calculated'

    print 'Setup completed'

def getData (table, cpcet, cpc):
    """ Reads data from the intersected cpc/grid table. """
    
    gc = checkGC (table)
    print 'gridcode is ', gc
    
    field_names = [f.name for f in arcpy.ListFields(cpc)]  
    #metID = field_names[2]

    if cpcet == "TRMM":
        metID = "TRMMID"
    if cpcet == "RRET25Congo":
        metID = "ETID"
    if cpcet == "RRET25ag":
        metID = "ETIDag"
    if cpcet == "GCM":
        metID = "GCMID"      

    print metID
   

    fields = ["HRR_ID", gc, metID, "AP_SQKM", "SHAPE@AREA"]
           
    data = {"grid": [],
            "hrr": [],
            "cpc": [],
            "ap": [],
            "area": [],
            "wt": []
            }
    
    with arcpy.da.SearchCursor (table, fields) as cursor:
          
        # Sort on HRR_ID
        cursor = sorted(cursor, key = itemgetter(0))
        # extract data to lists
        for row in cursor:
            data["cpc"].append (row[2])
            data["grid"].append (row[1])
            data["hrr"].append (row [0])
            data["ap"].append (row[3])
            data["area"].append (row [4])
    print 'cursor run'
    return data

            

def calcWt (data):
    numRecs = len(data["hrr"])
    areaDict = {} # Dictionary of total areas by grid code
    
    for n in range (numRecs):
    # fill gridDict with sum of areas by grid code
        hrr = data["hrr"][n]
        # if the 2nd or later entry of a grid code, cumulative sum of area,
        # else add entry for that grid code.
        if hrr in areaDict:
            areaDict [hrr] = areaDict [hrr] + data ["ap"][n]
        else :
            areaDict [hrr] = data ["ap"][n]

    for n in range (numRecs):
    # Calculate weighted average of areas
        hrr = data["hrr"][n]
        
        data ["wt"].append (round((data ["ap"][n] / areaDict [hrr]), 3))
        
    return data


def writeCSV(data, workspace, cpcet):
    # Writes data to Pgrid.txt
    numRecs = len(data["grid"])
    
    csvFile = os.path.join(workspace, "Pgrid.txt")
    print "file name is", csvFile
    with open(csvFile, "w") as myFile:
        
        writer = csv.writer(myFile, delimiter = ",", lineterminator = "\n")
        # Header row		
        writer.writerow(["ID", "HRR_ID", "wt"])
        for n in range(numRecs):
            row = [data["cpc"][n], data["hrr"][n], data["wt"][n]]
            writer.writerow (row)
            
    myFile.close()


def fortranCall (fortSpace, outPath, place, cpcet):
    """ Runs overlay4.exe, and puts the output in the current workspace"""

    newPgrid = 'Pgrid_{}_{}.txt'.format (cpcet, place)
    newOverlay = 'Grid_overlay_{}.txt'.format (cpcet)
    pGrid = 'Pgrid.txt'
    overlayGrid = 'Pgrid_overlay.txt'
    exe = os.path.join (fortSpace, 'overlay4.exe')
    
    fromFile = [os.path.join (fortSpace, pGrid),
                os.path.join (fortSpace, overlayGrid)
                ]
    toFile = [os.path.join (outPath, newPgrid),
              os.path.join (outPath, newOverlay)
              ]
    
    
    subprocess.Popen (exe, cwd = fortSpace)
    time.sleep(20) # Without this, computer would sometimes have Pgrid.txt open,
                    # or would not recognize Pgrid_overlay.txt

    # Move results to output location and rename.
    for n in range (2):
        print 'moving ', toFile [n]
        shutil.copy (fromFile [n], toFile [n])
        time.sleep(20)
                             
    print 'have run overlay4.exe'
                   
if __name__ == '__main__':
    main ()



