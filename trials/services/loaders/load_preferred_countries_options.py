import django_countries

from trials.models import *


class LoadPreferredCountriesOptions:
    def load_all(self):
        self.load_data()

    def load_data(self):
        items = django_countries.countries.countries
        data = {
            'US': [items['US'], 1],
            'GB': [items['GB'], 2],
            'other': ['Other', 150]
        }

        for code in data.keys():
            title, sort_key = data[code]
            PreferredCountry.objects.update_or_create(code=code, defaults={'title': title, 'sort_key': sort_key})
