"""
Unit tests of the module setExcludeExport

To run tests type:
    from rmh.patientModel.roi import test_setExcludeExport
    test_setExcludeExport.run_tests()
"""

# -------------- #

from rmh.test import rslOffline as rsl
from rmh.test.dummyPatient import addRegionOfInterest

from rmh.patientModel.roi import setExcludeExport
import nose

reload(setExcludeExport)

# -------------- #

def test_nonExcludedRois():
    """
    Do we find all ROIs not excluded from export?
    """
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    
    case.PatientModel.RegionsOfInterest[0].ExcludeFromExport = True
    addRegionOfInterest(case, Name='ROI_2', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[1].ExcludeFromExport = True
    addRegionOfInterest(case, Name='ROI_3', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[2].ExcludeFromExport = False
    addRegionOfInterest(case, Name='ROI_4', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[3].ExcludeFromExport = False
    addRegionOfInterest(case, Name='ROI_5', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[4].ExcludeFromExport = False
    
    expectRoiNameList = [
        case.PatientModel.RegionsOfInterest[2], 
        case.PatientModel.RegionsOfInterest[3], 
        case.PatientModel.RegionsOfInterest[4]
        ]
    
    result = setExcludeExport.get_nonexcluded_rois(patient, case.CaseName)
    
    for rResult, rExpect in zip(result, expectRoiNameList):
        print('Problem occured: Expected %s and result was %s' % (rExpect.Name, rResult.Name))
        assert(rResult == rExpect)

        
# -------------- #

def test_removeSupports():
    """
    Do we remove Support types? 
    
    NOTE that this test requires the order of ROIs in the list to be 
    the same when this isn't actually important
    
    """
   
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    
    case.PatientModel.RegionsOfInterest[0].Type = 'Organ'
    addRegionOfInterest(case, Name='ROI_a', Color='Red', Type='Support')
    addRegionOfInterest(case, Name='ROI_b', Color='Red', Type='Organ')
    addRegionOfInterest(case, Name='ROI_c', Color='Red', Type='Support')
    addRegionOfInterest(case, Name='ROI_d', Color='Red', Type='Organ')
    
    expectRoiNameList = [
        case.PatientModel.RegionsOfInterest[0],  ## this is already present 
        case.PatientModel.RegionsOfInterest[2], 
        case.PatientModel.RegionsOfInterest[4]
        ]
        
    list_of_rois = case.PatientModel.RegionsOfInterest
    
    result = setExcludeExport.remove_supports( list_of_rois )
    
    for rResult, rExpect in zip(result, expectRoiNameList):
        print('Problem occured: Expected %s and result was %s' % (rExpect.Name, rResult.Name))
        assert(rResult == rExpect)    

        
        
# -------------- #



def test_removeBolus():
    """
    Do we remove Bolus types? 
    """
   
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    
    case.PatientModel.RegionsOfInterest[0].Type = 'Organ'
    addRegionOfInterest(case, Name='ROI_a', Color='Red', Type='Bolus')
    addRegionOfInterest(case, Name='ROI_b', Color='Red', Type='Organ')
    addRegionOfInterest(case, Name='ROI_c', Color='Red', Type='Bolus')
    addRegionOfInterest(case, Name='ROI_d', Color='Red', Type='Organ')
    
    expectRoiNameList = [
        case.PatientModel.RegionsOfInterest[0],  ## this is already present 
        case.PatientModel.RegionsOfInterest[2], 
        case.PatientModel.RegionsOfInterest[4]
        ]
        
    list_of_rois = case.PatientModel.RegionsOfInterest
    
    result = setExcludeExport.remove_bolus( list_of_rois )
    
    for rResult, rExpect in zip(result, expectRoiNameList):
        print('Problem occured: Expected %s and result was %s' % (rExpect.Name, rResult.Name))
        assert(rResult == rExpect)    

# -------------- #




def test_removeDensityOverrides():
    """
    Do we remove all ROIs with a material density overide? 
    """
   
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    
    case.PatientModel.RegionsOfInterest[0].Type = 'Organ'
    
    addRegionOfInterest(case, Name='ROI_a', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[1].RoiMaterial = case.PatientModel.Materials[0]
    
    addRegionOfInterest(case, Name='ROI_b', Color='Red', Type='Organ')
    addRegionOfInterest(case, Name='ROI_d', Color='Red', Type='Organ')
    
    expectRoiNameList = [
        case.PatientModel.RegionsOfInterest[0],
        case.PatientModel.RegionsOfInterest[2], 
        case.PatientModel.RegionsOfInterest[3]
        ]
        
    list_of_rois = case.PatientModel.RegionsOfInterest
    
    result = setExcludeExport.remove_density_overrides( list_of_rois )
    
    for rResult, rExpect in zip(result, expectRoiNameList):
        print('Problem occured: Expected %s and result was %s' % (rExpect.Name, rResult.Name))
        assert(rResult == rExpect)    

# -------------- #



   

   
def test_removeExternals():
    """
    Do we remove External types? 
    """
   
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    
    case.PatientModel.RegionsOfInterest[0].Type = 'Organ'
    addRegionOfInterest(case, Name='ROI_a', Color='Red', Type='External')
    addRegionOfInterest(case, Name='ROI_b', Color='Red', Type='Organ')  #2
    addRegionOfInterest(case, Name='ROI_c', Color='Red', Type='External') #3
    addRegionOfInterest(case, Name='ROI_d', Color='Red', Type='Organ') #4
    
    expectRoiNameList = [
        case.PatientModel.RegionsOfInterest[0],  ## this is already present 
        case.PatientModel.RegionsOfInterest[2], 
        case.PatientModel.RegionsOfInterest[4]
        ]
        
    list_of_rois = case.PatientModel.RegionsOfInterest
    
    result = setExcludeExport.remove_externals( list_of_rois )
    
    for rResult, rExpect in zip(result, expectRoiNameList):
        print('Problem occured: Expected %s and result was %s' % (rExpect.Name, rResult.Name))
        assert(rResult == rExpect)    

# -------------- #
    
    
    
def test_removeTargets():
    """
    Do we remove Target types?
    
    NOTE: this field is in roi.OrganData.OrgnType
    """  
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    
    case.PatientModel.RegionsOfInterest[0].OrganData.OrganType = 'Other'
    addRegionOfInterest(case, Name='ROI_2', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[1].OrganData.OrganType = 'Target'
    addRegionOfInterest(case, Name='ROI_3', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[2].OrganData.OrganType = 'Other'
    addRegionOfInterest(case, Name='ROI_4', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[3].OrganData.OrganType = 'Target'
    addRegionOfInterest(case, Name='ROI_5', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[4].OrganData.OrganType = 'Other'
     
    expectRoiNameList = [
        case.PatientModel.RegionsOfInterest[0],  ## this is already present 
        case.PatientModel.RegionsOfInterest[2], 
        case.PatientModel.RegionsOfInterest[4]
        ]
        
    list_of_rois = case.PatientModel.RegionsOfInterest
    
    result = setExcludeExport.remove_targets( list_of_rois )
    
    for rResult, rExpect in zip(result, expectRoiNameList):
        print('Problem occured: Expected %s and result was %s' % (rExpect.Name, rResult.Name))
        assert(rResult == rExpect)    

# -------------- #
    
    

    
def test_removeClinicalGoals():
    """
    Do we remove all ROIs that are clinical goals?
    
    IN HERE: patient.Cases[caseName].TreatmentPlans[planName].TreatmentCourse.EvaluationSetup.EvaluationFunctions
    """  
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    plan = case.TreatmentPlans[0]
        
    # create one clinical goal (i.e. an ROI found here: 
    #    patient.Cases[caseName].TreatmentPlans[planName].TreatmentCourse.EvaluationSetup.EvaluationFunctions )   
    plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[0].ForRegionOfInterest.Name = 'clinical_goal'
    
    addRegionOfInterest(case, Name='ROI_2', Color='Red', Type='Organ')
    addRegionOfInterest(case, Name='clinical_goal', Color='Red', Type='Organ')
    addRegionOfInterest(case, Name='ROI_4', Color='Red', Type='Organ')
  
    expectRoiNameList = [
        case.PatientModel.RegionsOfInterest[0],  
        case.PatientModel.RegionsOfInterest[1], 
        case.PatientModel.RegionsOfInterest[3]
        ]
        
    list_of_rois = case.PatientModel.RegionsOfInterest
    
    result = setExcludeExport.remove_clinical_goals( list_of_rois, patient, case.CaseName, plan.Name  )
    
    for rResult, rExpect in zip(result, expectRoiNameList):
        print('Problem occured: Expected %s and result was %s' % (rExpect.Name, rResult.Name))
        assert(rResult == rExpect)    

# -------------- #





def test_removeApprovedStructures():
    """
    Do we remove all approved ROIs from list?    
    """  
    
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    plan = case.TreatmentPlans[0]

    # Add an approved ROI
    case.PatientModel.StructureSets[0].ApprovedStructureSets[0].ApprovedRoiStructures[0].OfRoi.Name = 'ROI_approved'
  
    addRegionOfInterest(case, Name='ROI_2', Color='Red', Type='Organ')
    addRegionOfInterest(case, Name='ROI_approved', Color='Red', Type='Organ')
    addRegionOfInterest(case, Name='ROI_4', Color='Red', Type='Organ')
  
    expectRoiNameList = [
        case.PatientModel.RegionsOfInterest[0],  
        case.PatientModel.RegionsOfInterest[1], 
        case.PatientModel.RegionsOfInterest[3]
        ]
        
    list_of_rois = case.PatientModel.RegionsOfInterest
    
    result = setExcludeExport.remove_approved_rois( list_of_rois, case  )
    
    for rResult, rExpect in zip(result, expectRoiNameList):
        print('Problem occured: Expected %s and result was %s' % (rExpect.Name, rResult.Name))
        assert(rResult == rExpect)    

# -------------- #



    

def test_selectForExclusion():
    """
    Do we successfully exclude desired ROIs?
    """
    patient = rsl.get_current('Patient')
    case = patient.Cases[0]
    
    case.PatientModel.RegionsOfInterest[0].ExcludeFromExport = False
    addRegionOfInterest(case, Name='ROI_2', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[1].ExcludeFromExport = False
    addRegionOfInterest(case, Name='ROI_3', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[2].ExcludeFromExport = False
    addRegionOfInterest(case, Name='ROI_4', Color='Red', Type='Organ')
    case.PatientModel.RegionsOfInterest[3].ExcludeFromExport = False
    
    # Make list of ROIS to alter ExcludeFromExport -> True  
    rois_to_exclude=[]
    rois_to_exclude.append(case.PatientModel.RegionsOfInterest[1])
    rois_to_exclude.append(case.PatientModel.RegionsOfInterest[2])
    
    setExcludeExport.select_for_exclusion(rois_to_exclude, patient, case.CaseName)
    
    for roi in rois_to_exclude:
        print('Problem occured: ROI %s should be excluded ' % roi.Name )
        assert(roi.ExcludeFromExport == True )

        
# -------------- #
    
    
    
    

    
    
def run_tests():
    """
    Run all the automated tests on this script
    """
    nose.run(argv=['', __file__, '-v'])
  
run_tests.__test__ = False