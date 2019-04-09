"""
Set the ExcludeFromExport flag on ROIs that are not required for RadCalc or XVI

To run type:
    from rmh.patientModel.roi import setExcludeExport
    setExcludeExport.main()
"""

from setExcludeExport_gui import generateWarning
from rmh.dialogs import RmhMessageBox
from rmh.utilities import approval

import sys, os, math, clr

try:
    import connect as rsl
except:
    print('No RayStation connection available using offline testing connection.')
    from rmh.test import rslOffline as rsl


DEFAULT_TITLE = "Exclude ROIs From Export"

  
def get_rois(patient, caseName):
    '''Return list of ROIs in patient'''
    rois = [roi for roi in patient.Cases[caseName].PatientModel.RegionsOfInterest ]
    return rois
    
    
    
def get_nonexcluded_rois(patient, caseName):
    '''Return list of only ROIs unselected for exclusion (i.e. default; for export)'''
    rois = [roi for roi in patient.Cases[caseName].PatientModel.RegionsOfInterest if not roi.ExcludeFromExport ]
    return rois


    
def remove_supports(list_rois):
    '''  Remove any ROIs from list that are of type Support   '''
    return [ roi for roi in list_rois if roi.Type.lower().strip() != 'support'  ]


    
def remove_bolus(list_rois):
    ''' Remove any ROIs from list that are of type Bolus  '''
    return [ roi for roi in list_rois if roi.Type.lower().strip() != 'bolus'  ]

    
    
def remove_externals(list_rois):
    ''' Remove any ROIs from list that are of type External  '''
    return [ roi for roi in list_rois if roi.Type.lower().strip() != 'external'  ]
    
   
def remove_density_overrides(list_rois):
    ''' Remove any ROIs that have a matrial density override  '''
    return [ roi for roi in list_rois if roi.RoiMaterial is None ]   
    
    
def remove_targets(list_rois):
    ''' Remove any ROIs from list that are of type Target  '''
    return [ roi for roi in list_rois if roi.OrganData.OrganType.lower().strip() != 'target'  ]
    
    

def remove_clinical_goals(rois, patient, caseName, planName):
    ''' Remove from list all OARs that are clinical goals, since these should be exported '''
    
    # Get list of OARs that are clinical goals
    goals = []
    for ef in patient.Cases[caseName].TreatmentPlans[planName].TreatmentCourse.EvaluationSetup.EvaluationFunctions:
        oar = ef.ForRegionOfInterest.Name.lower()
        if oar not in goals: # don't duplicate entries
            goals.append( oar )
    
    return [ rr for rr in rois if rr.Name.lower() not in goals ]
    
    
    
def remove_approved_rois(rois, case):
    ''' Remove any approved structures from list 
    
    Trying to modify ExcludeFromExport fo these causes RayStation to crash! 
    '''
    
    # Get list of approved structures
    approved_list = []
    
    for sSet in case.PatientModel.StructureSets:
        if sSet.ApprovedStructureSets.Count > 0:
            for approvedSet in sSet.ApprovedStructureSets:
                approved_list = approved_list + [approveRoi.OfRoi.Name.lower() for approveRoi in approvedSet.ApprovedRoiStructures]
    
    # Exclude approved structure from roi list
    return [rr for rr in rois if rr.Name.lower() not in approved_list ]
    
           

            
def select_for_exclusion( rois_to_exclude, patient, caseName ):
    ''' Exclude from export all ROIs in list provided '''
    for r in rois_to_exclude:
        print("  trying to remove ", r.Name)
        patient.Cases[caseName].PatientModel.RegionsOfInterest[r.Name].ExcludeFromExport = 1 

            


def findAndExcludeROIs(patient=None, case=None, plan=None):
    
    if patient is None:
        try: 
            patient = rsl.get_current('Patient')
        except:
            RmhMessageBox.message("No patient selected!", title=DEFAULT_TITLE)
            return
    
    if case is None:
        try:     
            case = rsl.get_current('Case')
        except:
            RmhMessageBox.message("No case selected!", title=DEFAULT_TITLE)
            return
    
    if plan is None:
        try:
            plan = rsl.get_current('Plan')
        except:
            RmhMessageBox.message("No plan selected!", title=DEFAULT_TITLE)
            return
    
    caseName = case.CaseName
    planName = plan.Name
    
    
    
    # Deal with plan approvals; If plan is approved, no edits allowed, end script 
    if plan.Review is not None and plan.Review.ApprovalStatus == 'Approved':
        print('Plan is approved and not editable!')
        return
    
    ######### Make list of ROIs that we will exclude from export ##########
 
    # Get all ROIs not currently selected for exclusion (this is default, "Exclude from export" is unselected, 
    #    assume any selected were done so intentionally)
    nonexcluded_rois = get_nonexcluded_rois(patient, caseName) 
        
        
    # Remove "Bolus" and "Support" types from list i.e. couch, immobiliation device. 
    #    IMPORTANT since trying to change ExcludeFromExport for causes script to crash. THIS MAY JUST BE THAT THEY WERE "APPROVED"?
    rois_to_exclude = remove_supports( nonexcluded_rois )
    rois_to_exclude = remove_bolus( rois_to_exclude )


    # RayStation forbids exclusion of ROIs with a density override; remove these
    rois_to_exclude = remove_density_overrides( rois_to_exclude )

    
    # Remove any "External" types from list
    rois_to_exclude = remove_externals( rois_to_exclude )
    
    
    # Remove any Target organs since we don't want to alter these (maybe we want to check for mis-labelling of ROI types?)
    rois_to_exclude = remove_targets( rois_to_exclude )

    
    # Remove clinical goals from exclusion list
    rois_to_exclude = remove_clinical_goals( rois_to_exclude, patient, caseName, planName )

    
    # Remove any ROIs that have been approved (attempting to modify immutable object causes RayStation to crash)
    rois_to_exclude = remove_approved_rois( rois_to_exclude, case )

   
       
    #########  Now select these for exlcusion  ####### 
    select_for_exclusion( rois_to_exclude, patient, caseName )
    
    
    
    # Make message window to prompt selection check
    num_to_exclude = len( rois_to_exclude )
    prompt = str(num_to_exclude)+' ROIs have been excluded from export\n'
    for r in rois_to_exclude:
        prompt = prompt + '\n      '+r.Name
    
    generateWarning(prompt)

            
    
    
    
    
    
    
def main():

    # Get current 'Patient' object plus 'Case' and 'Plan' names
    try: 
        patient = rsl.get_current('Patient')
    except:
        RmhMessageBox.message("No patient selected!", title=DEFAULT_TITLE)
        return
    
    try:     
        case = rsl.get_current('Case')
    except:
        RmhMessageBox.message("No case selected!", title=DEFAULT_TITLE)
        return
    
    try:
        plan = rsl.get_current('Plan')
    except:
        RmhMessageBox.message("No plan selected!", title=DEFAULT_TITLE)
        return

        
        
    # Wrap whole method into single action to be undone
    actionName = 'Set Exclusion status on ROIs'
    with rsl.CompositeAction(actionName):   
        findAndExcludeROIs(patient, case, plan)

    
    
    
    
    
