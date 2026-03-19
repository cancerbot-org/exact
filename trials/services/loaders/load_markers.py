from trials.models import *
from trials.services.markers_mapper import MarkersMapper
from trials.services.therapies_mapper import *


class LoadMarkers:
    def load_all(self):
        # print("\n\n>>>>LoadMarkers.load_all")
        self.load_categories()
        self.load_markers()

    def load_categories(self):
        data = MarkersMapper().categories()

        for code, title in data.items():
            MarkerCategory.objects.update_or_create(code=code, defaults={'title': title})

    def load_markers(self):
        data = MarkersMapper().data()

        for code in data.keys():
            obj = data[code]
            title = obj['name']
            descr = obj['description']

            marker, _ = Marker.objects.update_or_create(code=code, defaults={'title': title, 'description': descr})

            categories = MarkerCategory.objects.filter(title__in=obj['categories'])
            marker.categories.set(categories)
