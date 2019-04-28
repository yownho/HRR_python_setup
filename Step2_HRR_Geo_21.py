"""
GIS setup for Hillslope River Routing Model (HRR) Step 2

Parts:
1. Takes catchments table, streams table, Flow accumulation grid. Output is HRR setup tables, with each catchment
   grouped by Watershed IDs. Table is ordered by unique HRRID. In first table, HRRID sorted in MAX. In final table,
   HRRID is sorted on 1) WID and 2)Cumulative Area. Area is in number of grid pixels.
2. Calculate lfp length for each catchment, in km.
3. Takes HRR table, catchments shapefile projected, streams shapefile projected. Add fields to catchments (Area sqkm) and streams (Length km) and CumA Sqkm.
   Fill first two from joined fields. Cum A from variation of CumA HRR.

Hydro-Geo-Spatial Research Lab
Website: http://www.northeastern.edu/beighley/home/
By: Yuanhao Zhao
Email: zhao.yua@husky.neu.edu
"""

import arcpy, os.path
from arcpy import env
from arcpy.sa import *

from operator import itemgetter, attrgetter

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

#####************************************* Change Input Parameters As Needed ************************#####
cellSize = 0.00083333333   # Grid/pixel size of Fdir grid (get from grid properties in ArcMap)
targetWorkspace = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1000\GISworking2" # Output workspace                         
flowAcc = r"C:\Research\NASA_Decomp\Ohio_GIS_basic\faccm_ohio" # flow accumulation raster                                                                     
region = 'OH' #two letters represent simulated bas                                                    
zone = '02' #two numbers represent the model run
projection = r"C:\Research\HRR_0326\2.1\2.1\Lambert Azimuthal Eq Area N America (Flood).prj" #shapefiles need to be projected in meters
projected = 'false' #True if streams and catchments already projected in meters
#####*************************************************************************************************#####

#####**** do not change any of the below *************************************************************#####
def main (): 
    arcpy.env.workspace = targetWorkspace

    place = region + zone

    #files generated from step1, no need to modify
    streamsFC = "Streams.shp" #stream shapefile from step 1               
    maxFacc = "MaxFAcc.dbf"  #dbf file from step 1          
    catch = "Catchments.shp" #HRR catchments
    LFP = "lfpstr.shp" #LFP shapefile

    #out feature, no need to modify
    lfp_m = "LFPstr_m.shp" 
    lfpits = "lfpits.shp"
    StrDis = "lfpstrd.shp" 

    #####***** part1 *****#####

    #Check workspace type, and set output names
    desc = arcpy.Describe(targetWorkspace)
    isGDB = desc.workspaceType # FileSystem if not GDB, else type of GDB.

    if isGDB != "FileSystem":
        newTableFinal = "HRR_Table2_" + place
        newTable = "HRR_Table1_" + place
    else:
        newTableFinal = "HRR_Table2_" + place + ".dbf"
        newTable = "HRR_Table1_" + place + ".dbf"
        
    arcpy.CopyRows_management (streamsFC, newTable)
    joinTable (newTable, maxFacc)

    addFieldsTable (newTable)
    deleteFields (newTable)
    fillZeroes (newTable)

    buildChannels (newTable, 1)
    cumArea (newTable)
    assignWID (newTable)
    arcpy.Copy_management (newTable, newTableFinal)

    buildChannels (newTableFinal, 2)
    cumArea (newTableFinal)
    assignWID (newTableFinal)

    relateHRR (newTableFinal)

    arcpy.AddField_management(newTableFinal, "Error", "FLOAT")
    expression = 'float(!CumArea!*1.0 - !MAX!) / float (!CumArea!)'
    arcpy.CalculateField_management (newTableFinal, 'ERROR', expression, 'PYTHON')
    print "Error calculated"

    #####***** Part2 *****#####
    desc = arcpy.Describe(targetWorkspace)
    isGDB = desc.workspaceType # FileSystem if not GDB, else type of GDB.
    if isGDB != "FileSystem":
       hrr3  = "HRR_Table3_" + region + zone
    else:
       hrr3 = "HRR_Table3_" + region + zone + ".dbf"

    arcpy.Copy_management (newTableFinal, hrr3)
    arcpy.Intersect_analysis([LFP,catch], lfpits)

    arcpy.Dissolve_management(lfpits, StrDis, "GRIDCODE", "", "MULTI_PART", "DISSOLVE_LINES")

    print 'Pjoject to meters'
    if (str(projected) == 'false') or (projected == False):
            print "Projecting streams and catchments"
            arcpy.Project_management(StrDis, lfp_m, projection)

    #calculate the channel length, add to the HRR3 table
    print 'Calculate LFP'
    fillFieldsLFP (hrr3, lfp_m)

    #####***** Part3 *****#####
    if (str (projected) == 'false') or (projected == False):
        print "Projecting streams and catchments"
        catch, streamsFC = projectFCs (catch, streamsFC, projection, targetWorkspace)
            
    fillFields (hrr3, catch, streamsFC, region, zone)

    print 'Success'

def checkGC (table):
    """ Returns correct Grid Code field. Can be either GRIDCODE or GRID_CODE """
    fields = arcpy.ListFields (table)
    #Get correct name for gridcode field
    for f in fields:
        if f.name.upper() == "GRID_CODE":
            return "GRID_CODE"
        elif f.name.upper() == "GRIDCODE":
            return "GRIDCODE"

def joinTable (streamstable, table):
    """Joins streams shapefile to MaxFAcc on Grid Code, for max FAcc by stream/catchment."""
    fields = ['COUNT', 'MAX']
    gcTable = checkGC (table) # Get correct grid code name
    gcStream = checkGC (streamstable)
    arcpy.JoinField_management(streamstable, gcStream, table, gcTable, fields)

def addFieldsTable (table):
    """Add new fields"""
    #HRR_ID is the ID in order of sort from low MAX to high MAX
    # WID is watershed ID
    # Down_ID is the next grid code downstream
    # NumUp is the number of watersheds directly upstream
    # Up1, Up2, Up3 are grid codes of watersheds directly upstream
    # CumArea is the cumulative area of the upstream watersheds.
    fieldNames = [["HRR_ID", "LONG"], ["WID", "LONG"], ["Down_ID","LONG"], ["NumUp","SHORT"], ["Up1ID","LONG"],
                  ["Up2ID", "LONG"], ["Up3ID", "LONG"], ["Up4ID", "LONG"], ["CumArea", "FLOAT"]
                 ]
    for f in fieldNames:
        arcpy.AddField_management (table, f[0], f[1])

def deleteFields (table):
    """ Delete unneeded fields"""
    fieldNames = ['AREA', 'GRID_COD_1', 'SHAPE_LENG']
    for f in fieldNames:
        arcpy.DeleteField_management (table, f)

def fillZeroes (table):
    """ Fill zeroes into columns where zero is the default value """
    fieldNames = ["NumUp", "Up1ID", "Up2ID", "Up3ID", "Up4ID", "WID"]
    for f in fieldNames:
        arcpy.CalculateField_management (table, f, 0)

def buildChannels (table, n):
    #Build channels- associate from-to nodes with Grid Codes up and downstream,
    #associate watershed values."""

    numRec = int (arcpy.GetCount_management (table).getOutput (0))
    ##NumRec needs to be at least highest number found in from/to, because to and from nodes labels can be > number of records.
    numRec += numRec*10

    gcNewTable = checkGC (table)

    toFrom =[0 for x in range (numRec)] #List where record number n is the from value
    fromTo = [0 for x in range (numRec)] #List where record number n is the to value
    sink = [0 for x in range (numRec)] #List to hold values for all records that are sinks or outlets.
    downID = [-1 for x in range (numRec)]
    numUp = [0 for x in range (numRec)]
    up1 = [0 for x in range (numRec)]
    up2 = [0 for x in range (numRec)]
    up3 = [0 for x in range (numRec)]
    up4 = [0 for x in range (numRec)]
    hrr = [0 for x in range (numRec)]
    dict = {} #Will contain {grCode:[0 downID, 1 numUp, 2 up1, 3 up2, 4 up3, 5 sink, 6 hrr]}

    print 'new table grid code is', gcNewTable
    fields = [gcNewTable, "MAX", "FROM_NODE", "TO_NODE", "HRR_ID", "DOWN_ID", "NUMUP", \
              "Up1ID", "Up2ID", "Up3ID", "Up4ID", 'WID', 'CumArea']

    with arcpy.da.SearchCursor (table, fields) as cursor:
        # Stores all records referenced to grCode in a list of dictionaries.
        for row in cursor:
            grCode = row[0]
            dict[grCode] =[0 for x in range (5)]

        #Sorts cursor by MAX
        cursor.reset ()

        #Fills toFrom
        for row in cursor:
            fromID = int (row[2]) #From_Node
            grCode = row[0]
            # index fromID = grCode
            toFrom [fromID] = grCode #c #ToFrom goes current from node to current grid code.

        cursor.reset ()

        #Fills fromTo

        m = 1 #sink num
        # Sort records
        if n == 1:
            cursor = sorted (cursor, key = itemgetter (1)) # Sort on MAX
        else:
            # cursor = sorted (cursor, key = itemgetter (10,11)) #sort on WID, then CumArea
            cursor = sorted (cursor, key = itemgetter (11,12)) #sort on WID, then CumArea

        for row in cursor:
            grCode = row[0]
            toID = int (row[3]) #To_Node

            k = toFrom [toID] #k = grid code at the To_Node
            if k == 0:
                fromTo [grCode] = 0 #There is no down unit
                sink [grCode] = m #This is a sink or terminus.
                m +=1
            else:
                fromTo [grCode] = k #Row ID for the down unit (dpfaf)
                sink [grCode] = 0 #This is not a sink or terminus.

        #Fills column downValue

    # Sort records
        for row in cursor:
            grCode = row[0]
            downID [grCode] = fromTo [grCode] #Assigns DownID

        if n == 1:
            print "n = 1, sort on MAX"
            cursor = sorted (cursor, key = itemgetter (1)) # Sort on MAX
        else:
            print "n != 1, sort on WID & CumArea"
            #cursor = sorted (cursor, key = itemgetter (10,11)) #sort on WID, then CumArea
            cursor = sorted (cursor, key = itemgetter (11,12)) #sort on WID, then CumArea
        #Fills upID values. Next two loops are where data MUST be sorted by area (MAX)
        c = 1
        for row in cursor:
            grCode = row[0]
            dstr = downID [grCode]
            hrr[grCode] = c
            if up1[dstr] == 0: #If up1 at the next downstream is 0
                up1 [dstr] = grCode #upID1 at row num downID = current row (c)
                numUp [dstr] = 1
            elif up1[dstr] > 0:
                if up2 [dstr] == 0:
                    up2 [dstr] = grCode
                    numUp [dstr] = 2
                elif up3 [dstr] == 0:
                    up3 [dstr] = grCode
                    numUp [dstr]= 3
                elif up4 [dstr] == 0:
                    up4 [dstr] = grCode
                    numUp [dstr]= 4
                elif dstr > 0:
                    numUp = 9999
                    print (str (dstr) + "has more than 4 watersheds flowing into it")
            c +=1

        # Sort records
        # fills dictionary with values for use in update cursor.
        for row in cursor:
            grCode = row[0]
            dict[grCode] = [downID[grCode], numUp[grCode], up1[grCode], up2[grCode],\
                            up3[grCode], up4[grCode], sink[grCode], hrr[grCode]]
        print "Channels determined"


    #Update rows
    with arcpy.da.UpdateCursor (table, fields) as cursor:
        for row in cursor:
            grCode = row[0]
            row [4] = dict [grCode][7]
            row [5] = dict [grCode][0]
            row [6] = dict [grCode][1]
            row [7] = dict [grCode][2]
            row [8] = dict [grCode][3]
            row [9] = dict [grCode][4]
            row [10] = dict [grCode][5]
            row [11] = dict [grCode][6]
            cursor.updateRow (row)
    print "Channels Built"
    if cursor:
        del cursor

def cumArea (table):
    """ Calculates cumulative area of watershed at current catchment for each catchment in a watershed"""
    gcNewTable = checkGC (table)
    fields = [gcNewTable, "COUNT", "UP1ID", "UP2ID", "UP3ID", "UP4ID", "CumArea", "HRR_ID"]
    numRec = int (arcpy.GetCount_management (table).getOutput (0))
    numRec += numRec*10
    #numRec += numRec/3

    countL = [0 for x in range (numRec)] #List of all areas in Count field
    sumArea = [0 for x in range (numRec)]

    with arcpy.da.SearchCursor (table, fields) as cursor:
        # Makes a list of all areas in order of Grid Code
        for row in cursor:
            id = row[0]
            countL [id] = row[1]
        cursor.reset()
        #Sort on HRR_ID

        cursor = sorted (cursor, key = lambda row:row[7])
        # get all cumulative areas
        for row in cursor:
            # sumArea = area in count field + area in each Up field.
            id = row [0]
            sumArea[id] = countL [row[0]] + countL [row[2]]  + countL [row[3]] \
                          + countL [row[4]] + countL [row[5]]
            countL[id] = sumArea [id]

    print "Cumulative area determined"

    with arcpy.da.UpdateCursor (table, fields) as cursor:
        for row in cursor:
            id = row[0]
            row[6] = sumArea [id]
            cursor.updateRow (row)

    print "Cumulative Area entered"

    if cursor:
        del cursor


def assignWID (table):
    """ Assigns watershed ID to each catchment"""
    gcNewTable = checkGC (table)
    fields = [gcNewTable,  "UP1ID", "UP2ID", "UP3ID", "UP4ID", "WID", "HRR_ID"]
    numRec = int (arcpy.GetCount_management (table).getOutput (0))
    numRec += numRec*10

    wid = [0 for x in range (numRec)]

    with arcpy.da.SearchCursor (table, fields) as cursor:

        # Makes a list of all areas in order of Grid Code
        for row in cursor:
            id = row[0]
            wid [id] = row[5]

        cursor.reset()

        #Sort on HRR_ID
        cursor = sorted (cursor, key = lambda row:row[6], reverse = True)

        for row in cursor:
            # fills list with appropriate watersheds.
            id = row[0]
            up1 = row[1]
            up2 = row[2]
            up3 = row[3]
            up4 = row[4]

            if up1 > 0:
                wid[up1] = wid[id]
            if up2 > 0:
                wid[up2] = wid[id]
            if up3 > 0:
                wid[up3] = wid[id]
            if up4 > 0:
                wid[up4] = wid[id]

        print "WID determined"

    #updates WID column in table
    with arcpy.da.UpdateCursor (table, fields) as cursor:
        for row in cursor:
            id = row[0]
            row [5] = wid[id]
            cursor.updateRow (row)

        print "WID entered"

    if cursor:
        del cursor

def relateHRR (table):
    """ Relates up and down IDs on HRRID instead of Grid Code"""
    gcNewTable = checkGC (table) # Get correct grid code name
    fields = [ gcNewTable,  "HRR_ID", "UP1ID", "UP2ID", "UP3ID", "UP4ID", "DOWN_ID"]

    with arcpy.da.SearchCursor (table, fields) as cursor:
        allCodes = {} # dictionary relating grid codes to HRRID
        for row in cursor:
            # {grid code: hrr}
            allCodes[row[0]] = row[1]

        cursor.reset()
        allCodes[0] = 0 # Takes care of entries with no up or down ID.

    # update table replaceing grid code with HRRID in up and down IDs
    with arcpy.da.UpdateCursor (table, fields) as cursor:
        for row in cursor:
            # up1 = allCodes[grid code from up1 column]= HRR at that column
            row[2] = allCodes[row[2]]#up1
            row[3] = allCodes[row[3]]#up2
            row[4] = allCodes[row[4]]#up3
            row[5] = allCodes[row[5]]#up4
            row[6] = allCodes[row[6]]#down
            cursor.updateRow (row)


#Adds fields to feature class
def addFields (fc, fieldList):
    """ Adds fields in a list of fields"""
    for field in fieldList:
        print "Adding field " + field + " to " + fc
        arcpy.AddField_management (fc, field, "FLOAT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")


def fillFieldsLFP (hrr3, stream):   
    fieldsTable = ["Lc_LFP_km"]
    addFields (stream, fieldsTable)    #channel length by LFP
    
    #Update new fields
    print "Updating simple fields"
    arcpy.CalculateField_management (stream, "Lc_LFP_km", "!SHAPE.LENGTH!/1000", "PYTHON")
    
    newGC = checkGC (hrr3)
    strGC = checkGC (stream)
    
    arcpy.JoinField_management (hrr3, newGC, stream, strGC, "Lc_LFP_km")


def prjNames (workspace):
    """ Check workspace type, and set output names """
    desc = arcpy.Describe(workspace) 
    isGDB = desc.workspaceType # FileSystem if not GDB, else type of GDB.
    m = isGDB, 'is the workspace type.'
    arcpy.AddMessage (m)
    if isGDB != "FileSystem":
        catch_m = 'catchments_m'
        str_m = 'streams_m'
    else:
        catch_m = 'catchments_m.shp'
        str_m = 'streams_m.shp'
    print arcpy.GetMessages ()
    return catch_m, str_m

def projectFCs (catch, stream, prj, workspace):
    """ Projects feature classes and returns names """
    c_m, s_m = prjNames (workspace)
    m = c_m, s_m, "Projecting catchments and streams, in ProjectFCs"
   
    arcpy.Project_management(catch, c_m, prj)
    arcpy.Project_management(stream, s_m, prj)
    return c_m, s_m

def cumFields (table, count, cumulative ):
   """ Calculates cumulative area of each catchment and all catchments upstream in sqkm. """
   fields = [count, "UP1ID", "UP2ID", "UP3ID", "UP4ID", cumulative, "HRR_ID"]

   countArea = [0] #List of all areas in Count field. HRR IDs start at 1, so 0 is a filler. If no HRRID listed, area is 0.
   sumArea = {} #dictionart of cumulative sum of all areas.

   with arcpy.da.SearchCursor (table, fields) as cursor:

       #Sort on HRR_ID
       cursor = sorted (cursor, key = lambda row:row[6])

       # Makes a list of all areas at list index HRRID
       for row in cursor:
           countArea.append (row[0])

       # get all cumulative areas
       for row in cursor:
           # sumArea = area in count field + area in each Up field.
           id = row [6]
           # sumArea  = area at currentHRRID + area in HRRID in up1 + area in HRRID in up2  + Aaea in HRRID in up3 + Aaea in HRRID in up4
           sumArea[id] = countArea [row[6]] + countArea [row[1]] + countArea [row[2]] + countArea [row[3]] + countArea [row[4]]
           countArea[id] = sumArea [id] # current cumulative area updated.

   if cursor:
       del cursor

   print "Cumulative determined"
   with arcpy.da.UpdateCursor (table, fields) as cursor:
       for row in cursor:
           id = row[6]
           # cumulative area at current HRRID
           row[5] = sumArea[id]
           cursor.updateRow (row)

   print "Cumulative entered"

def fillFields (hrr3, catch, stream, region, zone):
   """ Fills in length, area, and cumulative length and area fields."""

   #Add fields to both tables
   fieldsTable = ["CumA_sqkm","CumL_km","cumLfp_km"] #added by YZ
   addFields (hrr3, fieldsTable)
   addFields (catch, ["A_sqkm"])
   addFields (stream, ["L_km"])
   addFields (hrr3, ["Lp_km"])

   #Update new fields
   print "Updating simple fields"

   arcpy.CalculateField_management (stream, "L_km", "!SHAPE.LENGTH! / 1000", "PYTHON")   #GIS channel length
   arcpy.CalculateField_management (catch, "A_sqkm", "!SHAPE.AREA@SQUAREKILOMETERS!", "PYTHON")

   newGC = checkGC (hrr3)
   strGC = checkGC (stream)
   catchGC = checkGC (catch)

   arcpy.JoinField_management (hrr3, newGC, stream, strGC, "L_km")
   arcpy.JoinField_management (hrr3, newGC, catch, catchGC, "A_sqkm" )

   #assume min length of change as 100 m
   expression = "getClass(float(!Lc_LFP_km!),float(!A_sqkm!),0.1)"
   #expression = "getClass(float(!Lc_LFP_km!),float(!A_sqkm!),cellSize)" 

   codeblock = """def getClass(lpkm,asqkm,dx):
     if lpkm < dx:
        return asqkm/dx/2
     elif lpkm >= dx:
        return asqkm/lpkm/2"""
    
   arcpy.CalculateField_management (hrr3, "Lp_km", expression, "PYTHON", codeblock)  #EB

   arcpy.JoinField_management (hrr3, newGC, catch, catchGC, "Lp_km" )

   arcpy.DeleteField_management (catch, "A_sqkm")
   arcpy.DeleteField_management (catch, "Lp_km")
   arcpy.DeleteField_management (stream, "L_km")
   
   print 'updating Cum fields'
   cumFields (hrr3, "A_sqkm", "CumA_sqkm")
   cumFields (hrr3, "L_km", "CumL_km")
   cumFields (hrr3, "Lc_LFP_km", "cumLfp_km")

#if __name__ == "__main__":
#        main ();
main ()