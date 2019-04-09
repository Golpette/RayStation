"""
Create a deformable registration and map ROIs.
Designed for use with the INSIGHT-2 adaptive H&N trial

To run type:
    from rmh.plan import adaptive_create_def_reg
    adaptive_create_def_reg.main()
"""

import connect as rsl
import os
import json

from rmh.dialogs import (
    chooseFromList, enterNumber, RmhMessageBox
)

''' QUESTIONS:
#  Make new ROIs for CTVs copied via rigid registration?
#  Map CTVs to new "CTV_dir"
#  What about a re-derived CTV from the mapped GTV? (Margin of 1cm?)
'''

######################################################

DEFAULT_MAP_FILE = os.path.join(os.path.split(__file__)[0],"adaptive_create_def_reg_required_mappings.json")

# Define unique name of DIR
REGISTRATION_GROUP_NAME = "xxx_DIR"
# I think by naming explicitly naming the DIR we cannot run the script twice.
# Can I have DIRs between different image pairs with the same name, or is this a problem?


#####################################################

def loadRequiredMappings(mapFile=None):
    """
    Load the list of required ROI names to map from a json file
    """
    if mapFile is None:
        mapFile = DEFAULT_MAP_FILE
    
    with open(mapFile,"rt") as fp1:
        mappings = json.load(fp1)
        return [x.lower() for x in mappings]
        
#####################################################

def makeDIR( old_exam, new_exam, patient=None, case=None, requiredMappings=None ):
    """
    Creates intensity-based deformable image registration with mapped ROIs  
    (1)Create external contour; (2)Rigid reg; (3)DIR; (4)map non-derived ROIs.
    """
    
    if patient is None:
        patient = rsl.get_current("Patient")
    if case is None:
        case = rsl.get_current("Case")
    if requiredMappings is None:
        requiredMappings = loadRequiredMappings()
	
	
	print("TODO: check if any of the contours already exist in the rescan and deal with them")
    # Don't want to override anything that already exists...
    
    print("Creating external ROI")
    case.PatientModel.RegionsOfInterest['External'].CreateExternalGeometry(Examination=new_exam, ThresholdLevel=-250)

    
    print("Performing rigid registration")
    case.ComputeRigidImageRegistration(       
        FloatingExaminationName = new_exam.Name,         
        ReferenceExaminationName = old_exam.Name,         
        UseOnlyTranslations=False, HighWeightOnBones=False, InitializeImages=True, 
        FocusRoisNames=[], 
        #RegistrationName=None
        RegistrationName = "RigidReg"
    )


    print("Performing intensity-based deformable registration")
    # The older planning scan is the "target" and rescan is the "reference" image
    # No controlling ROIs or POIs
    case.PatientModel.CreateHybridDeformableRegistrationGroup(
            RegistrationGroupName = REGISTRATION_GROUP_NAME, 
            ReferenceExaminationName = new_exam.Name, 
            TargetExaminationNames=[ old_exam.Name ], 
            ControllingRoiNames=[], ControllingPoiNames=[], FocusRoiNames=[], 
            AlgorithmSettings = { 'NumberOfResolutionLevels': 3, 'InitialResolution': { 'x': 0.5, 'y': 0.5, 'z': 0.5 }, 
                'FinalResolution': { 'x': 0.25, 'y': 0.25, 'z': 0.25 }, 'InitialGaussianSmoothingSigma': 2, 'FinalGaussianSmoothingSigma': 0.333333333333333, 
                'InitialGridRegularizationWeight': 400, 'FinalGridRegularizationWeight': 400, 'ControllingRoiWeight': 0.5, 'ControllingPoiWeight': 0.1, 
                'MaxNumberOfIterationsPerResolutionLevel': 1000, 'ImageSimilarityMeasure': "CorrelationCoefficient", 'DeformationStrategy': "Default", 'ConvergenceTolerance': 1E-05 
            }
    )  
    
  
    print("Obtaining list of ROIs to map")
    rois_to_map = [ 
        roi_geom.OfRoi.Name for roi_geom in case.PatientModel.StructureSets[ old_exam.Name ].RoiGeometries
        if roi_geom.OfRoi.Name.lower() in requiredMappings
        #and roi_geom.OfRoi.DerivedRoiExpression is None  
		## Do we want this anymore? Can't have it if we want to map derived CTVs!
        and roi_geom.PrimaryShape is not None
        and roi_geom.HasContours()
    ]    

   
    print "rois to map: ", rois_to_map
   
   
    print("Mapping ROIs")
    case.MapRoiGeometriesDeformably(
        RoiGeometryNames = rois_to_map, 
        CreateNewRois=True,
        StructureRegistrationGroupNames=[REGISTRATION_GROUP_NAME], 
        ReferenceExaminationNames=[new_exam.Name], TargetExaminationNames=[old_exam.Name], 
        ReverseMapping=True, AbortWhenBadDisplacementField=False
    )
	
    

    print("Displaying DIR screen for review and approval")
    ui = rsl.get_current('ui')
    try:
        ui.TitleBar.MenuItem['Patient Modeling'].Button_Patient_Modeling.Click()
    except SystemError as se:
        if "is not present in the collection" in se.message:
            print("No 'Patient Modeling' tab")
            
    ui = rsl.get_current('ui')
    try:
        ui.TabControl_Modules.TabItem['Deformable Registration'].Button_Deformable_Registration.Click()
    except SystemError as se:
        if "is not present in the collection" in se.message:
            print("No 'Deformable Registration tab")    
    
    # Something like this to actually bring up the registration?
    # ui.TabControl_ToolBar.ToolBarGroup['CURRENT REGISTRATION'].RayPanelDropDownItem['Select'].DropDownButton_Select.TextBlock_OpenDropDownCommand_DisplayText
    

    #Prompt user to inspect registration
    msg = "\nClose script and click \"Select\" to inspect the registration and mapping\n" 
    RmhMessageBox.message( msg, 'Script finished')
     
    
	
# ---------------------------------- #


def select_scan(case, prompt):
    """
    Select an examination
    """
    candidateCTs = [
        exam.Name for exam in case.Examinations 
        if exam.EquipmentInfo.Modality == "CT"
        and not "Elekta" in exam.EquipmentInfo.ImagingSystemReference.ImagingSystemName
    ]
    
    title = "Select an image"
    
    if len(candidateCTs) == 0:
        raise DeformRegException("Case has no CT images")
    elif len(candidateCTs) > 1:
        # Add dates to list
        choose_from = []
        for c in candidateCTs:
            date_time = case.Examinations[c].GetExaminationDateTime()
            choose_from.append( c + " ---- " + str(date_time) )
            
        ct_with_date = chooseFromList.getChoiceFromList(choiceList=choose_from, prompt=prompt, title=title)       
        candidateCT = ct_with_date.split("----")[0].strip()          
    else:
        candidateCT = candidateCTs[0]
        
    return candidateCT
    
	
# ---------------------------------- #

	
class DeformRegException(Exception):
    """
    Custom exception for creation of DIR
    """
    pass

# ---------------------------------- #




    
def main():
    
    patient = rsl.get_current("Patient")
    case = rsl.get_current("Case")
    
    #Select original
    original_scan = select_scan(case, "Select previous planning scan (target)")
    old_exam = case.Examinations[original_scan]

    #Select rescan
    rescan = select_scan(case, "Select rescan (reference)")   
    new_exam = case.Examinations[rescan]
    
   
    makeDIR( old_exam, new_exam, patient=patient, case=case )
    
    
    
    
    
    
    
