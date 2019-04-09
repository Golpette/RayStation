"""
Motion By Points on ROI contours
Target motion based on bony landmarks

STEVE:  This is modified from motionByPoints.py to allow for multiple replanning scans.
        It checks what planning CT each exam is registered to.
        I did this very bad: it fetches PLANNING_CT data for every exam, for every ROI, every time.
        Since only 2 patients have a replan, I didn't bother fixing this inefficiency.
        
        
to run type:
    from rmhTools.roiTools import motionByPoints_multiPlan
    motionByPoints_multiPlan.main()
"""

import connect as rsl
import os

# --------------- #


SLICE_INTERVAL = 0.25  # cm

#DESIRED_ROIS = [ 'GTVt rind_Upper', 'GTVt+1cm_Middle', 'GTVt+1cm_Lower', 'GTVt rind_Middle', 'GTVt rind_Lower', 'Mesorectum rind_Upper', 'Mesorectum rind_Lower' ]
DESIRED_ROIS = [ 'LN_R&L2', 'Mesorectum rind_Upper2', 'Mesorectum rind_Lower2' ]

REF_POINT_SP = "Ref Point SP"
REF_POINT_RFH = "Ref Point RFH"

# Directory into which profile data will be saved
dataPath = os.path.join(r'\\rtp-bridge2-rt.ad.rmh.nhs.uk\IntoSecure\ICR',os.environ['USERNAME'],'RayStationExport')

EXPORT_FILE_PREFIX = 'motionPoints_multiPlan_'





# --------------- #

def getRefPointCoordinates(sSet, pointName):
    pt = sSet.PoiGeometries[pointName].Point
    return {'x':pt.x, 'y':pt.y, 'z':pt.z}
    
# --------------- #




def findContoursListNearPos(roiGeom, zPos):
    """
    Return the LIST of roi contours closest to the requested z position   
    (sinece we can have multiple contours per slice)
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
        print "ERROR: minInd not set in findContourNearPos"
    
    # list all contours with this 
    list_conts = []
    for con in roiGeom.PrimaryShape.Contours:    
        #if con[0].z == actualZ:              ###   STEVE: THIS WAS CREATING BUGS ON RANDOM SLICES, ONLY PICKING UP 1 OF 2 CONTOURS.
        abs_diff = abs(con[0].z - actualZ)
        if( abs_diff <  0.001  ):             ## this is to catch rounding errors in RayStation.      
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





def findExtremePoints_2( contour_list, refX, refY, refZ):
    """
    Find coordinates of contour points at most extreme right-left and ant-post positions
      ** with respect to reference coords **
    NOTE: THERE MAY BE MULTIPLE CONTOURS ON A GIVEN SLICE!
    """
    minX=9E99; minY=9E99; minX_ind=-1; minY_ind=-1
    maxX=-9E99; maxY=-9E99; maxX_ind=-1; maxY_ind=-1
    
    cminX = 999; cmaxX=-999  # NEED TO STORE WHICH CONTOUR ACTUALLY HAS THE MAX VALUE
    cminY = 999; cmaxY=-999
    
    for (c,contour) in enumerate(contour_list):
    
        for (indx,pt) in enumerate(contour):
        
            if pt.x < minX:
                minX = pt.x
                minX_ind = indx
                cminX = c           # need this so we actually take extreme value from correct contour!
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
            print "Index has not been set in findExtremePoints()"
            
        extremes = {'R.x':contour_list[cminX][minX_ind].x-refX , 'R.y':contour_list[cminX][minX_ind].y-refY, 'R.z':contour_list[cminX][minX_ind].z-refZ,
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
    Produce ONLY desired list of ROIS that exist in patient
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
                print "---> WARNING: No ROI for ", roi, "in", exam.Name
                           
            try:
                pp = roi_geom.PrimaryShape.Contours
            except:
                print "---> WARNING: No contour for ", roi, "in", exam.Name
                
# --------------- # 


def getRegisteredPlan( exam, exam_list ):
    """
    Get the planning scan that this exam has been registered to
    """
    frameOfRef = exam.EquipmentInfo.FrameOfReference
    
    toreturn="x"
    for ex in exam_list:
        if 'planning' in ex.Name.lower() and ex.EquipmentInfo.FrameOfReference == frameOfRef:
            
            print "matched: ", exam.Name, "with", ex.Name
            toreturn=ex
            
    if toreturn=="x":
        print "ERROR(7) - No registered planning CT found for", exam.Name
        
    return toreturn
    
# --------------- #   


def getReferenceData( case, plan_to_register, roi_name, slice_selection ):
    """
    Create reference values for this roi in the planning CT
    """
    PLANNING_CT=[]  # TO STORE ALL REFERENCE DISTANCES
    
    roi_geom = case.PatientModel.StructureSets[plan_to_register.Name].RoiGeometries[roi_name] 

    # Reference coordinates for z (SP) and x,y (RFH)
    sSet = case.PatientModel.StructureSets[plan_to_register.Name]
    ref_SP = getRefPointCoordinates(sSet, REF_POINT_SP)
    ref_RFH = getRefPointCoordinates(sSet, REF_POINT_RFH)
            
    refX = ref_RFH['x'] 
    refY = ref_RFH['y']
    refZ = ref_SP['z']   

    # For each slice, get R/L/A/P extreme points
    for z in slice_selection:        
 
        list_of_contours = findContoursListNearPos(roi_geom, z)
        ext_coords = findExtremePoints_2(list_of_contours, refX, refY, refZ)
        
        if 'planning' in plan_to_register.Name.lower():
            planning_slice = {'roi':roi_name, 'exam':plan_to_register.Name, 'z':z-refZ, 'R.x':ext_coords['R.x'], 'R.y':ext_coords['R.y'], 'L.x':ext_coords['L.x'], 'L.y':ext_coords['L.y'], 'P.x':ext_coords['P.x'], 'P.y':ext_coords['P.y'], 'A.x':ext_coords['A.x'], 'A.y':ext_coords['A.y']   }
            PLANNING_CT.append(  planning_slice )
        else:
            print "plan_to_register is not a PlanningCT or Planning CT"
        
    return PLANNING_CT

# ------------------------- #







    
def main():


    patient = rsl.get_current('Patient')
    case = rsl.get_current('Case')
    
        
    try:
        os.makedirs(dataPath)
    except:
        pass
         
    filename = os.path.join(dataPath,'%s%s.csv' % (EXPORT_FILE_PREFIX,patient.PatientID))
    
    
    # Get relevant ROIs
    all_roi_names = getDesiredROIs(case, DESIRED_ROIS)
    
    
    if len( all_roi_names ) == 0:
        print "---> WARNING: None of the desired ROIs are present!"
    print "ROI names found:", all_roi_names

    
    
    
    # Get all exam names
    all_exams = [ exam for exam in case.Examinations ]     
    print "Exams:",[exam.Name for exam in all_exams]
    


    # Check that all ROIs that exist
    checkAllContoursPresent(case, all_exams, all_roi_names)

      
  
    ## Check for multiple planning scans  ## TODO: Deal with this properly
    exam_names = [ ex.Name for ex in all_exams ]  
    no_plans = 0
    for nm in exam_names:
        if 'planning' in nm.lower():
            no_plans += 1
    if no_plans > 1:
        print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        print "---> There are multiple planning scans associated with patient"
        print "---> All CBCTs will be registered to their appropriate Plan."
        print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


        
    
    # Make the .csv file header
    with open(filename, 'w') as fp:
        fp.write('roi,exam,z,R.x,R.y,L.x,L.y,P.x,P.y,A.x,A.y\n')
    
    
    
    
        
    strings_to_print = []
       
    for roi_name in all_roi_names:
        
        ## STORE ALL DATA FROM PLANNING CT AS REFERENCE. #####  TODO: SOME PATIENTS MIGHT HAVE 2 PLANNING SCANS
        PLANNING_CT = []   
        
        hold_register=""
        
        for exam in all_exams:
        
        
            # Find what planning ct this exam is registered to.
            plan_to_register = getRegisteredPlan( exam, all_exams )
               
            
            ###############################################################
            # Reference coordinates for z (SP) and x,y (RFH)
            sSet = case.PatientModel.StructureSets[exam.Name]
            ref_SP = getRefPointCoordinates(sSet, REF_POINT_SP)
            ref_RFH = getRefPointCoordinates(sSet, REF_POINT_RFH)
            
            refX = ref_RFH['x']  # NOTE that these vary slightly between exams
            refY = ref_RFH['y']
            refZ = ref_SP['z']   # this is sometimes one slice off between exams
            
            if abs(ref_SP['x']-ref_RFH['x']) < 2.0:
                print "---> WARNING(1): Check that SP and RFH are positioned correctly in", exam.Name
            if abs(ref_SP['z']-ref_RFH['z']) < 2.0:
                print "---> WARNING(2): Check that SP and RFH are positioned correctly in", exam.Name                
            if abs(ref_SP['z']) > 100:
                print "---> WARNING(3): Check that SP point has been positioned in", exam.Name
            if abs(ref_RFH['z']) > 100:
                print "---> WARNING(4): Check that RFH point has been positioned in", exam.Name            
                
               
            #print ' ----  Origin of new coord system ---- '
            #print exam.Name
            #print 'RFH point: x = ', ref_RFH['x'], ', y = ', ref_RFH['y']
            #print 'SP point: z = ', ref_SP['z']
            
            print "...",roi_name,"in",exam.Name
            ################################################################
            
            
            
            ## Check that both PrimaryShape and Contour exists: 
            roi_geom = case.PatientModel.StructureSets[exam.Name].RoiGeometries[roi_name]
            #roiGeom
            
            
          
            if hasattr(roi_geom, "PrimaryShape"):
                primshape = roi_geom.PrimaryShape  
                
                if hasattr( primshape, "Contours"):
                    conto = roi_geom.PrimaryShape.Contours 
            
                    pointsAdded=0                 

                    
                    
                    # Get relevant z-coordinate limits of ROI
                    z_lims = findSliceLimits(roi_geom, exam.Name)    #roiGeom        
                    z_min = z_lims[0];  z_max = z_lims[1]

                    # Get list of the z-coordinates of desired slices 
                    #     (TODO: ensure same "closest slice" not selected multiple times; or just remove from list at end)
                    slice_selection = [ ]
                    s = z_min - SLICE_INTERVAL
                    while s < z_max:
                        s = s + SLICE_INTERVAL
                        slice_selection.append( s )
                        
                        

                    # Create PLANNING_CT reference data here. THIS IS SLOW; DON'T NEED TO DO THIS EVERY TIME
                    #   only update if different
                    #if hold_to_register.Name != plan_to_register.Name:
                    if hold_register is not plan_to_register:
                        PLANNING_CT = getReferenceData( case, plan_to_register, roi_name, slice_selection )
                    else:
                       print "hold_register IS plan_to_register! PLANNING_CT not altered."
                        
                    #update hold
                    hold_register = plan_to_register
                    
                    
                 
                    # For each slice, get R/L/A/P extreme points
                    for z in slice_selection:       
                    
                    
                        # INGIRD BUG: MULTIPLE CONTOUR OBJECTS SOMETIMES PRESENT
                        list_of_contours = findContoursListNearPos(roi_geom, z)  #roiGeom
                        ext_coords = findExtremePoints_2(list_of_contours, refX, refY, refZ)
                        
                        
                        #################################
                        ## We want to give all values WRT to the PLANNING CT.
                        ## If we find z-values outside range of planning CT, we use the extreme values of the planning CT,
                        ## rather than not using the data ...... 
                        closest_z = -999
                        min_diff = 9E99
                        min_plan_z = 9E99
                        max_plan_z = -9E99
                        closest_indx = -1
                        
                        
                        for ind,dct in enumerate(PLANNING_CT):                                        
                        
                            planning_z = dct['z']
                                                
                            if planning_z < min_plan_z:
                                min_plan_z = planning_z
                            if planning_z > max_plan_z:
                                max_plan_z = planning_z
                                
                            diff = abs(  (z-refZ) - planning_z  )
                            #diff = abs( z - planning_z )
                                                
                            if diff < min_diff:
                                min_diff = diff
                                closest_z = planning_z
                                closest_indx = ind
                                
                        '''        
                        if closest_z < min_plan_z:
                            closest_z = min_plan_z
                            closest_indx = 0                  ## IS THIS SAFE? i.e SLICES ALWAYS IN ORDER SMALLEST TO BIGGEST Z-VALUE?
                        if closest_z > max_plan_z:
                            closest_z = max_plan_z
                            closest_indx = len(PLANNING_CT)-1
                        '''
                        ############################################

                        #print "closest_indx", closest_indx
                        
                        
                        # Line to be added to .csv output file, referenced to "Planning CT"
                        #line =  (  roi_name + ',' + exam.Name + ',' + str( z ) + ',' +  #### THIS WILL GIVE ACTUAL Z OF SLICE
                        line =  (  roi_name + ',' + exam.Name + ',' + str( z - refZ  ) + ',' + 
                                str(ext_coords['R.x'] - PLANNING_CT[closest_indx]['R.x']) + ',' + 
                                str(ext_coords['R.y'] - PLANNING_CT[closest_indx]['R.y']) + ',' + 
                                str(ext_coords['L.x'] - PLANNING_CT[closest_indx]['L.x']) + ',' + 
                                str(ext_coords['L.y'] - PLANNING_CT[closest_indx]['L.y']) + ',' + 
                                str(ext_coords['P.x'] - PLANNING_CT[closest_indx]['P.x']) + ',' + 
                                str(ext_coords['P.y'] - PLANNING_CT[closest_indx]['P.y']) + ',' + 
                                str(ext_coords['A.x'] - PLANNING_CT[closest_indx]['A.x']) + ',' + 
                                str(ext_coords['A.y'] - PLANNING_CT[closest_indx]['A.y']) + '\n'    )    
                        strings_to_print.append( line )
                        
                        
                        # Printed for debugging
                        #if pointsAdded < 10 and exam.Name == 'CBCT5':
                        #    print "R.x CBCT1 - PlanningCT : " + str(ext_coords['R.x']) + " - " + str( PLANNING_CT[closest_indx]['R.x'] )
                        #    print "L.x CBCT1 - PlanningCT : " + str(ext_coords['L.x']) + " - " + str( PLANNING_CT[closest_indx]['L.x'] )
                        
                        
                        '''
                        # Add some of these extreme points to image          
                        if pointsAdded < 10:
                            pointsAdded = pointsAdded + 1
                            ## add the reference coords back in!!
                            coords = {'x':ext_coords['L.x']+refX,'y':ext_coords['L.y']+refY,'z':ext_coords['L.z']+refZ}
                            makePointAtCoords(case, exam, coords, 'left_ext'+str(pointsAdded), pointColor='Red')
                            coords_r = {'x':ext_coords['R.x']+refX,'y':ext_coords['R.y']+refY,'z':ext_coords['R.z']+refZ}
                            makePointAtCoords(case, exam, coords_r, 'right_ext'+str(pointsAdded), pointColor='Blue')                
                        '''
                        
                else:
                    print "---> WARNING: No contour for ", roi_name, "in", exam.Name
            else:
                print "---> WARNING: No ROI for ", roi_name, "in", exam.Name      
                
                
     

    # Now print all data
    with open(filename, 'a') as fp:
        for line in strings_to_print:
            fp.write( line )

     
