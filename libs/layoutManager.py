from libs.settings.settingsJSON import msettings
from kivy.logger import Logger
import json


class LayoutManager:

    def __init__(self, _kivy_instance):
        self.kivy_instance = _kivy_instance

    def LoadLayout(self, *args):
        Logger.debug("LayoutManager: Loading layout from {}".format(msettings.get('LAYOUT_FILE')))
        try:
            with open(msettings.get('LAYOUT_FILE'), 'r') as fp:
                arr = fp.readlines()
                for line in arr:
                    self.kivy_instance.AddGraph(json.loads(line))
        except Exception:
            Logger.debug('LayoutManager: Failed to open Layout File!')

    def SaveLayout(self, *args):
        Logger.debug(f"LayoutManager: Saving layout to {msettings.get('LAYOUT_FILE')}")
        file_to_delete = open(msettings.get('LAYOUT_FILE'), 'w')
        file_to_delete.close()
        isFirst = True
        for graph in self.kivy_instance.main_container.GraphArr:
            with open(msettings.get('LAYOUT_FILE'), 'a') as fp:
                if isFirst:
                    isFirst = False
                else:
                    fp.write('\n')
                json.dump(graph.s, fp)
