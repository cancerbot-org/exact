class MarkersMapper:
    def categories(self):
        return {
            "cytogenic": "Cytogenic Markers",
            "molecular": "Molecular Markers",
        }
    def data(self):
        return {
            "del17p13": {
                "name": "Del(17p13) Deletion",
                "description": "Deletion of the TP53 gene on chromosome 17p, associated with poor prognosis and resistance to therapy.",
                "categories": ["Cytogenic Markers", "Molecular Markers"]

            },
            "t414": {
                "name": "t(4;14) Translocation",
                "description": "Translocation involving chromosomes 4 and 14, affecting the FGFR3 and MMSET genes, linked to high-risk disease.",
                "categories": ["Cytogenic Markers"]
            },
            "t1114": {
                "name": "t(11;14) Translocation",
                "description": "Translocation between chromosomes 11 and 14, involving the CCND1 gene, commonly seen in plasma cell leukemia and considered standard or favorable risk.",
                "categories": ["Cytogenic Markers", "Molecular Markers"]
            },
            "t1416": {
                "name": "t(14;16) Translocation",
                "description": "Translocation between chromosomes 14 and 16, involving the MAF gene, associated with poor prognosis.",
                "categories": ["Cytogenic Markers", "Molecular Markers"]
            },
            "1q21Amplification": {
                "name": "1q21 Amplification",
                "description": "Gain of additional copies of chromosome 1q, associated with poor prognosis and treatment resistance.",
                "categories": ["Cytogenic Markers"]
            },
            "hyperdiploidy": {
                "name": "Hyperdiploidy",
                "description": "Presence of multiple chromosomal gains, particularly of odd-numbered chromosomes (e.g., 3, 5, 7, 9, 11, 15, 19, 21), associated with better prognosis.",
                "categories": ["Cytogenic Markers", "Molecular Markers"]
            },
            "chromothripsis": {
                "name": "Chromothripsis",
                "description": "Extensive chromosomal rearrangements caused by a single catastrophic event, linked to aggressive disease and poor outcomes.",
                "categories": ["Cytogenic Markers"]
            },
            "krasMutation": {
                "name": "KRAS Mutation",
                "description": "Mutation in the KRAS gene, often associated with disease progression and targeted by MAPK/ERK pathway inhibitors.",
                "categories": ["Cytogenic Markers", "Molecular Markers"]
            },
            "nrasMutation": {
                "name": "NRAS Mutation",
                "description": "Mutation in the NRAS gene, commonly seen in multiple myeloma and linked to disease progression.",
                "categories": ["Cytogenic Markers", "Molecular Markers"]
            },
            "brafMutation": {
                "name": "BRAF Mutation",
                "description": "Mutation in the BRAF gene, which may indicate responsiveness to targeted therapies like BRAF inhibitors.",
                "categories": ["Cytogenic Markers", "Molecular Markers"]
            },
            "mycRearrangements": {
                "name": "MYC Rearrangements",
                "description": "Structural abnormalities involving the MYC gene, associated with aggressive disease behavior.",
                "categories": ["Cytogenic Markers", "Molecular Markers"]
            },

            "tp53Mutation": {
                "name": "TP53 Mutation",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "t414Fgfr3": {
                "name": "t(4;14) with FGFR3 activation",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "1q21": {
                "name": "+1q (1q21 gain or amplification)",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "ighRearrangements": {
                "name": "IGH Rearrangements",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "cd38Expression": {
                "name": "CD38 Expression",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "bcmaExpression": {
                "name": "BCMA Expression",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "atmOrAtrMutations": {
                "name": "ATM or ATR Mutations",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "notch1or2Mutations": {
                "name": "NOTCH1/NOTCH2 Mutations",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "complexKaryotype": {
                "name": "Complex Karyotype",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "fam46cMutation": {
                "name": "FAM46C Mutation",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "dis3Mutation": {
                "name": "DIS3 Mutation",
                "description": "",
                "categories": ["Molecular Markers"]
            },
            "xbp1Mutation": {
                "name": "XBP1 Mutation",
                "description": "",
                "categories": ["Molecular Markers"]
            },
        }
