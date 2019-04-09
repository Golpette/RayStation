"""
To run type:

from rmh.batch import writePoiRoiStats
writePoiRoiStats.main()
"""

import os
import connect as rsl


DEFAULT_TARGETNAME = "planningCT"
DEFAULT_REFNAME = "rescanCT"
MAPPED_SUB = "planningCT->rescanCT"

DEFAULT_EXPORTFILE_ROIS = r"\\xxx\roi_stats.csv"


DEFAULT_ROILIST = [  
    "GTV_N", "GTV_P",
    "CTV_65Gy", "CTV_54Gy",	"CTV_60Gy",
    "Parotid_R", "Parotid_L",
    "SpinalCord", "BrainStem", "Chiasm",
    "OpticNerve_R", "OpticNerve_L",
    "Lens_R", "Lens_L",
    "Globe_R", "Globe_L", 
    "Nodes_OP"
	]


##DEFAULT_POILIST = ["C3","C2", "clivus", "RT pterygoid", "T1 spinous process"]
#DEFAULT_EXPORTFILE = r"\\xxx\poi_stats.csv"


##########################################################################################
'''
def exportPointDetails(patient=None, case=None, poiList=None, targetName=None, refName=None, exportFile=None):
    
    if patient is None:
        patient = rsl.get_current("Patient")
    if case is None:
        case = rsl.get_current("Case")
    if poiList is None:
        poiList = DEFAULT_POILIST
    if targetName is None:
        targetName = DEFAULT_TARGETNAME
    if refName is None:
        refName = DEFAULT_REFNAME
    if exportFile is None:
        exportFile = DEFAULT_EXPORTFILE
        
    #regGrp = case.PatientModel.StructureRegistrationGroups['no ROIs']

    case.MapPoiGeometriesDeformably(
        PoiGeometryNames=poiList, CreateNewPois=True, ReverseMapping=True,
        StructureRegistrationGroupNames=[ REGISTRATION_NAME ],
        ReferenceExaminationNames = [refName],    ## want to map from the target (planningCT) to the rescan!
        TargetExaminationNames = [targetName]
    )

	
    poiPairs = [(poi, "{}_{}->{}".format(poi,targetName,refName)) for poi in poiList]   # CHANGE THIS IF ReverseMapping=False!!!

	
    if not os.path.isfile(exportFile):
        with open(exportFile,"w") as fp1:
            fp1.write("PatientID, PointName, Original,,,Mapped,,,Error,,,AbsError\n")
            fp1.write(",,X,Y,Z,X,Y,Z,X,Y,Z,,\n")
            
    with open(exportFile,"a") as fp1:
        for poi1, poi2 in poiPairs:
            
            origPoint = case.PatientModel.StructureSets[refName].PoiGeometries[poi1].Point
            mappedPoint = case.PatientModel.StructureSets[refName].PoiGeometries[poi2].Point
            
            diff = {
                "X" : mappedPoint.x - origPoint.x,
                "Y" : mappedPoint.y - origPoint.y,
                "Z" : mappedPoint.z - origPoint.z
            }
            
            absDiff = (diff["X"]**2 + diff["Y"]**2 + diff["Z"]**2) ** 0.5
            
            fp1.write("{},{},{},{},{},{},{},{},{},{},{},{},\n".format(
                patient.PatientID, poi1, 
                origPoint.x, origPoint.y, origPoint.z, 
                mappedPoint.x, mappedPoint.y, mappedPoint.z,
                diff["X"], diff["Y"], diff["Z"], absDiff))
        
#################################################################################
'''

def exportROIDetails(patient=None, case=None, roiList=None, targetName=None, refName=None, exportFile_rois=None):
    if patient is None:
        patient = rsl.get_current("Patient")
    if case is None:
        case = rsl.get_current("Case")
    if roiList is None:
        roiList = DEFAULT_ROILIST
    if targetName is None:
        targetName = DEFAULT_TARGETNAME
    if refName is None:
        refName = DEFAULT_REFNAME
    if exportFile_rois is None:
        exportFile_rois = DEFAULT_EXPORTFILE_ROIS
    
	
	
		
	
	#Make sure all have PrimarShape and Contours
	rois_for_stats = []	
	for roi in roiList:
		try:
			if( len(case.PatientModel.StructureSets[refName].RoiGeometries[roi].PrimaryShape.Contours) > 0
				and case.PatientModel.StructureSets[refName].RoiGeometries[roi+"_"+MAPPED_SUB].PrimaryShape ):
 				rois_for_stats.append( roi )
		except:
			print roi, " not present"
	


    roiPairs = [(roi, "{}_{}".format(roi,MAPPED_SUB) ) for roi in rois_for_stats]


    if not os.path.isfile( exportFile_rois ):
        with open(exportFile_rois,"wt") as fp2:
            fp2.write("PatientID, RoiName, Original volume, Mapped volume, DiceSimilarityCoefficient, Precision, Sensitivity, Specificity, MeanDistanceToAgreement, MaxDistanceToAgreement\n")
    
    sSet = case.PatientModel.StructureSets[refName]
    
    with open(exportFile_rois,"at") as fp2:
        
        for roi1, roi2 in roiPairs:
        
            roiResult = sSet.ComparisonOfRoiGeometries(RoiA=roi1, RoiB=roi2, ComputeDistanceToAgreementMeasures=True)
            
            vol_orig = sSet.RoiGeometries[ roi1 ].GetRoiVolume()
            vol_mapped = sSet.RoiGeometries[ roi2 ].GetRoiVolume()     
            
            fp2.write("{},{},{},{},{},{},{},{},{},{},\n ".format(
                patient.PatientID, 
                roi1, 
                vol_orig, vol_mapped,
                roiResult['DiceSimilarityCoefficient'], 
                roiResult['Precision'],
                roiResult['Sensitivity'],
                roiResult['Specificity'],
                roiResult['MeanDistanceToAgreement'],
                roiResult['MaxDistanceToAgreement']  )  
            )

def main():
    #exportPointDetails()
    exportROIDetails()
    










































