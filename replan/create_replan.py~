"""
Create a replan as an adapted plan.

To run type:
    from rmh.plan import create_replan
    create_replan.main()

- Before running this script there must be an approved
  deformable registration with original planning CT as the "target"
  and the new rescan CT as the "reference" image.
  
- Will not allow more than 1 dose escalation, nor a reduction in the
  prescribed dose, but allows any number of replans
  
  TODO: prompt for localisation
  TODO: Add couch
"""

import sys; sys.dont_write_bytecode=True

# import connect as rsl; patient = rsl.get_current("Patient"); case = rsl.get_current("Case"); plan = rsl.get_current("Plan"); beam_set = rsl.get_current("BeamSet"); exam = rsl.get_current("Examination")

import connect as rsl
import os

from rmh.plan import stopOption

from rmh.dialogs import (
    chooseFromList, enterNumber, RmhMessageBox
)

# ---------------------------------- #


ADAPT_PLAN_SUFFIX = "replan"
MACHINE_FOR_OPT = "StrctAgility"
FINAL_MACHINE = "Agility"

NUM_OPTIMIZATIONS = 3
RESCALE_BETWEEN_OPTIMIZATIONS = False
OPT_ITERS_MAX = 60
OPT_TOL = 1E-7
OPT_ITERS_PREP = 7


doseEscalatePrescList = [
    "6890cGy", "7170cGy", "7370cGy"
]

OBJECTIVES_TO_SCALE_WITH_PRESCRIPTION = [
    "PTV_60Gy",
    "PTV_60Gy_ed",
    "PTV_60Gy_rind",
    "ring_60Gy_a",
    "ring_60Gy_b",
    "60Gy_nearParotids",
    #
    "PTV_65Gy",
    "PTV_65Gy_ed",
    "PTV_65Gy_rind",
    "PTV_70Gy",
    "PTV_70Gy_ed",
    "PTV_70Gy_rind",
    "Parotid_R",
    "Parotid_L",
    "Parotids_Superficial",
    "ring_65Gy_a",
    "ring_65Gy_b",
    "par_R-PTVs",
    "par_L-PTVs",
    "65Gy_nearParotids"
]

GOALS_TO_SCALE_WITH_PRESCRIPTION = [
    "PTV_60Gy",
    "PTV_60Gy_ed",
    "PTV_60Gy_rind",
    "ring_60Gy_a",
    "ring_60Gy_b",
    "60Gy_nearParotids", 
    #
    "PTV_65Gy",
    "PTV_65Gy_ed",
    "PTV_65Gy_rind",
    "PTV_70Gy",
    "PTV_70Gy_ed",
    "PTV_70Gy_rind",
    "ring_65Gy_a",
    "ring_65Gy_b",
    "par_R-PTVs",
    "par_L-PTVs",
    "65Gy_nearParotids"
]





def get_background_dose(case, plan, roi_presc):
    """
    Calculate the delivered median dose to roi_presc  
    
    (Background dose before the input plan)
    (Uses the D50% (median) dose of roi_presc for each plan)
    """  
    curr_plan = plan
    background = 0    
 
    #Store starting fractions of each escalation / replan
    start_fractions=[]
    # D50 to PTV_65Gy_ed as dose per fraction
    D50_values = []
    
    # If original plan, we have zero background dose
    if( curr_plan.AdaptionTo is None ):
        background = 0       
    else:  
        searching_plans = True
        while( searching_plans ):
        
            if( curr_plan.AdaptionTo is not None ):                    
                # Store starting fractions of each change                
                start_fractions.append( curr_plan.FractionNumber )
                # Median dose to prescribed roi (per fraction)
                D50 = curr_plan.BeamSets[0].FractionDose.GetDoseAtRelativeVolumes(RoiName=roi_presc, RelativeVolumes=[0.5] )[0]
                # Add to front of list
                D50_values = [D50] + D50_values
                
                prev_plan = curr_plan.AdaptionTo.Name
                curr_plan = case.TreatmentPlans[ prev_plan ]
            else:
                searching_plans = False
                  
            if( curr_plan.FractionNumber == 0 ):
                start_fractions.append( 1 ) #Start fraction of original plan should be 1, NOT 0 as given by FractionNumber field
                D50 = curr_plan.BeamSets[0].FractionDose.GetDoseAtRelativeVolumes(RoiName=roi_presc, RelativeVolumes=[0.5] )[0]
                D50_values = [D50] + D50_values
                searching_plans = False 
        
        # But we don't actually want the dose from the plan input into this method. 
        # We only want background UP TO this plan.
        D50_values.pop()
        
        #print "start_fractions ", start_fractions  
        #print "D50_values ", D50_values
        
        # Use "start_fractions" to find number of fractions at each delivered prescription level
        #   note the order: [0]=at first prescription, [1]=at 2nd, etc.
        fxs_at_dose = []
        for (index,n) in enumerate(start_fractions):
            n_fx = 0 
            if ( index!=len(start_fractions)-1 ):
                n_fx = n - start_fractions[ index+1 ]
                fxs_at_dose = [n_fx] + fxs_at_dose

        #print "fxs at dose ", fxs_at_dose
    
        # Total dose so far delivered is then  sum(fxns_at_dose[j] * doses_per_fx[j] )
        if (  len(fxs_at_dose) == len( D50_values )  ):
            for (index,d) in enumerate( D50_values ):
                background += ( d * fxs_at_dose[index] )             
        else:
            raise AdaptPlanException( "fxs_at_dose and doses_per_fx not same size" )            
       
    return background





def check_new_prescription_valid( case, plan, pres ):
    """ 
    Check that we are not allowing a dose de-escalation, nor a second escalation.
    
    (Both prohibited in the XXX trial)
    """
    curr_plan = plan
    #Store prescribed dose at each replan
    prescriptions=[] 
    prescriptions.append( pres )
    
    searching_plans = True
    while( searching_plans ):    
        if( curr_plan.AdaptionTo is not None ):                  
            # Store prescriptions of each change
            presc = curr_plan.BeamSets[0].Prescription.PrimaryDosePrescription.DoseValue
            prescriptions.append( presc )                    
            
            prev_plan = curr_plan.AdaptionTo.Name
            curr_plan = case.TreatmentPlans[ prev_plan ]
        else:
            searching_plans = False
              
        if( curr_plan.FractionNumber == 0 ):
            presc = curr_plan.BeamSets[0].Prescription.PrimaryDosePrescription.DoseValue
            prescriptions.append( presc )
            searching_plans = False            
            
    if len(prescriptions)>=3:
        for jj in range( len(prescriptions)-2 ):
            if prescriptions[0]!=prescriptions[jj+1]:
                raise AdaptPlanException( "Prescription of all adaptations must be same as the first adaptation" )                   
    
    if len(prescriptions)>1:
        for i in range( len(prescriptions)-1 ):
            if (prescriptions[i] < prescriptions[i+1]):
                raise AdaptPlanException( "Decrease in prescribed dose detected." )



  
def add_HN_MBS( case, exam_name, structure ):
    """ Use MBS to create a mesh (Brain and Mandible) """       
    
    # Note that MBS makes mesh: no Contours but a PrimaryShape       
    roi_color = "255, 255, 255"
    if( structure == "Brain" ):
        roi_color = "255, 255, 0"
    elif( structure == "Mandible" ):
        roi_color = "112, 48, 160"
                
    if( structure not in [roi_geom.OfRoi.Name for roi_geom in case.PatientModel.StructureSets[exam_name].RoiGeometries]  ):
        case.PatientModel.MBSAutoInitializer(  
            MbsRois=[
            { 'CaseType': "HeadNeck", 'ModelName': structure, 'RoiName': structure, 'RoiColor': roi_color }, 
            ], 
            CreateNewRois = True,      #since no ROI exists
            Examination = case.Examinations[ exam_name ], 
            UseAtlasBasedInitialization=True
        )
        # Adapt the mesh (Improves the accuracy? Is once enough?)
        case.PatientModel.AdaptMbsMeshes( 
            Examination=case.Examinations[ exam_name ], RoiNames=[ structure ], CustomStatistics=None, CustomSettings=None        
        ) 
    elif( case.PatientModel.StructureSets[exam_name].RoiGeometries[ structure ].PrimaryShape is None ):
        case.PatientModel.MBSAutoInitializer(  
            MbsRois=[
            { 'CaseType': "HeadNeck", 'ModelName': structure, 'RoiName': structure, 'RoiColor': roi_color }, 
            ], 
            CreateNewRois = False,     #ROI exists but has not contours
            Examination = case.Examinations[ exam_name ], 
            UseAtlasBasedInitialization=True
        )
        # Adapt the mesh (Improves the accuracy? Is once enough?)
        case.PatientModel.AdaptMbsMeshes( 
            Examination=case.Examinations[ exam_name ], RoiNames=[ structure ], CustomStatistics=None, CustomSettings=None        
        )         
    #else: 
    #    s = "structure already exists so don't add/modify anything"



    
def set_objectives_to_beamset( adapted_plan, adapted_beam_set ):
    """ Assign all objectives to the beamset only 
    
    i.e. do not include background dose
    """    
    
    # Want to change RestrictToBeamSet=None to the appropriate BeamSet:
    restrict_to = adapted_beam_set.DicomPlanLabel
  
    constituent_functions = [cf for cf in adapted_plan.PlanOptimizations[0].Objective.ConstituentFunctions ]
    
    for index,cf in enumerate(constituent_functions):
    
        func_type = ""     
        if hasattr( cf.DoseFunctionParameters, 'FunctionType' ):
            func_type = cf.DoseFunctionParameters.FunctionType
        elif hasattr( cf.DoseFunctionParameters, 'LowDoseDistance' ):
            func_type = "DoseFallOff"   # some special case that had no FunctionType attribute in StateTree.
        else:
            raise AdaptPlanException("Unrecognized objective type for objective number {}".format(index))
        
        # RayStation bug. Will not set FunctionType to 'UniformEud'. 
        # See patient 682659, where it fails we actually get 'TargetEud' when recording script
        if func_type=='UniformEud':
            func_type = 'TargetEud'
            print( " --> WARNING: Have changed a UniformEud to TargetEud for objective {}".format(index)  )
     
        adapted_plan.PlanOptimizations[0].EditOptimizationFunction( 
            DoseBasedRoiFunction= cf,
            FunctionType=func_type,  
            RoiName = cf.ForRegionOfInterest.Name, 
            IsConstraint = False, 
            IsRobust = cf.UseRobustness, 
            RestrictToBeamSet = restrict_to 
        )       
    
    
    
    
def set_optimization_params( adapted_plan ):
    """ Set normal clinical H&N optimization parameters """
    adapted_plan.PlanOptimizations[0].OptimizationParameters.Algorithm.MaxNumberOfIterations = OPT_ITERS_MAX
    adapted_plan.PlanOptimizations[0].OptimizationParameters.Algorithm.OptimalityTolerance = OPT_TOL
    adapted_plan.PlanOptimizations[0].OptimizationParameters.DoseCalculation.IterationsInPreparationsPhase = OPT_ITERS_PREP
    # ?? adapted_plan.PlanOptimizations[0].OptimizationParameters.TreatmentSetupSettings[0].BeamSettings[0].ArcConversionPropertiesPerBeam.MaxArcDeliveryTime = 120
    
    
def delete_empty_objectives( case, adapted_plan, adapted_ct_name ):
    """ Remove objectives on empty structures and return a list that were removed """
    
    constituent_functions = [cf for cf in adapted_plan.PlanOptimizations[0].Objective.ConstituentFunctions ]

    list_objs_removed=[]

    for cf in constituent_functions:
        roi_name = cf.ForRegionOfInterest.Name
        roi_volume = 0
        try:
            roi_volume = case.PatientModel.StructureSets[adapted_ct_name].RoiGeometries[roi_name].GetRoiVolume()
        except:
            roi_volume = 0
            
        if roi_volume==0:
            list_objs_removed.append(roi_name)
            cf.DeleteFunction()
    
    return list_objs_removed
    
    

def rederive_rois( case, current_exam ):
    """Re-derive all unapproved rois 
    
    TODO: Is it possible that unapproved CTV may be derived, then edited and not "underived", and this method could alter it?
          Should I just update things without any contours? 
          (This would mean we could NOT edit a GTV and rerun script as PTVs wouldnt be updated)
    TODO: Is the order these are rederived important? (Probably accounted for in order of appearance in template)
    """ 
    
    approved_structs = []
    try:
        structs = case.PatientModel.StructureSets[current_exam.Name].ApprovedStructureSets[0].ApprovedRoiStructures    
        approved_structs = [ st.OfRoi.Name for st in structs ]
    except:
        print " -- CAREFUL: New plan has no ApprovedStructureSets"
        print " --    You may be rederiving modified structures"

    
    # Get list of ROIs to re-derive
    rois_to_rederive = [ 
        roi for roi in case.PatientModel.RegionsOfInterest
        if roi.DerivedRoiExpression is not None
        and roi.Name not in approved_structs
        # AND no countours exist for this Roi?
        and case.PatientModel.StructureSets[current_exam.Name].RoiGeometries[roi.Name].PrimaryShape == None
    ]
    
    print " --    Number of rois being rederived = ", len(rois_to_rederive)
    
    for roi in rois_to_rederive:
        roi.UpdateDerivedGeometry(Examination=current_exam, Algorithm="Auto")
    

    
    
def rescale_objectives(adapted_plan, presc_new, presc_delivered, prev_beamset_presc, fxns_planned_for_previously, remaining_fractions):    
    """ Rescale all objectives for remaining fractions and dose escalation
    
    Boost dose to structures in OBJECTIVES_TO_SCALE_WITH_PRESCRIPTION
    """
    
    constituent_functions = [cf for cf in adapted_plan.PlanOptimizations[0].Objective.ConstituentFunctions ] 
    
    for index,cf in enumerate(constituent_functions):
    
        if( cf.ForRegionOfInterest.Name in OBJECTIVES_TO_SCALE_WITH_PRESCRIPTION ):  
            # Then dose escalation required
            if hasattr( cf.DoseFunctionParameters, 'DoseLevel' ):
                curr_dose_level = cf.DoseFunctionParameters.DoseLevel   
                new_dose =  ( 1.0*curr_dose_level / prev_beamset_presc ) *  ( presc_new - presc_delivered )
                cf.DoseFunctionParameters.DoseLevel = new_dose  
                
            elif hasattr( cf.DoseFunctionParameters, 'HighDoseLevel' ):
                curr_dose_level = cf.DoseFunctionParameters.HighDoseLevel                     
                new_dose =  ( 1.0*curr_dose_level / prev_beamset_presc ) *  ( presc_new - presc_delivered )
                cf.DoseFunctionParameters.HighDoseLevel = new_dose  
                
                if hasattr( cf.DoseFunctionParameters, 'LowDoseLevel' ):
                    curr_dose_level = cf.DoseFunctionParameters.LowDoseLevel                                      
                    new_dose =  ( 1.0*curr_dose_level / prev_beamset_presc ) *  ( presc_new - presc_delivered )
                    cf.DoseFunctionParameters.LowDoseLevel = new_dose  
     
                else:
                    raise AdaptPlanException("Unrecognized objective type for objective number {}".format(index))           
            else:
                raise AdaptPlanException("Unrecognized objective type for objective number {}".format(index))            
                       
        else:               
            # No dose escalation required on these
            if hasattr( cf.DoseFunctionParameters, 'DoseLevel' ):
                curr_dose_level = cf.DoseFunctionParameters.DoseLevel             
                cf.DoseFunctionParameters.DoseLevel = (1.0*curr_dose_level/fxns_planned_for_previously) * remaining_fractions 
                
            elif hasattr( cf.DoseFunctionParameters, 'HighDoseLevel' ):
                curr_dose_level = cf.DoseFunctionParameters.HighDoseLevel             
                cf.DoseFunctionParameters.HighDoseLevel = (1.0*curr_dose_level/fxns_planned_for_previously) * remaining_fractions                 
                
                if hasattr( cf.DoseFunctionParameters, 'LowDoseLevel' ):
                    curr_dose_level = cf.DoseFunctionParameters.LowDoseLevel             
                    cf.DoseFunctionParameters.LowDoseLevel = (1.0*curr_dose_level/fxns_planned_for_previously) * remaining_fractions                    
                
                else:
                    raise AdaptPlanException("Unrecognized objective type for objective number {}".format(index))         
            else:
                raise AdaptPlanException("Unrecognized objective type for objective number {}".format(index))


                

def rescale_goals(adapted_plan, presc_new, presc_delivered, prev_beamset_presc, fxns_planned_for_previously, remaining_fractions):
    """ Rescale all clinical goals for remaining fractions and dose escalation
    
    Boost dose to structures in GOALS_TO_SCALE_WITH_PRESCRIPTION
    """
    
    # Rescale the dose in AcceptanceLevel field
    evaluation_functions = [ ef for ef in adapted_plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions ]
    for ef in evaluation_functions:
    
        if ef.ForRegionOfInterest.Name in GOALS_TO_SCALE_WITH_PRESCRIPTION:
            # Possible dose escalation
            curr_value = ef.PlanningGoal.AcceptanceLevel
            acceptance_level =  ( 1.0*curr_value / prev_beamset_presc ) *  ( presc_new - presc_delivered )
            ef.PlanningGoal.AcceptanceLevel = acceptance_level    
        else: 
            # No escalation to these 
            curr_value = ef.PlanningGoal.AcceptanceLevel
            ef.PlanningGoal.AcceptanceLevel = (1.0*curr_value / fxns_planned_for_previously ) * remaining_fractions    
    
    
    
def add_bolus( case, adapted_beam_set ):
    """ Add standard bolus """
    
    if('PTV_bolus' in [roi.Name for roi in case.PatientModel.RegionsOfInterest ]):
        for bm in adapted_beam_set.Beams:
            bm.SetBolus(BolusName="PTV_bolus")
    else:
        raise AdaptPlanException("No PTV_bolus ROI exists")    



def perform_optimizations( case, adapted_ct_name, adapted_plan, adapted_beam_set, full_ptv_name, presc_new, presc_delivered, remaining_fractions  ):
    """ Perform desired number of optimizations 
    
    Rescale to full pTV between each if RESCALE_BETWEEN_OPTIMIZATIONS
    """

    for ii in range(NUM_OPTIMIZATIONS):
    
        print "  Optimization ", ii+1
        adapted_plan.PlanOptimizations[0].RunOptimization()
        
        if RESCALE_BETWEEN_OPTIMIZATIONS:
        
            print "  Rescaling MU/fx for prescription to full (non _ed) PTV\" "
            if full_ptv_name not in [ geom.OfRoi.Name for geom in case.PatientModel.StructureSets[adapted_ct_name].RoiGeometries ]:
                raise AdaptPlanException("{} does not exist in rescan".format( full_ptv_name ))
            elif ( not case.PatientModel.StructureSets[adapted_ct_name].RoiGeometries[full_ptv_name].HasContours() ):
                raise AdaptPlanException("{} has no volume ".format(full_ptv_name))       
                
            D50_fx = adapted_beam_set.FractionDose.GetDoseAtRelativeVolumes(RoiName=full_ptv_name, RelativeVolumes=[0.5])[0]
            scale_MU =  1.0*( presc_new - presc_delivered ) / ( D50_fx * remaining_fractions )
            
            print "  scale MU by: ", scale_MU
            for bm in adapted_beam_set.Beams:
                bm.BeamMU = bm.BeamMU * scale_MU
                    
            # Check rescaled MUs per segment are ok, revert if not.           # xx does it actually allow me to change it if not feasible?
            if (adapted_beam_set.MachineFeasibilityTest(TreatmentMachineName = MACHINE_FOR_OPT) != ''):
                print("   !!! Beam is infeasible")
                if( "  Minimum MU per arc segment" in adapted_beam_set.MachineFeasibilityTest(TreatmentMachineName = MACHINE_FOR_OPT)  ):
                    print("    !!! Rescaled MUs were not valid; reverting")
                    for bm in adapted_beam_set.Beams:
                        bm.BeamMU = bm.BeamMU / scale_MU
                else:
                    raise AdaptPlanException("Beam infeasible for reason other than MU per segment")                    
  
        
        
def select_treatment_adaptation_tab():
    """ Attempt to move to treatment adaptation tab """
    
    ui = rsl.get_current('ui')
    
    try:
        ui.TitleBar.MenuItem['Treatment Adaptation'].Button_Treatment_Adaptation.Click()
    except SystemError as se:
        if "is not present in the collection" in se.message:
            print("No 'Treatment Adaptation' Title tab")
    try:
        ui.TabControl_Modules.TabItem['Adaptive Replanning'].Button_Adaptive_Replanning.Click()
    except SystemError as se:
        if "is not present in the collection" in se.message:
            print("No 'Adaptive Replanning' tab")       
    # Also bring up scripting tab
    try:
        ui.ToolPanel.TabItem._Scripting.Select()
    except SystemError as se:
        if "is not present in the collection" in se.message:
            print("No 'Scripting' tab in ToolPanel")                
        
 

 
def prompt_machine_change( adapted_beam_set ):
    """ Prompt machine change to Agility 
    
    We have optimized on StrctAgility. Not scriptable.
    """
    
    #Prompt user to change machine from StrctAgility to Agility
    pauseMsg = "Change treatment machine to " + FINAL_MACHINE + " \n\n"
    pauseMsg += "\t1. Click \"OK\" on this message\n"
    pauseMsg += "\t2. Click \"Edit adapted plan\" in Plan Setup \n"
    pauseMsg += "\t3. Change Treatment Machine to \"" + FINAL_MACHINE + "\" \n"
    pauseMsg += "\t4. In Scripting side panel click play icon near bottom of window"
    
    rsl.await_user_input(pauseMsg)
    
    # Warn if machine not changed
    if( adapted_beam_set.MachineReference.MachineName == FINAL_MACHINE):    
        print("Machine changed successfully")
    else:
        m = "Treatment machine not changed to " + FINAL_MACHINE + " \n"
        m = m + "Change machine and perform dose calculation"
        RmhMessageBox.message( m, "CHANGE TREATMENT MACHINE" )
    
     
        
        
        
        
    
# ------------------------------------------------------------------------- #

def makeAdaptedPlan(adapt_from_fx, adapted_ct_name, tot_nr_fx, 
                    newTargetPresc=None, patient=None, case=None, 
                    plan=None, beam_set=None):
    """
    Create new adapted plan, scale objectives and goals, optimize
    with virtual bolus, final dose calculation without bolus
    """
    
    replanName = "{}_{}".format(plan.Name, ADAPT_PLAN_SUFFIX)       
    remaining_fractions = tot_nr_fx - adapt_from_fx + 1 
    
    if patient is None:
        patient = rsl.get_current("Patient")
    if case is None:
        case = rsl.get_current("Case")
    if plan is None:
        plan = rsl.get_current("Plan")
    if beam_set is None:
        beam_set = rsl.get_current("BeamSet")

        
    # Get new target prescription dose 
    prescription = beam_set.Prescription.PrimaryDosePrescription
    newTargetPrescVal = prescription.DoseValue
    if newTargetPresc is not None and "cGy" in newTargetPresc:
        newTargetPrescVal = float(newTargetPresc.strip(" cGy"))
        
    ## Get ROI associated with prescription
    roi_with_prescription = prescription.OnStructure.Name
        

    print("Checking prescription is valid")
    check_new_prescription_valid( case, plan, newTargetPrescVal )
    
    
    print("Checking for constraints")
    for cons_fun in [cf for cf in plan.PlanOptimizations[0].Objective.ConstituentFunctions]:
        if cons_fun.Constraint is True:
            raise AdaptPlanException("Constraints not allowed. See objective number {} on {}".format(index, cons_fun.ForRegionOfInterest.Name))


    print("Creating adapted plan")
    adapted_plan = case.AddNewAdaptivePlan(
        FractionNumber=adapt_from_fx,
        AdaptToPlanName=plan.Name, 
        UseTreatmentDeliveryAsSource=False,
        PlanName= replanName,
        PlannedBy= os.environ["USERNAME"], 
        Comment= "", 
        ExaminationName= adapted_ct_name, 
        AllowDuplicateNames= False
    )
    
    
    print("Creating adapted beamset")      
    adapted_plan.AddNewAdaptedBeamSet(  
        MachineName = MACHINE_FOR_OPT,       
        Name="adpt_beamset",   
        AdaptToRadiationSet = beam_set.DicomPlanLabel,
        RemoveBeams=False, 
        ClearBeamModifiers=True,      
        ExaminationName = adapted_ct_name, 
        Modality = beam_set.Modality, 
        TreatmentTechnique = beam_set.GetTreatmentTechniqueType(),
        PatientPosition = beam_set.PatientPosition, 
        NumberOfFractions = remaining_fractions,
        CreateSetupBeams = False, UseLocalizationPointAsSetupIsocenter = False,
        Comment = "", RbeModelReference=None, 
        EnableDynamicTrackingForVero=False, NewDoseSpecificationPointNames=[],
        NewDoseSpecificationPoints=[]
    )

    
    
    print("Creating adapted beamset prescription")
    adapted_beam_set = adapted_plan.BeamSets[0]           
    adapted_beam_set.AddDosePrescriptionToRoi(
        RoiName = roi_with_prescription,
        DoseVolume=prescription.DoseVolume, 
        PrescriptionType=prescription.PrescriptionType,
        DoseValue = newTargetPrescVal,
        RelativePrescriptionLevel=prescription.RelativePrescriptionLevel,
        AutoScaleDose=False
    )
    

    print("Save and set adapted plan as current")   
    patient.Save()
    adapted_plan.SetCurrent()
    # Change UI display
    ui = rsl.get_current('ui')
    try:
        ui.TitleBar.MenuItem['Plan Optimization'].Button_Plan_Optimization.Click()
    except SystemError as se:
        if "is not present in the collection" in se.message:
            print("No 'Plan Optimization' tab")


    print("Use MBS for Brain and Mandible")
    add_HN_MBS( case, adapted_ct_name, "Brain" )
    add_HN_MBS( case, adapted_ct_name, "Mandible" )
  
    print("Updating all structures")
    rederive_rois( case, case.Examinations[adapted_ct_name] )
    
    print("Loop through objectives and change dose to beam set")
    set_objectives_to_beamset( adapted_plan, adapted_beam_set )
    
    
    
    ################ Variables needed for scaling the objectives and goals #############################   
    presc_new =  newTargetPrescVal
    presc_delivered = get_background_dose(case, adapted_plan, roi_with_prescription )
    print "   - presc_delivered = ", presc_delivered
	 
    # Actual dose from previous beamset is not stored anywhere? 
    # This "prescription" is from the previous plan's beamset
    prev_beamset_presc = prescription.DoseValue - get_background_dose(case, plan, roi_with_prescription )        
    print "   - prev_beamset_presc = ", prev_beamset_presc
        
    #Need this for scaling non-escalated volumes
    start_fx_prev_plan = plan.FractionNumber
    if(start_fx_prev_plan==0):  #RS uses 0 for original plan
        start_fx_prev_plan=1
    fxns_planned_for_previously = tot_nr_fx - start_fx_prev_plan + 1    
    ################################################################################################### 
    
 
    print("Rescaling dose for all objectives")  
    rescale_objectives( adapted_plan, presc_new, presc_delivered, prev_beamset_presc, fxns_planned_for_previously, remaining_fractions )
    
    print("Rescaling dose for all clinical goals")  
    rescale_goals( adapted_plan, presc_new, presc_delivered, prev_beamset_presc, fxns_planned_for_previously, remaining_fractions )
    
    print("Deleting any objectives for ROIs with zero volume in rescan CT")
    # Also store the names of those removed for later
    objectives_removed = delete_empty_objectives( case, adapted_plan, adapted_ct_name )
    
    print("Saving")
    patient.Save()

    print("Adding bolus in for optimizations")
    add_bolus( case, adapted_beam_set )
    
    print("Set standard optimization settings")
    set_optimization_params( adapted_plan )
    
    print("Do optimizations")
    # Want to scale to full, un-edited PTV between optimizations
    full_ptv_name = roi_with_prescription.split("_ed")[0].split("_Ed")[0].split("_ED")[0]   # xx CAREFUL 
    perform_optimizations( case, adapted_ct_name, adapted_plan, adapted_beam_set, full_ptv_name, presc_new, presc_delivered, remaining_fractions  )
    
    print("Saving")
    patient.Save()     
  
    print("Changing UI to Treatment Adaptation tab")
    select_treatment_adaptation_tab()
  
    print("Prompting user to change treatment machine to Agility")
    prompt_machine_change( adapted_beam_set )
    
    print("Removing bolus")
    if('PTV_bolus' in [roi.Name for roi in case.PatientModel.RegionsOfInterest ]):
        for bm in adapted_beam_set.Beams:
            bm.SetBolus(BolusName="")
    else:
        raise AdaptPlanException("No PTV_bolus ROI exists")

        
    print("Dose calculation without bolus")
    adapted_beam_set.ComputeDose(ComputeBeamDoses=True, DoseAlgorithm="CCDose", ForceRecompute=False)
    
    
    print("Calculating dose scaling factor")
    # Without bolus we rescale on the edited ROI, PTV_65Gy_ed
    D50_per_fx = adapted_beam_set.FractionDose.GetDoseAtRelativeVolumes(RoiName=roi_with_prescription, RelativeVolumes=[0.5])[0]
    scale_MU_fact =  1.0*( presc_new - presc_delivered ) / ( D50_per_fx * remaining_fractions )
    print "scale_MU: ", scale_MU_fact

    
    print("Scaling MU/fx in all beams")
    for bm in adapted_beam_set.Beams:
        bm.BeamMU = bm.BeamMU * scale_MU_fact     
    # Check rescaled MUs per segment are ok, revert if not.           
    if (adapted_beam_set.MachineFeasibilityTest(TreatmentMachineName = FINAL_MACHINE) != ''):
        print(" !!! Beam is infeasible")
        if( "Minimum MU per arc segment" in adapted_beam_set.MachineFeasibilityTest(TreatmentMachineName = FINAL_MACHINE)  ):
            print("  !!! Rescaled MUs were not valid after removal of bolus; reverting.\nRecalculate dose.")
            for bm in adapted_beam_set.Beams:
                bm.BeamMU = bm.BeamMU / scale_MU_fact
        else:
            raise AdaptPlanException("Beam infeasible for reason other than MU per segment")



    print("Dose calculation without bolus")
    adapted_beam_set.ComputeDose(ComputeBeamDoses=True, DoseAlgorithm="CCDose", ForceRecompute=False)
    
    
    print("Saving")
    patient.Save()
    


    #Prompt user to change color table for beam set and list any objectives removed
    msg = "\nCheck color table reference value is " + str(presc_new - presc_delivered) + " cGy  \n\n"
    msg=msg + "List of objectives removed:\n" 
    for cf_rm in objectives_removed:
        msg=msg+"\t"+cf_rm+"\n"
    RmhMessageBox.message( msg, 'Change color table reference')
    
    
    
    
    
# ---------------------------------- #

def _find_ReplanCT(case, beam_set):
    """
    Find the name of the replan CT.
    If there is more than one candidate ask user to select it from a list
    """
    planningCT = beam_set.GetPlanningExamination()
    candidateCTs = [
        exam.Name for exam in case.Examinations 
        if exam.GetExaminationDateTime() > planningCT.GetExaminationDateTime()
        and not "Elekta" in exam.EquipmentInfo.ImagingSystemReference.ImagingSystemName
        and exam.EquipmentInfo.Modality == "CT"
    ]
    
    title = "Replan Image"
    prompt = "Choose Image for Replan ..."
    
    if len(candidateCTs) == 0:
        #### TESTING SECOND ADAPT ###
        #candidateCT = 'RescanCT_secondAdapt'
        #candidateCT = 'RescanCT'
        ###########
        raise AdaptPlanException("Case has no CT images acquired after planning CT")
    elif len(candidateCTs) > 1:
        # Add dates to list
        choose_from = []
        for c in candidateCTs:
            date_time = case.Examinations[c].GetExaminationDateTime()
            choose_from.append( c + " ---- " + str(date_time) )
            
        ct_with_date = chooseFromList.getChoiceFromList(choiceList=choose_from, prompt=prompt, title=title)       
        candidateCT = ct_with_date.split("----")[0].strip()          
        #candidateCT = chooseFromList.getChoiceFromList(choiceList=candidateCTs, 
        #                        prompt=prompt, title=title)
    else:
        candidateCT = candidateCTs[0]
        
    return candidateCT
    
# ---------------------------------- #

def _find_adaptionNumFractions(exam, tot_nr_fx):
    """
    Find out what fraction replan is to start on
    """
    if exam.ImportFraction > 0:
        adapt_from_fx = exam.ImportFraction
    else:
        prompt = "Replan will start on fraction ..."
        title = "Replan Fraction Number"
        adapt_from_fx = enterNumber.getValue(prompt=prompt, title=title, 
                                lowBound=0, highBound=tot_nr_fx)
    
    return adapt_from_fx
    
# ---------------------------------- #
        
class AdaptPlanException(Exception):
    """
    Custom exception for creation of adapted plan
    """
    pass

# ---------------------------------- #




    
def main():

    # Offer to continue or abort without saving
    stopOption.giveStopOption( "\n\n\tAPPROVE ALL STRUCTURES BEFORE CONTINUING\n\n\tAny changes will be saved\n\tDo you wish to continue?\n\n\n\tAdd couch before continuing", "        --- WARNING --- ")
    
    patient = rsl.get_current("Patient")
    case = rsl.get_current("Case")
    plan = rsl.get_current("Plan")
    exam = rsl.get_current("Examination")
    beam_set = rsl.get_current("BeamSet")
    
    tot_nr_fx = len([tf for tf in plan.TreatmentCourse.TreatmentFractions])
    adapted_ct_name = _find_ReplanCT(case, beam_set)
    adapt_exam = case.Examinations[adapted_ct_name]
    adapt_from_fx =  _find_adaptionNumFractions(adapt_exam, tot_nr_fx)
    
    prompt = "Select new prescription dose level.\n(Cancel to keep current prescription)"
    title = "Dose Escalation"
    pres = chooseFromList.getChoiceFromList(choiceList=doseEscalatePrescList, 
                                prompt=prompt, title=title)
                                
    
    
    #Make message box summarising all details of replan
    max_arc_deliv = plan.PlanOptimizations[0].OptimizationParameters.TreatmentSetupSettings[0].BeamSettings[0].ArcConversionPropertiesPerBeam.MaxArcDeliveryTime
    p_orig = str( beam_set.Prescription.PrimaryDosePrescription.DoseValue )
    p_new = ""
    if pres is None:
        p_new = p_orig + " cGy"
    else:
        p_new = pres
    msg = 'Creating adapted plan:\n\n'
    msg=msg + "    Adapting plan: "+plan.Name+"\n"
    msg=msg + "    Adapting exam: "+exam.Name+" ("+ str(exam.GetExaminationDateTime()) +  ") to "+adapt_exam.Name+" ("+ str(adapt_exam.GetExaminationDateTime())  +   ")     \n"
    msg=msg + "    Prescription from "+p_orig+" to "+p_new+"\n"
    msg=msg + "    Adapting from fraction "+str( int(adapt_from_fx) )+"\n"
    msg=msg + "    Max arc delivery time = "+str(max_arc_deliv)+" s\n"
    RmhMessageBox.message( msg, 'Please check details')
    
    
    
    makeAdaptedPlan(adapt_from_fx, adapted_ct_name, tot_nr_fx=tot_nr_fx,
                    newTargetPresc=pres, patient=patient, case=case, 
                    plan=plan, beam_set=beam_set)
                    
