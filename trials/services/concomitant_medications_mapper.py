class ConcomitantMedicationsMapper:
    def diseases(self):
        return {
            "MM": "Multiple myeloma",
            "FL": "Follicular lymphoma",
            "BC": "Breast cancer",
            "CLL": "Chronic lymphocytic leukemia",
        }

    def data(self):
        return {
            "investigational_agents": {
                "name": "Investigational Agents",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "immunosuppressants": {
                "name": "Immunosuppressants",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "corticosteroids": {
                "name": "Corticosteroids (high-dose or chronic use)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "CYP450_Modulators": {
                "name": "CYP450 Modulators",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "QT_Prolonging_Medications": {
                "name": "QT-Prolonging Medications",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "anticoagulants": {
                "name": "Anticoagulants (certain types)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Neurologically_Active_Drugs": {
                "name": "Neurologically Active Drugs",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Antineoplastic_Therapies": {
                "name": "Antineoplastic Therapies (non-protocol)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "HIV_Antiretroviral_Therapy": {
                "name": "HIV Antiretroviral Therapy",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "systemic_corticosteroids_lt_5_mg_day": {
                "name": "systemic corticosteroids (e.g., prednisone) =< 5 mg/day",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "systemic_corticosteroids_gt_5_mg_day": {
                "name": "systemic corticosteroids (e.g., prednisone) > 5 mg/day",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "systemic_corticosteroids_gt_10_mg_day": {
                "name": "systemic corticosteroids (e.g., prednisone) > 10 mg/day",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "systemic_corticosteroids_gt_20_mg_day": {
                "name": "systemic corticosteroids (e.g., prednisone) > 20 mg/day",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "mineralocorticoids": {
                "name": "mineralocorticoids (e.g., fludrocortisone)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "inhaled_corticosteroids": {
                "name": "Inhaled corticosteroids",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "topical_intranasal_corticosteroids": {
                "name": "Topical/intranasal corticosteroids",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Immunoglobulin_Replacement_Therapy": {
                "name": "Immunoglobulin Replacement Therapy",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Chronic_Antiviral_Therapy": {
                "name": "Chronic Antiviral Therapy",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "radiation_therapy": {
                "name": "radiation therapy",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "local_palliative_radiotherapy": {
                "name": "Local palliative radiotherapy",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Strong_CYP450_Modulators": {
                "name": "Strong CYP450 Modulators",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Antibiotics_CYP3A4_Inhibitors": {
                "name": "Antibiotics-CYP3A4 Inhibitors (eg: erythromycin, Clarithromycin)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Antibiotics_CYP3A4_Inducers": {
                "name": "Antibiotics-CYP3A4 Inducers (eg: rifampin, rifabutin, rifapentine)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Antifungals_CYP3A4_Inhibitors": {
                "name": "Antifungals-CYP3A4 Inhibitors (eg: ketoconazole, itraconazole, fluconazole)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "CYP3A4_Inducers": {
                "name": "CYP3A4 Inducers",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Anti_seizure_med_CYP3A4_Inducer": {
                "name": "Anti-seizure med CYP3A4 Inducer (eg: Carbamazepine, phenytoin)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "St_Johns_Wort_herbal_antidepressant_CYP3A4_Inducer": {
                "name": "St. John’s Wort herbal antidepressant-CYP3A4 Inducer",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "CYP3A4_Inhibitors": {
                "name": "CYP3A4 Inhibitors",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Grapefruit_juice_CYP3A4_Inhibitor": {
                "name": "Grapefruit juice CYP3A4 Inhibitor (Other CYP3A4 Inhibitor)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Anticoagulants": {
                "name": "Anticoagulants (eg: Warfarin, heparin)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Supportive_therapy": {
                "name": "Supportive therapy",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Bone_modifying_Agents": {
                "name": "Bone-modifying Agents (e.g., bisphosphonates, denosumab)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Herbal_Supplements": {
                "name": "Herbal Supplements (e.g., Echinacea, Ginseng, Ginkgo biloba, high-dose turmeric)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Growth_factors": {
                "name": "Growth factors (e.g., G-CSF, GM-CSF, erythropoiesis-stimulating agents)",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Aspirin_lt_81mg_daily": {
                "name": "Aspirin =< 81mg daily",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Aspirin_gt_81mg_daily": {
                "name": "Aspirin > 81mg daily",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "Chronic_Opioid_Therapy": {
                "name": "Chronic Opioid Therapy",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },
            "NSAIDs": {
                "name": "NSAIDs",
                "diseases": ["MM", "FL", "BC", "CLL"]
            },

            # MM-specific
            "Other_Anti_Cancer_Agents": {
                "name": "Other Anti-Cancer Agents",
                "diseases": ["MM"]
            },
            "Live_Vaccines": {
                "name": "Live Vaccines",
                "diseases": ["MM", "FL"]
            },
            "Antivirals_and_Antifungals": {
                "name": "Antivirals and Antifungals (Strong CYP Modulators)",
                "diseases": ["MM"]
            },

            # Follicular Lymphoma–specific additions
            "Targeted Therapy": {
                "name": "Targeted Therapy",
                "diseases": ["FL"]
            },
            "radiotherapy": {
                "name": "Radiotherapy",
                "diseases": ["FL"]
            },
            "Concomitant_radiation_therapy": {
                "name": "Concomitant Radiation Therapy",
                "diseases": ["FL"]
            },
            "antibiotics": {
                "name": "Antibiotics",
                "diseases": ["FL"]
            },
            "inactivated_vaccines": {
                "name": "Inactivated Vaccines",
                "diseases": ["FL"]
            },
            "supportive_therapy": {
                "name": "Supportive Therapy",
                "diseases": ["FL"]
            },
            "hormonal_therapy": {
                "name": "Hormonal Therapy",
                "diseases": ["FL"]
            },
            "bisphosphonates": {
                "name": "Bisphosphonates",
                "diseases": ["FL"]
            },

            "Monoclonal_Antibodies_anti_CD20": {
                "name": "Monoclonal Antibodies (e.g., anti-CD20) outside study",
                "diseases": ["FL"]
            },
            "CAR_T_or_Other_Cell_Therapies": {
                "name": "CAR-T or Other Cell Therapies",
                "diseases": ["FL"]
            },

            # Breast Cancer–specific additions
            "Hormonal_Agents_not_in_protocol": {
                "name": "Hormonal Agents (e.g., SERMs, AIs, GnRH analogs) not in protocol",
                "diseases": ["BC"]
            },
            "HER2_targeted_Therapies": {
                "name": "HER2-targeted Therapies (e.g., trastuzumab)",
                "diseases": ["BC"]
            },
            "CDK4_6_Inhibitors": {
                "name": "CDK4/6 Inhibitors (e.g., palbociclib, ribociclib, abemaciclib)",
                "diseases": ["BC"]
            },
            "Estrogen_containing_Medications": {
                "name": "Estrogen-containing Medications (e.g., HRT, contraceptives)",
                "diseases": ["BC"]
            },
            "SERMs": {
                "name": "SERMs (e.g., tamoxifen)",
                "diseases": ["BC"]
            },
            "LHRH_GnRH_agonists": {
                "name": "LHRH/GnRH agonists (e.g., goserelin, leuprolide, Triptorelin, Buserelin)",
                "diseases": ["BC"]
            },

            # General for both
            "Strong_Enzyme_Inducers_Inhibitors_non_CYP450": {
                "name": "Strong Enzyme Inducers/Inhibitors (non-CYP450)",
                "diseases": ["FL", "BC"]
            },
            "Systemic_Antibiotics_Antifungals": {
                "name": "Systemic Antibiotics/Antifungals (if immunosuppressive)",
                "diseases": ["FL", "BC"]
            },
        }
