"""
Modified script to get roi stats between BH's and unknown clinician's
delineations in both planningCT and rescan

To run type:
    from rmh.batch import writeRoiStats_interObserv
    writeRoiStats_interObserv.main()
"""

import os
import connect as rsl

DEFAULT_EXPORTFILE_ROIS = r"\\xxx\roi_stats_interObserv.csv"

#PLAN_NAME = "rescan"
PLAN_NAME = "planningCT"

DEFAULT_ROILIST = ["Parotid_R", "Parotid_L", "SpinalCord", "BrainStem"]
suffix_1 = "_BH"


##########################################################################################


def exportROIDetails(patient=None, case=None, roiList=None, planName=None, exportFile_rois=None):
    '''
    Export ROI stats between BH's contours and those on the original and replan
    '''

    if patient is None:
        patient = rsl.get_current("Patient")
    if case is None:
        case = rsl.get_current("Case")
    if roiList is None:
        roiList = DEFAULT_ROILIST
    if planName is None:
        planName = PLAN_NAME
    if exportFile_rois is None:
        exportFile_rois = DEFAULT_EXPORTFILE_ROIS
    
	
    roiPairs = [ (roi+suffix_1, roi) for roi in roiList]
		

    if not os.path.isfile( exportFile_rois ):
        with open(exportFile_rois,"wt") as fp2:
            fp2.write("PatientID, RoiName, Brian's volume, Unknown's volume, DiceSimilarityCoefficient, Precision, Sensitivity, Specificity, MeanDistanceToAgreement, MaxDistanceToAgreement\n")
    
    sSet = case.PatientModel.StructureSets[planName]
    
    with open(exportFile_rois,"at") as fp2:
        
        for roi1, roi2 in roiPairs:
        
            roiResult = sSet.ComparisonOfRoiGeometries(RoiA=roi1, RoiB=roi2, ComputeDistanceToAgreementMeasures=True)
            
            vol_brian = sSet.RoiGeometries[ roi1 ].GetRoiVolume()
            vol_unknown = sSet.RoiGeometries[ roi2 ].GetRoiVolume()     
            
            fp2.write("{},{},{},{},{},{},{},{},{},{},\n ".format(
                patient.PatientID+"_"+PLAN_NAME, 
                roi1, 
                vol_brian, vol_unknown,
                roiResult['DiceSimilarityCoefficient'], 
                roiResult['Precision'],
                roiResult['Sensitivity'],
                roiResult['Specificity'],
                roiResult['MeanDistanceToAgreement'],
                roiResult['MaxDistanceToAgreement']  )  
            )

def main():
    exportROIDetails()
    










































