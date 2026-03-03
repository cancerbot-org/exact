from trials.models import *


class LoadBcOptions:
    def load_all(self, skip_hrd=False, skip_hr=True, skip_histologic_types=True):
        if not skip_histologic_types:
            self.load_histologic_types()
        self.load_er_status()
        self.load_pr_status()
        self.load_her2_status()
        if not skip_hr:
            self.load_hr_status()
        if not skip_hrd:
            self.load_hrd_status()

    def load_histologic_types(self):
        data = {
            'infiltrating_ductal_carcinoma': ['Infiltrating ductal carcinoma (IDC)', 10],
            'dcis': ['Ductal carcinoma in situ (DCIS)', 20],
            'infiltrating_lobular_carcinoma': ['Infiltrating lobular carcinoma (ILC)', 30],
            'lcis': ['Lobular carcinoma in situ (LCIS)', 40],
            'mixed_ductal_and_lobular_carcinoma': ['Mixed ductal and lobular carcinoma', 50],
            'mucinous_colloid_carcinoma': ['Mucinous (colloid) carcinoma', 60],
            'tubular_carcinoma': ['Tubular carcinoma', 70],
            'medullary_carcinoma': ['Medullary carcinoma', 80],
            'papillary_carcinoma': ['Papillary carcinoma', 90],
            'metaplastic_carcinoma': ['Metaplastic carcinoma', 100],
            'paget_disease_of_the_nipple': ['Paget disease of the nipple', 110],
            'inflammatory_carcinoma': ['Inflammatory carcinoma', 120],
        }

        HistologicType.objects.all().delete()
        for code in data.keys():
            title, sort_key = data[code]
            HistologicType.objects.update_or_create(code=code, defaults={'title': title, 'sort_key': sort_key})

    def load_er_status(self):
        data = {
            'er_minus': 'ER-',
            'er_plus': 'ER+',
            'er_plus_with_low_exp': 'ER+ with low expression',
            'er_plus_with_hi_exp': 'ER+ with high expression',
        }

        EstrogenReceptorStatus.objects.all().delete()
        for code, title in data.items():
            EstrogenReceptorStatus.objects.update_or_create(code=code, defaults={'title': title})

    def load_pr_status(self):
        data = {
            'pr_minus': 'PR-',
            'pr_plus': 'PR+',
            'pr_plus_with_low_exp': 'PR+ with low expression',
            'pr_plus_with_hi_exp': 'PR+ with high expression',
        }

        ProgesteroneReceptorStatus.objects.all().delete()
        for code, title in data.items():
            ProgesteroneReceptorStatus.objects.update_or_create(code=code, defaults={'title': title})

    def load_her2_status(self):
        data = {
            'her2_plus': 'HER2+',
            'her2_minus': 'HER2-',
            'her2_low': 'HER2 low',
        }

        Her2Status.objects.all().delete()
        for code, title in data.items():
            Her2Status.objects.update_or_create(code=code, defaults={'title': title})

    def load_hrd_status(self):
        data = {
            'hrd_plus': 'HRD+',
            'hrd_minus': 'HRD-',
        }

        HrdStatus.objects.all().delete()
        for code, title in data.items():
            HrdStatus.objects.update_or_create(code=code, defaults={'title': title})

    def load_hr_status(self):
        data = {
            'hr_plus': 'HR+',
            'hr_minus': 'HR-',
            'hr_plus_with_low_exp': "HR+ with low expression",
            'hr_plus_with_hi_exp': "HR+ with high expression",
        }

        HrStatus.objects.all().delete()
        for code, title in data.items():
            HrStatus.objects.update_or_create(code=code, defaults={'title': title})
