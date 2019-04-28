"""
GIS setup for Hillslope River Routing Model (HRR) Step 5

Objectives:
1. Take HRR3 table, Returns 3 tab delimited .txt files for HRR model to run: channels.txt, planes.txt. output_calibration.txt

Hydro-Geo-Spatial Research Lab
Website: http://www.northeastern.edu/beighley/home/
By: Yuanhao Zhao
Email: zhao.yua@husky.neu.edu
"""

import arcpy, os, os.path
from arcpy import env
from arcpy.sa import *

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

#####***** Input parameters chagne as needed*****#####
outputPath = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1000\HRRtxt2"  #Path with HRR table (see next line) and location to write text files
hrr = r"C:\Research\Scale_RC_aveVel_0316\HRRSetup\1000\HRRtxt2\HRR_Table3_OH02.dbf"  #Final HRR table with all slopes, lengths and areas 

### change lines 140 if width=alph(Area)^beta is known, width (m) & Area (km2)
# dict ['width_ch'][0][id] = 1.956 * ((dict['cumA_km2'][0][id]) ** 0.413)
### change lines 141 if qref=alph(Area)^beta is known, qref (cms) & Area (km2)
# dict ['q_r'][0][id]= 0.01 * 0.089 * ((dict['cumA_km2'][0][id]) ** 0.958) #10% of Qbank
###******************************#####

def main ():  
	
    arcpy.env.workspace = outputPath
	
    print ' running hrr to text on', hrr

    # Fill lists with appropriate data
    count = sum((1 for row in arcpy.da.SearchCursor(hrr, ['HRR_ID'])))
    numRec = count + 1  

    gridCode = checkGC (hrr)
    
    dict = fillLists (hrr, numRec)
    dict = removeFirst (dict)

    #Write to files
    makeFiles (outputPath, dict, numRec)
    
    print 'Success!'  
        
def checkGC (table):
    """ Returns correct Grid Code field. Can be either GRIDCODE or GRID_CODE """
    fields = arcpy.ListFields (table)
    for f in fields:
        if "GRID_CODE" in f.name.upper ():
            return "GRID_CODE"
        elif "GRIDCODE" in f.name.upper ():
            return "GRIDCODE"    


#Recalculates null values to -999  
def nullCheck (dict):
    """Recalculates slope from null to -999 where catchment has no null value in raster."""
    for id in dict['hrrID'][0]:
        #slope
        if not isinstance (dict['slope_ch'][0][id], float):
            dict['slope_ch'][0][id] = -999
        if not isinstance (dict['slope_p1'][0][id], float):
            dict['slope_p1'][0][id] = -999

        if not isinstance (dict['kSat'][0][id], float):
            dict['kSat'][0][id] = -999
        if not isinstance (dict['effPor'][0][id], float):
            dict['effPor'][0][id] = -999
        if not isinstance (dict['depthp'][0][id], float):
            dict['depthp'][0][id] = -999   

        if not isinstance (dict['lcp'][0][id], int):
            dict['lcp'][0][id] = -999   
               
    return dict

        
def fillLists (hrrTable, numRec):
    """ Creates data structure to hold final output."""
    # Data fields needed for final output, or needed to calculate final output.
    # Fills with default of -999 so it is obvious when a record does not exist for
    # a particular grid code.

    dict = {'gridCode': [[0 for x in range (numRec*10)], 1, 'all'], #arc
        'hrrID': [[0 for x in range (numRec)], 0, 'all'], #arc
            
        'length_p1': [[-999 for x in range (numRec)], 2, 'planes'], #calc
        'slope_p1': [[0.1 for x in range (numRec)], 3, 'planes'], #arc, calc
        'n_surface': [[0.8 for x in range (numRec)], 4, 'planes'], #constant
        'kSat': [[-999 for x in range (numRec)], 5, 'planes'], #arc
        'effPor': [[-999 for x in range (numRec)], 6, 'planes'], #arc
        'depthp': [[3.2 for x in range (numRec)], 7, 'planes'], #arc
        'lcp': [[-999 for x in range (numRec)], 8, 'planes'], #calc
            
        'downID': [[-999 for x in range (numRec)], 2, 'channels'], #arc
        'numUp': [[-999 for x in range (numRec)], 3, 'channels'], #arc
        'up1': [[-999 for x in range (numRec)], 4, 'channels'], #arc
        'up2': [[-999 for x in range (numRec)], 5, 'channels'], #arc
        'up3': [[-999 for x in range (numRec)], 6, 'channels'], #arc
        'up4': [[-999 for x in range (numRec)], 7, 'channels'], #arc
        'a_km2': [[999 for x in range (numRec)], 8, 'channels'], #arc
        'cumA_km2': [[999 for x in range (numRec)], 9, 'channels'], #arc
        'len_ch': [[-999 for x in range (numRec)], 10, 'channels'], #arc
        'slope_ch': [[0.001 for x in range (numRec)], 11, 'channels'], #constant
        'n': [[0.035 for x in range (numRec)], 12, 'channels'], #constant
        'width_ch': [[-999 for x in range (numRec)], 13, 'channels'], #calc
        'q_r': [[-999 for x in range (numRec)], 14, 'channels'], #calc            
        'guageA': [[-999 for x in range (numRec)], 2, 'output'] } #calc
        
    # fill values directly from Arc
    dict = fillArcLists (hrrTable, dict)

  # print dict
    
    # Fill lists with calculated values

    dict = nullCheck (dict)
    
    dict = calcChannelsLists (dict)
    
    return dict


def calcChannelsLists (dict): 
    """Calculates values for fields with calculated values. """
    hrrID = dict['hrrID'][0]
    for id in hrrID:
        dict['length_p1'][0][id] = dict['length_p1'][0][id] * 1000 #(m)
        dict['len_ch'][0][id] = dict['len_ch'][0][id] * 1000 #(m)
        dict['slope_p1'][0][id] =  dict['slope_p1'][0][id] / 100 #(percent)
        dict['slope_ch'][0][id] = dict['slope_ch'][0][id] / 100 #(percent)
        dict['kSat'][0][id] = dict['kSat'][0][id] / 24 # ksat, cm/day to cm/hour

        # from Beighley and Gummadi (2011)
        dict ['width_ch'][0][id] = 1.956 * ((dict['cumA_km2'][0][id]) ** 0.413)
        dict ['q_r'][0][id]= 0.01 * 0.089 * ((dict['cumA_km2'][0][id]) ** 0.958) #10% of Qbank
        
        dict ['guageA'][0][id] = int (dict['cumA_km2'][0][id])
    return dict

def fillArcLists (hrrTable, dict):
    """ Takes data from arc table and puts it into a list in memory."""
    # Create lists of correct length
    #list of fields in HRR3
    gridCode = checkGC (hrrTable)
    arcFields = [gridCode, 'HRR_ID', 'DOWN_ID', 'NUMUP', 'UP1ID',
                 'UP2ID', 'UP3ID', 'UP4ID', 'CUMA_SQKM', 'A_SQKM',
                 'LC_LFP_KM','LP_KM','KSAT','EFFPOR',
                 'SLOPE_STR','SLOPE_CAT','DEPTH', 'LC'
                 ]
        
    # list of lists
    arcLists =[dict['gridCode'][0], #1
		dict['hrrID'][0], #2
		dict['downID'][0], #3
		dict['numUp'][0], #4
                dict['up1'][0], #5
		dict['up2'][0], #6
		dict['up3'][0], #7
		dict['up4'][0], #8
		dict['cumA_km2'][0], #9
                dict['a_km2'][0], #10
		dict['len_ch'][0], #11
		dict['length_p1'][0], #12
		dict['kSat'][0], #13
                dict['effPor'][0], #14
		dict['slope_ch'][0],#15
                dict['slope_p1'][0], #16
		dict['depthp'][0], #17
		dict['lcp'][0], #18
		#dict['n_surface'][0] #19
               ]
               
    with arcpy.da.SearchCursor (hrrTable, arcFields) as cursor:

        for row in cursor:
            hrrINT= row [1]
            # Fill all lists, with HRRINT as index
            for i in range(len(arcLists)):
               arcLists[i][hrrINT] = row [i]
				
    dict['gridCode'][0] = arcLists [0]
    dict['hrrID'][0] = arcLists [1]
    dict['downID'][0] = arcLists [2]
    dict['numUp'][0] = arcLists [3]
    dict['up1'][0] = arcLists [4]
    dict['up2'][0] = arcLists [5]
    dict['up3'][0] = arcLists [6]
    dict['up4'][0] = arcLists [7]  
    dict['cumA_km2'][0] = arcLists [8]
    dict['a_km2'][0] = arcLists [9]
    dict['len_ch'][0] = arcLists [10]
    dict['length_p1'][0] = arcLists [11]
    dict['kSat'][0] = arcLists [12]
    dict['effPor'][0] = arcLists [13]
    dict['slope_ch'][0] = arcLists [14]
    dict['slope_p1'][0] = arcLists [15]
    dict['depthp'][0] = arcLists [16]
    dict['lcp'][0] = arcLists [17]
    #dict['n_surface'][0] = arcLists [18]

    return dict

 
def makeFiles (outPath, dict, numRec):
    """Creates and opens channels, planes, and ouput_calibration .txt files."""
    channels = os.path.join (outPath, 'channels.txt')
    planes = os.path.join (outPath, 'planes.txt')
    output = os.path.join (outPath, 'output_calibration.txt')
    input = os.path.join (outPath, 'input_num.txt')
    
    # Put data into lists for files
    chList, plList, outList = toLists (dict)

    chList = sorted (chList, key = lambda ch:ch[1])
    plList = sorted (plList, key = lambda pl:pl[1])
    outList = sorted (outList, key = lambda ou:ou[1])

    # make files     
    with open (planes, 'w') as handle:
        wrFile (plList, handle)
    with open (channels, 'w') as handle:
        wrFile (chList, handle)
    with open (output, 'w') as handle:
        wrFile2 (outList, numRec, handle)
    with open (input, 'w') as handle:
        wrInput (numRec, handle)

  
def wrFile (dataLists, handle):
    """Writes data to open file"""
    n = 0
    #Iterate number of records in HRRID
    #
    hrrID = dataLists [0][0]
    print len (dataLists)
    while n < len (hrrID):
        #Iterate fields for current file
        i = 0
        while i < (len (dataLists)):
            handle.write (str (dataLists[i][0][n]))

            if i == len (dataLists) - 1:
                handle.write ('\n')
            else:
                handle.write ('\t')
            i += 1
        n += 1 

def wrFile2 (dataLists, numRec, handle):
    """Writes data to open file"""
    n = 0
    #Iterate number of records in HRRID

    hrrID = dataLists [0][0]
    print len (dataLists)
    handle.write (str (numRec-1)+ '\n')
    while n < len (hrrID):
        #Iterate fields for current file
        i = 0
        while i < (len (dataLists)):
            handle.write (str (dataLists[i][0][n]))

            if i == len (dataLists) - 1:
                handle.write ('\n')
            else:
                handle.write ('\t')
            i += 1
        n += 1 
         
def toLists (dict):
    """Creates list of data to be written to files from dictionary."""
    ch = []
    pl = []
    out = []
    all = []
    for k, v in dict.iteritems ():
        if v[2] == 'planes':
            pl.append (v)
        
        elif v[2] == 'channels':
            ch.append (v)
        elif v[2] == 'output':
            out.append (v)
        else:
            all.append (v)
    ch = all + ch
    pl = all + pl
    out = all + out
    return ch, pl, out

# Removes first item of each list, where HRRID = 0. These are not valid datapoints  
def removeFirst (dict):
    for k, v in dict.iteritems():
        v[0] = v[0][1:]
    return dict

# Writes fill of inputs used to create data.
def wrInput (numRec, handle):
    handle.write (str (numRec-1))    
    
main ()
