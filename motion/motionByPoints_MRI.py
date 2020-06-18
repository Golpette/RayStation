"""
Target motion based on bony landmarks

Assume ROI is made of contours (i.e. not indices & vertices or 3d mesh)
Assume ROI contours are defined axially

User defines a base MR or CT scan and a list of other scans to compare it to

### FOR ZING TO RUN ###
to run type:
    from rmhTools.roiTools import motionByPoints_MRI
    motionByPoints_MRI.main()

"""

#TODO: print out sup/inf changes
#TODO: use a single ref point?
#####:
#TODO: automatically select appropriate slice thickness for each image pair?
#          (either largest, or that of the weekly CBCT?)
#TODO: GUI for easier use by clinicians
#TODO: user to specify output destination and filename
#TODO: make script safe for both Python 2 and 3
#TODO:


import connect as rsl
import os




############ For Zing to alter #############################################
############################################################################
# The names below are case sensitive and must match exactly

# This is the exam to which all others will be compared
BASE_EXAMINATION = "Plan CT"   
   
# These are the exams that will be compared to BASE_EXAMINATION. Separate entries with a comma.
EXAMINATION_LIST = [ 'Wk0 MR3D' ]  

# If your images contain different slice thicknesses, for the most accurace analysis
# you should use the largest value (the script will always compare the *closest* slice, hence
# using a smaller value will result in multiple slices in 1 scan being compared to the same slice in
# the other scan        
SLICE_INTERVAL = 0.2           

# List here all the ROIs you wish to include in the analysis
DESIRED_ROIS = [ 'CTV_Clin, CTV_SmallVol' ]            


# Originally SP was reference point for z-coord
REF_POINT_SP = "Ref Point SP"
# RFH was used a reference for x and y coordinates
REF_POINT_RFH = "Ref Point RFH"


# Directory into which profile data will be saved
dataPath = os.path.join(r'\\rtp-bridge2-rt.ad.rmh.nhs.uk\IntoSecure\ICR',os.environ['USERNAME'],'motionByPoints_MRI_data')

#############################################################################
#############################################################################



EXPORT_FILE_PREFIX = ''
stt = ""
for e in EXAMINATION_LIST:
    stt = stt+e+","
stt = stt.strip(",")
EXPORT_FILE_SUFFIX = "_base="+BASE_EXAMINATION+"_vs_"+stt






# --------------- #

def getRefPointCoordinates(sSet, pointName):
    """Returns dictionary of x,y,z coords of a POI"""
    pt = sSet.PoiGeometries[pointName].Point
    return {'x':pt.x, 'y':pt.y, 'z':pt.z}
    
# --------------- #



def findContoursListNearPos(roiGeom, zPos):
    """
    Return a list of ROI contours closest to the requested z position   
    (we can have multiple contours per slice)
    """
    contourZPos = [con[0].z for con in roiGeom.PrimaryShape.Contours]
    
    minZDiff = 9E99
    minInd = -1
    ### multiple contours on same slice
    actualZ = 9E99
    ###
    for cc,cZ in enumerate(contourZPos): 
        zDiff = abs(cZ-zPos)
        
        if zDiff < minZDiff:
            minZDiff = zDiff
            minInd = cc
            actualZ = cZ        
    
    # check minInd isn't -1
    if minInd == -1 or actualZ == 9E99:
        print("ERROR: minInd not set in findContourNearPos")
    
    # list all contours with this 
    list_conts = []
    for con in roiGeom.PrimaryShape.Contours:
        abs_diff = abs(con[0].z - actualZ)
        if( abs_diff <  0.001  ):   ## catch rounding errors in RayStation.      
            list_conts.append( con )    
        
    return list_conts
    
# --------------- #




def findSliceLimits(roiGeom, examName):
    '''
    Get max and min Z values for given ROI; return (min, max)
    '''
    
    contourZPos = [con[0].z for con in roiGeom.PrimaryShape.Contours]
    minZ = 9E99;  maxZ=-9E99
    for z in contourZPos:
        if z < minZ:
            minZ = z
        if z > maxZ:
            maxZ = z
     
    return (minZ, maxZ)

# --------------- #



def findExtremePoints(contour_list, refX, refY, refZ):
    """
    Find coordinates of contour points at most extreme right-left and ant-post positions
      ** with respect to reference coords **
    NOTE: There may be multiple contours on a given slice of the image
    """
    minX=9E99; minY=9E99; minX_ind=-1; minY_ind=-1
    maxX=-9E99; maxY=-9E99; maxX_ind=-1; maxY_ind=-1
    
    # To store which contour actually contains each extreme value since
    # there can be multiple contours per slice
    cminX = 999; cmaxX=-999  
    cminY = 999; cmaxY=-999
    
    for (c,contour) in enumerate(contour_list):
    
        for (indx,pt) in enumerate(contour):
        
            if pt.x < minX:
                minX = pt.x
                minX_ind = indx
                cminX = c           # need this so we actually take extreme value from correct contour
            if pt.y < minY:
                minY = pt.y
                minY_ind = indx
                cminY = c
            if pt.x > maxX:
                maxX = pt.x
                maxX_ind = indx
                cmaxX = c
            if pt.y > maxY:
                maxY = pt.y
                maxY_ind = indx   
                cmaxY = c
              
        if maxX_ind==-1 or minX_ind==-1 or maxY_ind==-1 or minY_ind==-1:
            print("Index has not been set in findExtremePoints()")
        
        
        extremes = {'R.x': contour_list[cminX][minX_ind].x-refX , 'R.y':contour_list[cminX][minX_ind].y-refY, 'R.z':contour_list[cminX][minX_ind].z-refZ,
            'L.x':contour_list[cmaxX][maxX_ind].x-refX , 'L.y':contour_list[cmaxX][maxX_ind].y-refY, 'L.z':contour_list[cmaxX][maxX_ind].z-refZ,
            'A.x':contour_list[cminY][minY_ind].x-refX , 'A.y':contour_list[cminY][minY_ind].y-refY, 'A.z':contour_list[cminY][minY_ind].z-refZ,
            'P.x':contour_list[cmaxY][maxY_ind].x-refX , 'P.y':contour_list[cmaxY][maxY_ind].y-refY, 'P.z':contour_list[cmaxY][maxY_ind].z-refZ
            }            
        
        
    return extremes

# --------------- #



def makePointAtCoords(case, exam, coords, pointName, pointColor='Red'):
    """
    Create a point if it doesn't exist else set coordinates
    N.B. coords must be a python dictionary
    """
    if pointName not in [pt.Name for pt in case.PatientModel.PointsOfInterest]:
        case.PatientModel.CreatePoi(Examination=exam, Point=coords,
                        Volume=0.0, Name=pointName, Color=pointColor,
                        Type='Marker')
    else:
        case.PatientModel.StructureSets[exam.Name].PoiGeometries[pointName].Point = coords

# --------------- #



def getDesiredROIs(case, desired_rois):
    """
    Return list of desired ROIs (only ROIS that exist in patient)
    """
    desired_lower = [ name.lower() for name in desired_rois ]  
    return [ roi.Name for roi in case.PatientModel.RegionsOfInterest if roi.Name.lower() in desired_lower ]

# --------------- #



def checkAllContoursPresent(case, exam_list, roi_list):
    """
    Check that all ROIS have an actual PrimaryShapy and Contour in each exam; print warning if not
    """    
    for roi in roi_list:
        for exam in exam_list:
        
            roi_geom = case.PatientModel.StructureSets[exam.Name].RoiGeometries[roi]
            
            try:
                ps = roi_geom.PrimaryShape
            except:
                print("---> WARNING: No ROI for {} in {} ".format(roi, exam.Name) )  
                           
            try:
                pp = roi_geom.PrimaryShape.Contours
            except:
                print("---> WARNING: No contour for {} in {}".format(roi,exam.Name) ) 
                
# --------------- # 








def main():


    patient = rsl.get_current('Patient')
    case = rsl.get_current('Case')
    
    try:
        os.makedirs(dataPath)
    except:
        pass
    
     
    ####filename = os.path.join(dataPath,'%s%s%s%s.csv' % (EXPORT_FILE_PREFIX,patient.PatientID,"_base=",BASE_EXAMINATION))
    filename = os.path.join(dataPath,'%s%s%s.csv' % (EXPORT_FILE_PREFIX,patient.PatientID,EXPORT_FILE_SUFFIX))

    # separate file for sup-inf motion
    filename_supinf = os.path.join(dataPath,'%s%s%s_SUPINF.csv' % (EXPORT_FILE_PREFIX,patient.PatientID,EXPORT_FILE_SUFFIX))

    
    # Get relevant ROIs
    all_roi_names = getDesiredROIs(case, DESIRED_ROIS)
    
    
    if len( all_roi_names ) == 0:
        print("---> WARNING: None of the desired ROIs are present!")
    print("ROI names found: {}".format(all_roi_names) )

    
    # Get all exam names
    all_exams_unordered = []
    try:
        for ex in EXAMINATION_LIST:
            all_exams_unordered.append(  case.Examinations[ ex ]  )
    except:
        print("ERROR -- Examination specified in EXAMINATION_LIST not found")
    
    
    print("Base image = {}".format(BASE_EXAMINATION)  )
    print("Images for comparison = {}".format([exam.Name for exam in all_exams_unordered]) )   
    
    

    # Have to put base exam at front of list
    all_exams = [ case.Examinations[BASE_EXAMINATION] ] + all_exams_unordered
    
    # Check that all ROIs that exist
    checkAllContoursPresent(case, all_exams, all_roi_names)

    # List of just names of exams
    exam_names = [ ex.Name for ex in all_exams ]
    

    
    # Make the .csv file header
    with open(filename, 'w') as fp:
        fp.write('roi,exam,z-RefZ,R.x,L.x,P.y,A.y\n')

    # I am assuming that the largest z value is always the "sup", and min is "inf"
    with open(filename_supinf, 'w') as fp:
        fp.write('roi,exam,S.z,I.z\n')
    
        
    strings_to_print = []
    supinf_to_print = []
    
    
    for roi_name in all_roi_names:
        
        ## STORE ALL DATA FROM PLANNING CT AS REFERENCE.
        BASE_SCAN = []   
        BASE_SCAN_SUPINF = []
        

        for exam in all_exams:
            
            ## Check that both PrimaryShape and Contour exists: 
            roi_geom = case.PatientModel.StructureSets[exam.Name].RoiGeometries[roi_name]
            
            if hasattr(roi_geom, "PrimaryShape"):
                primshape = roi_geom.PrimaryShape  
                
                if hasattr( primshape, "Contours"):
                    conto = roi_geom.PrimaryShape.Contours 
            
                    pointsAdded=0           
                
                    ###############################################################
                    # Reference coordinates for z (SP) and x,y (RFH)
                    sSet = case.PatientModel.StructureSets[exam.Name]
                    ref_SP = getRefPointCoordinates(sSet, REF_POINT_SP)
                    ref_RFH = getRefPointCoordinates(sSet, REF_POINT_RFH)
                    
                    refX = ref_RFH['x']  # NOTE that these ref points vary slightly between exams
                    refY = ref_RFH['y']
                    #global refZ
                    refZ = ref_SP['z']
                    
                    if abs(ref_SP['x']-ref_RFH['x']) < 2.0:
                        print("---> WARNING(1): Check that SP and RFH are positioned correctly in {}".format(exam.Name) )
                    if abs(ref_SP['z']-ref_RFH['z']) < 2.0:
                        print("---> WARNING(2): Check that SP and RFH are positioned correctly in {}".format(exam.Name) )                
                    if abs(ref_SP['z']) > 100:
                        print("---> WARNING(3): Check that SP point has been positioned in {}".format(exam.Name) ) 
                    if abs(ref_RFH['z']) > 100:
                        print("---> WARNING(4): Check that RFH point has been positioned in {}".format(exam.Name) )              
                              
                    #print(" ----  Origin of new coord system ---- ")
                    #print(exam.Name)
                    #print("RFH point: x = {}, y = {}".format(ref_RFH['x'],ref_RFH['y'])  )
                    #print("SP point: z = ".format(ref_SP['z']) )
                    
                    print("... {} in {}".format(roi_name,exam.Name)  ) 
                    ################################################################
                
                
                
                    # Get relevant ROI Geometry 
                    roiGeom = case.PatientModel.StructureSets[exam.Name].RoiGeometries[roi_name]    
            
                    # Get relevant z-coordinate limits of ROI
                    z_lims = findSliceLimits(roiGeom, exam.Name)            
                    z_min = z_lims[0];  z_max = z_lims[1]




                    ################## Want sup/inf information for Zing #######################
                    # Assume largest z value is "sup", min is "inf"        TODO: check this is true
                    if exam.Name == BASE_EXAMINATION: #MUST come first in list of exams
                        BASE_SCAN_SUPINF = {'roi':roi_name, 'exam':exam.Name, 'S.z':z_max-refZ, 'I.z':z_min-refZ }
                        #BASE_SCAN_SUPINF.append( supinf_info )

                    ##else:
                    # put this in the else block if we don't want to print out the zero values of the base scan
                    supinf_line =  ( roi_name + ',' + exam.Name + ',' + 
                            str( (z_max-refZ) - BASE_SCAN_SUPINF['S.z'] ) + ',' + 
                            str( (z_min-refZ) - BASE_SCAN_SUPINF['I.z'] ) + '\n'  )

                    supinf_to_print.append( supinf_line )

                    ############################################################################



                    # Get list of the z-coordinates of desired slices 
                    #  (TODO: ensure same "closest slice" not selected multiple times; or just remove from list at end)
                    slice_selection = [ ]
                    s = z_min - SLICE_INTERVAL
                    while s < z_max:
                        s = s + SLICE_INTERVAL
                        slice_selection.append( s )
                    
                    
                    
                    # For each slice, get R/L/A/P extreme points
                    for z in slice_selection:       
                                                         
                        # Get the extreme points for current ROI
                        list_of_contours = findContoursListNearPos(roiGeom, z)
                        ext_coords = findExtremePoints(list_of_contours, refX, refY, refZ)

                        
                        ### BASE_EXAMINATION must always appear first in list ###
                        #print(exam.Name)
                        if exam.Name == BASE_EXAMINATION:
                            planning_slice = {'roi':roi_name, 'exam':exam.Name, 'z':z-refZ, 'R.x':ext_coords['R.x'], 'R.y':ext_coords['R.y'], 'L.x':ext_coords['L.x'], 'L.y':ext_coords['L.y'], 'P.x':ext_coords['P.x'], 'P.y':ext_coords['P.y'], 'A.x':ext_coords['A.x'], 'A.y':ext_coords['A.y']   }

                            BASE_SCAN.append( planning_slice )
                            
                        
                        #################################
                        ## We want to give all values wrt to the BASE_EXAMINATION.
                        ## If we find z-values outside range of BASE_EXAMINATION, we use the extreme values of the BASE_EXAMINATION,
                        ## rather than not using the data. 
                        ## TODO: would all users actually want this though? Is there a better option?
                        closest_z = -999
                        min_diff = 9E99 
                        closest_indx = 99999

                        base_min = 9E99
                        base_max = -9E99  

                        
                        for ind,dct in enumerate(BASE_SCAN):                                        
                        
                            # Here we always select the closest slice in BASE_SCAN,
                            # even if it is very far from the current exam slice
                            planning_z = dct['z']
                                
                            diff = abs(  (z-refZ) - planning_z  )                                                   
                                                
                            if diff < min_diff:
                                min_diff = diff
                                closest_z = planning_z
                                closest_indx = ind   

                            '''       
                            if planning_z < base_min:
                                base_min = planning_z
                            if planning_z > base_max:
                                base_max = planning_z
                            '''
                        ############################################


            
                        #TODO (?): currently we ALWAYS choose the closest slice in the BASE_SCAN.
                        # i.e. it's like we extend the BASE_SCAN out when needed.
                        # This is likely totally fine for large volumes with little sup/inf
                        # motion but would give meaningless results for a small volume or for 
                        # large sup/inf motion.
                        # One option would be to only record L/R/A/P motion for slices that
                        # do actually overlap in the patient.
                        # To do this, here we would do something like:
                        # 
                        # if( (z_min-refZ)<base_min or (z_max-refZ)>base_max  ):
                        #     do nothing
                        # else:
                        #     append line
                        

                        # Line to be added to .csv output file, referenced to "Planning CT"
                        #line =  (  roi_name + ',' + exam.Name + ',' + str( z ) + ',' +  #### THIS WILL GIVE ACTUAL Z OF SLICE
                        line =  (  roi_name + ',' + exam.Name + ',' + str( z - refZ  ) + ',' + 
                                str( ext_coords['R.x'] - BASE_SCAN[closest_indx]['R.x']) + ',' + 
                                str( ext_coords['L.x'] - BASE_SCAN[closest_indx]['L.x']) + ',' + 
                                str( ext_coords['P.y'] - BASE_SCAN[closest_indx]['P.y']) + ',' + 
                                str( ext_coords['A.y'] - BASE_SCAN[closest_indx]['A.y']) + '\n' )
                        strings_to_print.append( line )
                        

                        """
                        # Add some of these extreme points to image          
                        if pointsAdded < 10:
                            pointsAdded = pointsAdded + 1
                            ## add the reference coords back in!!
                            coords = {'x':ext_coords['L.x']+refX,'y':ext_coords['L.y']+refY,'z':ext_coords['L.z']+refZ}
                            makePointAtCoords(case, exam, coords, 'left_ext'+str(pointsAdded), pointColor='Red')
                            coords_r = {'x':ext_coords['R.x']+refX,'y':ext_coords['R.y']+refY,'z':ext_coords['R.z']+refZ}
                            makePointAtCoords(case, exam, coords_r, 'right_ext'+str(pointsAdded), pointColor='Blue')                
                        """
                        
                else:
                    print("---> WARNING: No contour for {} in {}".format(roi_name,exam.Name)  ) 
            else:
                print("---> WARNING: No ROI for {} in {}".format(roi_name,exam.Name)  )

                
     

    # Now print all data
    with open(filename, 'a') as fp:
        for line in strings_to_print:
            fp.write( line )


    with open(filename_supinf, 'a') as fp:
        for line in supinf_to_print:
            fp.write( line )




