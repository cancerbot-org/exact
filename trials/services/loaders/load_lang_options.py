from trials.models import *


class LoadLangOptions:
    def load_all(self):
        self.load_languages()
        self.load_language_skill_levels()

    def load_languages(self):
        data = {
            'en': 'English',
            'es': 'Spanish',
            'other': 'Other',
        }

        for code, title in data.items():
            Language.objects.update_or_create(code=code.lower(), defaults={'title': title})

    def load_language_skill_levels(self):
        data = {
            'speak': 'Speak',
            'write': 'Write',
        }

        for code, title in data.items():
            LanguageSkillLevel.objects.update_or_create(code=code.lower(), defaults={'title': title})

