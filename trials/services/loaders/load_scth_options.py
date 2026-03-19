from trials.models import *


class LoadScthOptions:
    def load_all(self):
        self.load_data()

    def load_data(self):
        data = {
            "priorSCT": "prior SCT",
            "priorAutologousSCT": "prior autologous SCT",
            "priorAllogeneicSCT": "prior allogeneic SCT",
            "recentSCT": "recent SCT",
            "recentAutologousSCT": "recent autologous SCT",
            "recentAllogeneicSCT": "recent allogeneic SCT",
            "relapsedPostSCT": "relapsed post-SCT",
            "relapsedPostAutologousSCT": "relapsed post-autologous SCT",
            "relapsedPostAllogeneicSCT": "relapsed post-allogeneic SCT",
            "completedTandemSCT": "completed tandem SCT",
            "neverReceivedSCT": "never received SCT",
            "preAutologousSCT": "pre-autologous SCT",
            "preAllogeneicSCT": "pre-allogeneic SCT",
        }

        for code, title in data.items():
            StemCellTransplant.objects.update_or_create(code=code, defaults={'title': title})
