from trials.models import *


class LoadToxicityGradeOptions:
    def load_all(self):
        self.load_data()

    def load_data(self):
        data = {
            '0': 'Grade 0 (None)',
            '1': 'Grade 1 (Mild)',
            '2': 'Grade 2 (Moderate)',
            '3': 'Grade 3 (Severe)',
            '4': 'Grade 4 (Life-Threatening)'
        }

        for code, title in data.items():
            ToxicityGrade.objects.update_or_create(code=int(code), defaults={'title': title})
