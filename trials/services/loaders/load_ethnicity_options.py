import django_countries

from trials.models import *


class LoadEthnicityOptions:
    def load_all(self):
        self.load_data()

    def load_data(self):
        data = {
            'caucasian_or_european': 'Caucasian/European',
            'african_or_black': 'African/Black',
            'asian': 'Asian',
            'native_american': 'Native American',
            'other': "Other/Won't Say",
        }
        for code, title in data.items():
            Ethnicity.objects.update_or_create(code=code, defaults={'title': title})
