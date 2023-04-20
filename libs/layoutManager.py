from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.spinner import MDSpinner

from libs.settings.settingsJSON import msettings
from kivy.logger import Logger
import json


class LayoutManager:

    def __init__(self, _kivy_instance):
        self.kivy_instance = _kivy_instance
        self.scheduled_save = None
        self.save_time_good = True

    def ReloadLayout(self, *args):
        self.kivy_instance.RemoveAll()
        self.LoadLayout()
        self.kivy_instance.main_app.update_orientation()

    def LoadLayout(self, *args):

        Logger.debug("LayoutManager: Loading layout from {}".format(msettings.get('GRAPHS_LAYOUT_FILE')))
        try:
            with open(msettings.get('GRAPHS_LAYOUT_FILE'), 'r') as fp:
                arr = fp.readlines()
                for line in arr:
                    if line != '':
                        self.kivy_instance.AddGraph(json.loads(line))
        except Exception:
            Logger.debug('LayoutManager: Failed to open Graphs Layout File!')

        Logger.debug("LayoutManager: Loading layout from {}".format(msettings.get('CONTROLS_LAYOUT_FILE')))
        try:
            with open(msettings.get('CONTROLS_LAYOUT_FILE'), 'r') as fp:
                arr = fp.readlines()
                for line in arr:
                    if line != '':
                        self.kivy_instance.AddControls(json.loads(line))
        except Exception:
            Logger.debug('LayoutManager: Failed to open Controls Layout File!')

        if args and args[0] == 'no_cache':
            Logger.debug('LayoutManager: Pre-caching skipped!')
        else:
            self.kivy_instance.PreCacheAll()

    def SaveLayoutLow(self):

        Logger.debug(f"LayoutManager: Saving layout to {msettings.get('GRAPHS_LAYOUT_FILE')}")
        file_to_delete = open(msettings.get('GRAPHS_LAYOUT_FILE'), 'w')
        file_to_delete.close()
        isFirst = True
        for x in self.kivy_instance.main_container.GraphArr:
            with open(msettings.get('GRAPHS_LAYOUT_FILE'), 'a') as fp:
                if isFirst:
                    isFirst = False
                else:
                    fp.write('\n')
                json.dump(x.s, fp)

        Logger.debug(f"LayoutManager: Saving layout to {msettings.get('CONTROLS_LAYOUT_FILE')}")
        file_to_delete = open(msettings.get('CONTROLS_LAYOUT_FILE'), 'w')
        file_to_delete.close()
        isFirst = True
        for x in self.kivy_instance.controlsArray:
            with open(msettings.get('CONTROLS_LAYOUT_FILE'), 'a') as fp:
                if isFirst:
                    isFirst = False
                else:
                    fp.write('\n')
                json.dump(x.s, fp)

    def SaveTimeIsGood(self, *args):
        self.save_time_good = True

    def SaveLayout(self, *args):
        if self.save_time_good:

            self.SaveLayoutLow()

            self.scheduled_save = None
            self.save_time_good = False
            Clock.schedule_once(self.SaveTimeIsGood, msettings.get('SAVE_TIMEOUT_TIME'))
        else:
            if not self.scheduled_save:
                self.scheduled_save = Clock.schedule_once(self.SaveLayout, msettings.get('SAVE_TIMEOUT_TIME'))
