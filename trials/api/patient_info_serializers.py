from rest_framework import serializers

from trials.models import (
    PatientInfo,
    PatientInfoPreExistingConditionCategory,
    PreExistingConditionCategory,
)


class GeoLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientInfo
        fields = ['longitude', 'latitude']


class PatientInfoSerializer(serializers.ModelSerializer):
    externalId = serializers.CharField(
        source='external_id', required=False, allow_blank=True, allow_null=True
    )

    languagesSkills = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, source='languages_skills'
    )

    # Disease block
    patientAge = serializers.IntegerField(source='patient_age', required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    weight = serializers.FloatField(required=False, allow_null=True)
    weightUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='weight_units')
    height = serializers.FloatField(required=False, allow_null=True)
    heightUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='height_units')
    bmi = serializers.FloatField(required=False, read_only=True, allow_null=True)
    ethnicity = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    systolicBloodPressure = serializers.IntegerField(required=False, allow_null=True, source='systolic_blood_pressure')
    diastolicBloodPressure = serializers.IntegerField(required=False, allow_null=True, source='diastolic_blood_pressure')

    # Location
    country = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    region = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    postalCode = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True, source='postal_code')
    longitude = serializers.FloatField(allow_null=True, required=False)
    latitude = serializers.FloatField(allow_null=True, required=False)
    geolocation = GeoLocationSerializer(source='*', required=False, read_only=True)

    disease = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    stage = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    karnofskyPerformanceScore = serializers.IntegerField(required=False, allow_null=True, source='karnofsky_performance_score')
    ecogPerformanceStatus = serializers.IntegerField(required=False, allow_null=True, source='ecog_performance_status')
    noOtherActiveMalignancies = serializers.BooleanField(required=False, allow_null=True, source='no_other_active_malignancies')
    peripheralNeuropathyGrade = serializers.IntegerField(required=False, allow_null=True, source='peripheral_neuropathy_grade')
    preExistingConditionCategories = serializers.SerializerMethodField()
    noActiveInfectionStatus = serializers.BooleanField(required=False, allow_null=True, source='no_active_infection_status')

    # Myeloma
    cytogenicMarkers = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='cytogenic_markers')
    molecularMarkers = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='molecular_markers')
    stemCellTransplantHistory = serializers.JSONField(required=False, allow_null=True, source='stem_cell_transplant_history')
    plasmaCellLeukemia = serializers.BooleanField(required=False, allow_null=True, source='plasma_cell_leukemia')
    progression = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    measurableDiseaseImwg = serializers.BooleanField(required=False, allow_null=True, source='measurable_disease_imwg')

    # Lymphoma
    gelfCriteriaStatus = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='gelf_criteria_status')
    flipiScore = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='flipi_score')
    flipiScoreOptions = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='flipi_score_options')
    tumorGrade = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='tumor_grade')

    # CLL
    binetStage = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='binet_stage')
    proteinExpressions = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='protein_expressions')
    richterTransformation = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='richter_transformation')
    tumorBurden = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='tumor_burden')
    lymphocyteDoublingTime = serializers.IntegerField(required=False, allow_null=True, source='lymphocyte_doubling_time')
    tp53Disruption = serializers.BooleanField(read_only=True, allow_null=True, source='tp53_disruption')
    measurableDiseaseIwcll = serializers.BooleanField(required=False, allow_null=True, source='measurable_disease_iwcll')
    hepatomegaly = serializers.BooleanField(required=False, allow_null=True)
    autoimmuneCytopeniasRefractoryToSteroids = serializers.BooleanField(required=False, allow_null=True, source='autoimmune_cytopenias_refractory_to_steroids')
    lymphadenopathy = serializers.BooleanField(required=False, allow_null=True)
    largestLymphNodeSize = serializers.FloatField(required=False, allow_null=True, source='largest_lymph_node_size')
    splenomegaly = serializers.BooleanField(required=False, allow_null=True)
    spleenSize = serializers.FloatField(required=False, allow_null=True, source='spleen_size')
    diseaseActivity = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='disease_activity')
    btkInhibitorRefractory = serializers.BooleanField(required=False, allow_null=True, source='btk_inhibitor_refractory')
    bcl2InhibitorRefractory = serializers.BooleanField(required=False, allow_null=True, source='bcl2_inhibitor_refractory')
    absoluteLymphocyteCount = serializers.FloatField(required=False, allow_null=True, source='absolute_lymphocyte_count')
    qtcfValue = serializers.FloatField(required=False, allow_null=True, source='qtcf_value')
    serumBeta2MicroglobulinLevel = serializers.FloatField(required=False, allow_null=True, source='serum_beta2_microglobulin_level')
    clonalBoneMarrowBLymphocytes = serializers.FloatField(required=False, allow_null=True, source='clonal_bone_marrow_b_lymphocytes')
    clonalBLymphocyteCount = serializers.IntegerField(required=False, allow_null=True, source='clonal_b_lymphocyte_count')
    boneMarrowInvolvement = serializers.BooleanField(required=False, allow_null=True, source='bone_marrow_involvement')

    # Treatment
    priorTherapy = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='prior_therapy')
    firstLineTherapy = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='first_line_therapy')
    firstLineDate = serializers.DateField(required=False, allow_null=True, source='first_line_date')
    firstLineOutcome = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='first_line_outcome')
    secondLineTherapy = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='second_line_therapy')
    secondLineDate = serializers.DateField(required=False, allow_null=True, source='second_line_date')
    secondLineOutcome = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='second_line_outcome')
    laterTherapies = serializers.JSONField(required=False, allow_null=True, source='later_therapies')
    laterTherapy = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='later_therapy')
    laterDate = serializers.DateField(required=False, allow_null=True, source='later_date')
    laterOutcome = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='later_outcome')
    supportiveTherapies = serializers.JSONField(required=False, allow_null=True, source='supportive_therapies')
    supportiveTherapyDate = serializers.DateField(required=False, allow_null=True, source='supportive_therapy_date')
    lastTreatment = serializers.DateField(required=False, allow_null=True, source='last_treatment')
    relapseCount = serializers.IntegerField(required=False, allow_null=True, source='relapse_count')
    treatmentRefractoryStatus = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='treatment_refractory_status')

    # Blood
    absoluteNeutrophileCount = serializers.IntegerField(required=False, allow_null=True, source='absolute_neutrophile_count')
    absoluteNeutrophileCountUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='absolute_neutrophile_count_units')
    plateletCount = serializers.IntegerField(required=False, allow_null=True, source='platelet_count')
    plateletCountUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='platelet_count_units')
    whiteBloodCellCount = serializers.IntegerField(required=False, allow_null=True, source='white_blood_cell_count')
    whiteBloodCellCountUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='white_blood_cell_count_units')
    serumCalciumLevel = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, source='serum_calcium_level')
    serumCalciumLevelUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='serum_calcium_level_units')
    creatinineClearanceRate = serializers.IntegerField(required=False, allow_null=True, source='creatinine_clearance_rate')
    serumCreatinineLevel = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, source='serum_creatinine_level')
    serumCreatinineLevelUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='serum_creatinine_level_units')
    hemoglobinLevel = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, source='hemoglobin_level')
    hemoglobinLevelUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='hemoglobin_level_units')
    boneLesions = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='bone_lesions')
    meetsCRAB = serializers.BooleanField(required=False, allow_null=True, source='meets_crab')
    estimatedGlomerularFiltrationRate = serializers.IntegerField(required=False, allow_null=True, source='estimated_glomerular_filtration_rate')
    renalAdequacyStatus = serializers.BooleanField(required=False, allow_null=True, source='renal_adequacy_status')
    liverEnzymeLevelsAst = serializers.IntegerField(required=False, allow_null=True, source='liver_enzyme_levels_ast')
    liverEnzymeLevelsAlt = serializers.IntegerField(required=False, allow_null=True, source='liver_enzyme_levels_alt')
    liverEnzymeLevelsAlp = serializers.IntegerField(required=False, allow_null=True, source='liver_enzyme_levels_alp')
    serumBilirubinLevelTotal = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, source='serum_bilirubin_level_total')
    serumBilirubinLevelTotalUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='serum_bilirubin_level_total_units')
    serumBilirubinLevelDirect = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, source='serum_bilirubin_level_direct')
    serumBilirubinLevelDirectUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='serum_bilirubin_level_direct_units')
    albuminLevel = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, source='albumin_level')
    albuminLevelUnits = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='albumin_level_units')
    kappaFLC = serializers.IntegerField(required=False, allow_null=True, source='kappa_flc')
    lambdaFLC = serializers.IntegerField(required=False, allow_null=True, source='lambda_flc')
    meetsSLIM = serializers.BooleanField(required=False, allow_null=True, source='meets_slim')

    # Labs
    monoclonalProteinSerum = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, source='monoclonal_protein_serum')
    monoclonalProteinUrine = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, source='monoclonal_protein_urine')
    lactateDehydrogenaseLevel = serializers.IntegerField(required=False, allow_null=True, source='lactate_dehydrogenase_level')
    pulmonaryFunctionTestResult = serializers.BooleanField(required=False, allow_null=True, source='pulmonary_function_test_result')
    boneImagingResult = serializers.BooleanField(required=False, allow_null=True, source='bone_imaging_result')
    clonalPlasmaCells = serializers.IntegerField(required=False, allow_null=True, source='clonal_plasma_cells')
    ejectionFraction = serializers.IntegerField(required=False, allow_null=True, source='ejection_fraction')

    # Behavior
    consentCapability = serializers.BooleanField(required=False, allow_null=True, source='consent_capability')
    caregiverAvailabilityStatus = serializers.BooleanField(required=False, allow_null=True, source='caregiver_availability_status')
    contraceptiveUse = serializers.BooleanField(required=False, allow_null=True, source='contraceptive_use')
    noPregnancyOrLactationStatus = serializers.BooleanField(required=False, allow_null=True, source='no_pregnancy_or_lactation_status')
    pregnancyTestResult = serializers.BooleanField(required=False, allow_null=True, source='pregnancy_test_result')
    noMentalHealthDisorderStatus = serializers.BooleanField(required=False, allow_null=True, source='no_mental_health_disorder_status')
    noConcomitantMedicationStatus = serializers.BooleanField(required=False, allow_null=True, source='no_concomitant_medication_status')
    noTobaccoUseStatus = serializers.BooleanField(required=False, allow_null=True, source='no_tobacco_use_status')
    tobaccoUseDetails = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True, source='tobacco_use_details')
    noSubstanceUseStatus = serializers.BooleanField(required=False, allow_null=True, source='no_substance_use_status')
    substanceUseDetails = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True, source='substance_use_details')
    noGeographicExposureRisk = serializers.BooleanField(required=False, allow_null=True, source='no_geographic_exposure_risk')
    geographicExposureRiskDetails = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True, source='geographic_exposure_risk_details')
    concomitantMedications = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True, source='concomitant_medications')
    concomitantMedicationDate = serializers.DateField(required=False, allow_null=True, source='concomitant_medication_date')
    noHivStatus = serializers.BooleanField(required=False, allow_null=True, source='no_hiv_status')
    noHepatitisBStatus = serializers.BooleanField(required=False, allow_null=True, source='no_hepatitis_b_status')
    noHepatitisCStatus = serializers.BooleanField(required=False, allow_null=True, source='no_hepatitis_c_status')

    # Breast cancer
    boneOnlyMetastasisStatus = serializers.BooleanField(required=False, allow_null=True, source='bone_only_metastasis_status')
    menopausalStatus = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='menopausal_status')
    metastaticStatus = serializers.BooleanField(required=False, allow_null=True, source='metastatic_status')
    toxicityGrade = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='toxicity_grade')
    plannedTherapies = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='planned_therapies')
    histologicType = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='histologic_type')
    biopsyGrade = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='biopsy_grade')
    measurableDiseaseByRecistStatus = serializers.BooleanField(required=False, allow_null=True, source='measurable_disease_by_recist_status')
    estrogenReceptorStatus = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='estrogen_receptor_status')
    progesteroneReceptorStatus = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='progesterone_receptor_status')
    her2Status = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='her2_status')
    tnbcStatus = serializers.BooleanField(required=False, allow_null=True, source='tnbc_status')
    hrdStatus = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='hrd_status')
    hrStatus = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='hr_status')
    tumorStage = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='tumor_stage')
    nodesStage = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='nodes_stage')
    distantMetastasisStage = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='distant_metastasis_stage')
    stagingModalities = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='staging_modalities')
    geneticMutations = serializers.JSONField(required=False, allow_null=True, source='genetic_mutations')
    pdL1TumorCels = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='pd_l1_tumor_cels')
    pdL1Assay = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='pd_l1_assay')
    pdL1IcPercentage = serializers.IntegerField(required=False, allow_null=True, source='pd_l1_ic_percentage')
    pdL1CombinedPositiveScore = serializers.IntegerField(required=False, allow_null=True, source='pd_l1_combined_positive_score')
    ki67ProliferationIndex = serializers.IntegerField(required=False, allow_null=True, source='ki67_proliferation_index')

    class Meta:
        model = PatientInfo
        fields = [
            'id',
            'externalId',
            'languagesSkills',
            'patientAge',
            'gender',
            'weight',
            'weightUnits',
            'height',
            'heightUnits',
            'bmi',
            'ethnicity',
            'systolicBloodPressure',
            'diastolicBloodPressure',
            'country',
            'region',
            'postalCode',
            'longitude',
            'latitude',
            'geolocation',
            'disease',
            'stage',
            'karnofskyPerformanceScore',
            'ecogPerformanceStatus',
            'noOtherActiveMalignancies',
            'peripheralNeuropathyGrade',
            'preExistingConditionCategories',
            'noActiveInfectionStatus',
            'cytogenicMarkers',
            'molecularMarkers',
            'stemCellTransplantHistory',
            'plasmaCellLeukemia',
            'progression',
            'measurableDiseaseImwg',
            'gelfCriteriaStatus',
            'flipiScore',
            'flipiScoreOptions',
            'tumorGrade',
            'binetStage',
            'proteinExpressions',
            'richterTransformation',
            'tumorBurden',
            'lymphocyteDoublingTime',
            'tp53Disruption',
            'measurableDiseaseIwcll',
            'hepatomegaly',
            'autoimmuneCytopeniasRefractoryToSteroids',
            'lymphadenopathy',
            'largestLymphNodeSize',
            'splenomegaly',
            'spleenSize',
            'diseaseActivity',
            'btkInhibitorRefractory',
            'bcl2InhibitorRefractory',
            'absoluteLymphocyteCount',
            'qtcfValue',
            'serumBeta2MicroglobulinLevel',
            'clonalBoneMarrowBLymphocytes',
            'clonalBLymphocyteCount',
            'boneMarrowInvolvement',
            'priorTherapy',
            'firstLineTherapy',
            'firstLineDate',
            'firstLineOutcome',
            'secondLineTherapy',
            'secondLineDate',
            'secondLineOutcome',
            'laterTherapies',
            'laterTherapy',
            'laterDate',
            'laterOutcome',
            'supportiveTherapies',
            'supportiveTherapyDate',
            'lastTreatment',
            'relapseCount',
            'treatmentRefractoryStatus',
            'absoluteNeutrophileCount',
            'absoluteNeutrophileCountUnits',
            'plateletCount',
            'plateletCountUnits',
            'whiteBloodCellCount',
            'whiteBloodCellCountUnits',
            'serumCalciumLevel',
            'serumCalciumLevelUnits',
            'creatinineClearanceRate',
            'serumCreatinineLevel',
            'serumCreatinineLevelUnits',
            'hemoglobinLevel',
            'hemoglobinLevelUnits',
            'boneLesions',
            'meetsCRAB',
            'estimatedGlomerularFiltrationRate',
            'renalAdequacyStatus',
            'liverEnzymeLevelsAst',
            'liverEnzymeLevelsAlt',
            'liverEnzymeLevelsAlp',
            'serumBilirubinLevelTotal',
            'serumBilirubinLevelTotalUnits',
            'serumBilirubinLevelDirect',
            'serumBilirubinLevelDirectUnits',
            'albuminLevel',
            'albuminLevelUnits',
            'kappaFLC',
            'lambdaFLC',
            'meetsSLIM',
            'monoclonalProteinSerum',
            'monoclonalProteinUrine',
            'lactateDehydrogenaseLevel',
            'pulmonaryFunctionTestResult',
            'boneImagingResult',
            'clonalPlasmaCells',
            'ejectionFraction',
            'consentCapability',
            'caregiverAvailabilityStatus',
            'contraceptiveUse',
            'noPregnancyOrLactationStatus',
            'pregnancyTestResult',
            'noMentalHealthDisorderStatus',
            'noConcomitantMedicationStatus',
            'noTobaccoUseStatus',
            'tobaccoUseDetails',
            'noSubstanceUseStatus',
            'substanceUseDetails',
            'noGeographicExposureRisk',
            'geographicExposureRiskDetails',
            'concomitantMedications',
            'concomitantMedicationDate',
            'noHivStatus',
            'noHepatitisBStatus',
            'noHepatitisCStatus',
            'boneOnlyMetastasisStatus',
            'menopausalStatus',
            'metastaticStatus',
            'toxicityGrade',
            'plannedTherapies',
            'histologicType',
            'biopsyGrade',
            'measurableDiseaseByRecistStatus',
            'estrogenReceptorStatus',
            'progesteroneReceptorStatus',
            'her2Status',
            'tnbcStatus',
            'hrdStatus',
            'hrStatus',
            'tumorStage',
            'nodesStage',
            'distantMetastasisStage',
            'stagingModalities',
            'geneticMutations',
            'pdL1TumorCels',
            'pdL1Assay',
            'pdL1IcPercentage',
            'pdL1CombinedPositiveScore',
            'ki67ProliferationIndex',
        ]

    def get_preExistingConditionCategories(self, instance: PatientInfo):
        if instance.no_pre_existing_conditions is True:
            return 'none'
        if not instance.pk:
            # stateless in-memory instance
            cats = getattr(instance, '_pre_existing_condition_categories', [])
            return ','.join(c.code for c in cats)
        return ','.join(
            instance.pre_existing_condition_categories.values_list('category__code', flat=True)
        )

    def _handle_pre_existing_conditions(self, data, instance):
        raw = data.pop('preExistingConditionCategories', None)
        if raw is None:
            return

        if raw is None or str(raw) == '':
            codes = []
        elif isinstance(raw, (list, tuple)):
            codes = list(raw)
        else:
            codes = [x.strip() for x in str(raw).split(',')]

        instance.no_pre_existing_conditions = codes == ['none']
        instance.save(update_fields=['no_pre_existing_conditions'])

        instance.pre_existing_condition_categories.all().delete()
        if codes and codes != ['none']:
            cat_map = {
                c.code: c for c in PreExistingConditionCategory.objects.filter(code__in=codes)
            }
            for code in codes:
                if code in cat_map:
                    PatientInfoPreExistingConditionCategory.objects.create(
                        patient_info=instance, category=cat_map[code]
                    )

    def update(self, instance, validated_data):
        pre_existing = self.initial_data.get('preExistingConditionCategories')
        if pre_existing is not None:
            temp_data = {'preExistingConditionCategories': pre_existing}
            self._handle_pre_existing_conditions(temp_data, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
