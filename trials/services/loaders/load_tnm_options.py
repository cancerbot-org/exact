from trials.models import *


class LoadTnmOptions:
    def load_all(self):
        self.load_tumor_stages()
        self.load_nodes_stages()
        self.distant_metastasis_stages()
        self.staging_modalities()

    def load_tumor_stages(self):
        data = {
            'Tx': 'Tx: Primary Tumor, cannot be assessed',
            'T0': 'T0: No tumor evidence',
            'Tis': 'Tis: Non-invasive Carcinoma in situ (DCIS, LCIS, Paget’s without tumor)',
            'T1': 'T1: Invasive Tumor ≤ 2 cm',
            'T1mi': 'T1mi: Invasive Tumor ≤ 0.1 cm',
            'T1a': 'T1a: 0.1 – 0.5 cm',
            'T1b': 'T1b: 0.5 – 1 cm',
            'T1c': 'T1c: 1 – 2 cm',
            'T2': 'T2: Invasive Tumor > 2 – 5 cm',
            'T3': 'T3: Invasive Tumor > 5 cm',
            'T4': 'T4: Invades chest wall or skin, or inflammatory',
            'T4a': 'T4a: Invades chest wall',
            'T4b': 'T4b: Invades skin (may be swelling/ulcer)',
            'T4c': 'T4c: Invades both skin + chest wall',
            'T4d': 'T4d: Inflammatory carcinoma'
        }

        for code, title in data.items():
            TumorStage.objects.update_or_create(code=code.lower(), defaults={'title': title})

    def load_nodes_stages(self):
        data = {
            "NX": "NX: Nodes cannot be assessed (e.g., previously removed)",
            "N0": "N0: No lymph node involvement",
            "N1": "N1: 1–3 axillary lymph nodes or small internal mammary nodes",
            "N1mi": "N1mi: Micrometastasis (0.2–2 mm)",
            "N1a": "N1a: 1–3 axillary nodes (>2 mm)",
            "N1b": "N1b: Cancer cells in internal mammary sentinel nodes",
            "N1c": "N1c: 1–3 axillary nodes + internal mammary sentinel nodes",
            "N2": "N2: 4–9 axillary nodes or internal mammary nodes without axillary nodes",
            "N2a": "N2a: 4–9 axillary nodes (>2 mm)",
            "N2b": "N2b: Internal mammary nodes only (no axillary)",
            "N3": "N3: 10+ axillary, infraclavicular, or supraclavicular nodes; or both axillary + internal mammary",
            "N3a": "N3a: ≥10 axillary nodes (≥2 mm) or infraclavicular",
            "N3b": "N3b: 4–9 Axillary + mammary nodes",
            "N3c": "N3c: Supraclavicular nodes"
        }

        for code, title in data.items():
            NodesStage.objects.update_or_create(code=code.lower(), defaults={'title': title})

    def distant_metastasis_stages(self):
        data = {
            "M0": "M0: No distant metastasis",
            "M0(i_plus)": "M0(i+): No metastasis on scans, but cancer cells found in blood/bone marrow/distant nodes",
            "M1": "M1: Distant metastasis present"
        }

        for code, title in data.items():
            DistantMetastasisStage.objects.update_or_create(code=code.lower(), defaults={'title': title})

    def staging_modalities(self):
        data = {
            'c': 'c → Clinical',
            'p': 'p → Pathological',
            'yp': 'yp → Pathological after neoadjuvant therapy'
        }

        for code, title in data.items():
            StagingModality.objects.update_or_create(code=code.lower(), defaults={'title': title})
