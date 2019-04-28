# Step 7 --> make the P and ET bin files for each model unit

##this is not python
##
##just telling your to run makebins code in folder
##
##change input_P_ET.txt
##line 1: number pfaf units
##line 2: number of time steps, hourly
##line 4: start year
##Lines 5-6: leave as zero unless working on future climate model output
##
##
##Modify filenames/locations in main_P_ET_v1_GCM.f90
##fnameTRMM(1:44) = 'C:\Global_Data\TRMM\GnuWin32\bin\3B42_daily.'
##fnameRRET(1:65)='C:\Research\Amazon\AM_AG_GIS\HRR_g\makebins\PTET_GRID(Amazon).txt'
##
##copy overlay files to the makebins folder
##Grid_overlay_TRMM.txt
##Grid_overlay_RRET25Congo.txt
##
##re-make the exe file
##run the exe file
