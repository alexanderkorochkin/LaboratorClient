import threading
import uuid
from threading import Thread

from kivy.core.window import Window
from kivy.properties import ObjectProperty, ColorProperty, StringProperty
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDIcon
from kivymd.uix.widget import MDWidget

from libs.utils import *
from libs.gardengraph.init import Graph, LinePlot, SmoothLinePlot, PointPlot, ScatterPlot
from libs.opcua.opcuaclient import client
from libs.settings.settingsJSON import *
from libs.variables import DirectVariable, IndirectVariable


class AVGBuffer:
    def __init__(self, _instance):
        self.instance = _instance
        self.buffer = []
        self.avg_buffer = []

    def writeHistory(self, value):
        self.avg_buffer.append(float(value))
        if len(self.avg_buffer) > msettings.get('MAX_HISTORY_VALUES'):
            self.avg_buffer = self.avg_buffer[-msettings.get('MAX_HISTORY_VALUES'):]

    def addValue(self, value):
        self.buffer.append(float(value))
        if len(self.buffer) > self.instance.s['AVG_BUFFER_SIZE']:
            self.buffer = self.buffer[-self.instance.s['AVG_BUFFER_SIZE']:]

    def getLenAVG(self):
        return len(self.buffer)

    def getBuffer(self):
        return self.avg_buffer

    def getAverage(self):
        average = 0
        if len(self.buffer) != 0:
            average = sum(self.buffer)/len(self.buffer)
        self.writeHistory(average)
        return average

    def clear(self):
        self.buffer.clear()
        self.avg_buffer.clear()


class RPoint(MDWidget):
    color = ColorProperty('green')


class GardenGraph(Graph):
    def __init__(self, _graph_instance=None, **kwargs):
        super(GardenGraph, self).__init__(**kwargs)
        self.graph_instance = _graph_instance
        self.size_hint = [1, 1]
        self.pos_hint = None, None
        self.isDeleting = False
        self.draw_border = False
        self.padding = '10dp'

        self.point_value_indicator = None
        self.point_value_indicator_disabled = True

        self.avg_plot = LinePlot()
        self.avg_plot.points = []

        self.intime_plot = LinePlot()
        self.intime_plot.points = []

        self.target_value_plot = LinePlot()
        self.target_value_plot.points = []

        self.plot = LinePlot()
        self.plot.points = []

        self.spectral_plot = LinePlot()
        self.spectral_plot.points = []

        self.point_plot = ScatterPlot()
        self.point_plot.points = []

    def UpdatePlotSettings(self, plot_name='ALL', recombine=True):
        mode = self.graph_instance.s['MODE']
        if mode == 'NORMAL':
            self.xmax = msettings.get('MAX_HISTORY_VALUES') + 1
        if plot_name == 'ALL' or 'AVG':
            if mode == 'NORMAL' and self.graph_instance.s['SHOW_AVG_GRAPH']:
                if recombine:
                    self.remove_plot(self.avg_plot)
                    points_temp = self.avg_plot.points
                    self.avg_plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.accent_light, line_width=self.graph_instance.s['AVG_GRAPH_LINE_THICKNESS'])
                    self.avg_plot.points = points_temp
                self.add_plot(self.avg_plot)
            else:
                self.remove_plot(self.avg_plot)
        if plot_name == 'ALL' or 'INTIME':
            if mode == 'NORMAL' and self.graph_instance.s['SHOW_INTIME_GRAPH']:
                if recombine:
                    self.remove_plot(self.intime_plot)
                    points_temp = self.intime_plot.points
                    self.intime_plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.accent_color, line_width=self.graph_instance.s['INTIME_GRAPH_LINE_THICKNESS'])
                    self.intime_plot.points = points_temp
                self.add_plot(self.intime_plot)
            else:
                self.remove_plot(self.intime_plot)
        if plot_name == 'ALL' or 'TARGET':
            if mode == 'NORMAL' and self.graph_instance.s['SHOW_TARGET_VALUE']:
                if recombine:
                    self.remove_plot(self.target_value_plot)
                    points_temp = self.target_value_plot.points
                    self.target_value_plot = LinePlot(color=(0, 1, 0, 0.8), line_width=1)
                    self.target_value_plot.points = points_temp
                self.add_plot(self.target_value_plot)
            else:
                self.remove_plot(self.target_value_plot)
        if plot_name == 'ALL' or 'MAIN':
            if mode == 'NORMAL' and self.graph_instance.s['SHOW_MAIN_GRAPH']:
                if recombine:
                    self.remove_plot(self.plot)
                    points_temp = self.plot.points
                    self.plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color, line_width=self.graph_instance.s['MAIN_GRAPH_LINE_THICKNESS'])
                    self.plot.points = points_temp
                self.add_plot(self.plot)
            else:
                self.remove_plot(self.plot)
        if plot_name == 'ALL' or 'POINT':
            if mode == 'NORMAL':
                if recombine:
                    self.remove_plot(self.point_plot)
                    points_temp = self.target_value_plot.points
                    self.point_plot = ScatterPlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color, _radius=dp(8))
                    self.target_value_plot.points = points_temp
                self.add_plot(self.point_plot)
            else:
                self.remove_plot(self.point_plot)
        if plot_name == 'ALL' or 'SPECTRAL':
            if mode == 'SPECTRAL':
                if recombine:
                    self.remove_plot(self.spectral_plot)
                    points_temp = self.spectral_plot.points
                    self.spectral_plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color, line_width=self.graph_instance.s['MAIN_GRAPH_LINE_THICKNESS'])
                    self.spectral_plot.points = points_temp
                self.add_plot(self.spectral_plot)
            else:
                self.remove_plot(self.spectral_plot)

    def UpdatePlot(self, plot_name, arr: list):

        if not self.isDeleting and len(arr) > 0:

            self.y_precision = '% 0.' + str(self.graph_instance.s['GRAPH_ROUND_DIGITS']) + 'f'
            self.x_precision = '% 0.' + str(1) + 'f' if self.graph_instance.kivy_instance.main_app.d_type != 'desktop' or len(self.graph_instance.kivy_instance.main_container.GraphArr) > 4 else '% 0.' + str(2) + 'f'
            x_ticks = 5 if self.graph_instance.kivy_instance.main_app.d_type != 'desktop' or len(self.graph_instance.kivy_instance.main_container.GraphArr) > 4 else 10
            y_ticks = 4 if self.graph_instance.kivy_instance.main_app.d_type != 'desktop' or len(self.graph_instance.kivy_instance.main_container.GraphArr) > 4 else 8

            if plot_name == 'AVG':
                temp = []
                for i in range(len(arr)):
                    temp.append((i, arr[i]))
                self.avg_plot.points = temp

            elif plot_name == 'MAIN':
                temp_points = []
                temp_value_arr = []
                for i in range(len(arr)):
                    temp_points.append((i, arr[i][1]))
                for i in range(msettings.get('MAX_HISTORY_VALUES')):
                    temp_value_arr.append((i, arr[-1][1]))
                self.intime_plot.points = temp_value_arr
                self.plot.points = temp_points

                self.xmin = 0
                self.xmax = msettings.get('MAX_HISTORY_VALUES')
                self.x_ticks_major = (self.xmax - self.xmin) / x_ticks

                _yarr = [arr[i][1] for i in range(len(arr))]
                self.ymax = max(_yarr) + (max(_yarr) - min(_yarr)) * (self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] - 1)
                self.ymin = min(_yarr) - (max(_yarr) - min(_yarr)) * (self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] - 1)
                self.y_ticks_major = (self.ymax - self.ymin) / y_ticks
                if self.y_ticks_major == 0:
                    self.ymax = _yarr[0] + 1
                    self.ymin = _yarr[0] - 1
                    self.y_ticks_major = (self.ymax - self.ymin) / y_ticks

                self.add_plot(self.point_plot)
                self.point_plot.points = [(temp_points[-1][0], temp_points[-1][1])]

            elif plot_name == 'SPECTRAL':

                self.remove_plot(self.point_plot)

                temp_points = []
                for i in range(len(arr)):
                    temp_points.append((arr[i][0], arr[i][1]))
                self.spectral_plot.points = temp_points

                self.xmin = 0
                self.xmax = 0.5
                self.x_ticks_major = (self.xmax - self.xmin) / x_ticks

                _yarr = [arr[i][1] for i in range(len(arr))]
                self.ymax = float(max(_yarr) + (max(_yarr) - min(_yarr)) * (self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] - 1))
                self.ymin = 0.
                self.y_ticks_major = (self.ymax - self.ymin) / y_ticks
                if self.y_ticks_major == 0.:
                    self.ymax = 1
                    self.ymin = 0
                    self.y_ticks_major = (self.ymax - self.ymin) / y_ticks

    def ClearPlot(self):
        self.intime_plot.points = []
        self.avg_plot.points = []
        self.plot.points = []
        if self.point_value_indicator:
            self.point_value_indicator.opacity = 0
            self.point_value_indicator = []
            self.point_value_indicator_disabled = True
        self.spectral_plot.points = []


        self.ymax = 1
        self.ymin = 0
        self.xmax = msettings.get('MAX_HISTORY_VALUES') + 1 if self.graph_instance.s['MODE'] == 'NORMAL' else self.xmax
        self.xmin = 0

    def SetDeleting(self):
        self.isDeleting = True


class GraphBox(MDBoxLayout):

    def __init__(self, _kivy_instance, settings=None, **kwargs):
        super().__init__(**kwargs)
        self.WasHold = False
        self.main_value = 0.
        self.avg_value = 0.
        self.target_value = 0.
        self.size_hint = [1, None]
        self.isBadExpression = False
        self.isStartup = True
        self.isChosen = False
        self.accented = False
        self.precached = False

        self.modes = ['NORMAL', 'SPECTRAL']

        self.var = None
        self.gardenGraph = GardenGraph(border_color=[1, 1, 1, 0],
                                       y_ticks_major=0,
                                       y_ticks_minor=0,
                                       x_ticks_major=0,
                                       x_ticks_minor=0,
                                       xlog=False,
                                       ylog=False,
                                       tick_color=[0, 0, 0, 0],
                                       background_color=[1, 1, 1, 0],
                                       y_grid_label=graph_settings_defaults['GRAPH_LABEL_Y'],
                                       x_grid_label=graph_settings_defaults['GRAPH_LABEL_X'],
                                       x_grid=False,
                                       y_grid=False,
                                       xmin=0,
                                       xmax=msettings.get('MAX_HISTORY_VALUES') + 1,
                                       ymin=-1,
                                       ymax=1,
                                       font_size='12sp',
                                       label_options={
                                           'color': _kivy_instance.main_app.theme_cls.accent_color,  # color of tick labels and titles
                                           'bold': False,
                                           'halign': 'center',
                                           'valign': 'middle',
                                       },
                                       _graph_instance=self)

        self.kivy_instance = _kivy_instance
        self.avgBuffer = AVGBuffer(self)

        self.s = DictCallback(graph_settings_defaults.copy(), cls=self, callback=self.on_dict, log=False)

        if settings:
            self.ApplyLayout(settings)
        else:
            self.s['HASH'] = uuid.uuid4().hex

        for key in self.s.keys():
            if key != 'NAME':
                Logger.debug(f'SETTING: [{self.s["NAME"]}]:[{key}] is [{self.s[key]}]')
            else:
                Logger.debug(f'{self.__class__.__name__}: GRAPH [{self.s["NAME"]}] SETTINGS:')

        self.s.log = True

        self.ids.garden_graph_placer.add_widget(self.gardenGraph)
        self.gardenGraph.UpdatePlotSettings()

    def apply_setting(self, tag, settings):
        try:
            self.s[tag] = settings[tag]
        except Exception:
            return

    def apply_with_function(self, tag, settings, function):
        try:
            function(settings[tag])
        except Exception:
            return

    def ApplyLayout(self, settings):

        self.apply_with_function('NAME', settings, self.UpdateName)

        for tag in settings.keys():
            if tag != 'NAME':
                self.apply_setting(tag, settings)

    def on_dict(self, tag, value):
        if tag == 'GRAPH_LABEL_Y':
            self.gardenGraph.y_grid_label = value
        if tag == 'GRAPH_LABEL_X':
            self.gardenGraph.x_grid_label = value
        if tag == 'NAME':
            if value.find('*') != -1:
                self.s['IS_INDIRECT'] = True
            else:
                self.s['IS_INDIRECT'] = False
            self.UpdateNameButton()
        if tag == 'IS_INDIRECT':
            if value:
                self.var = IndirectVariable(client, self.kivy_instance, self)
            else:
                self.var = DirectVariable(client, self.kivy_instance, self, self.s['NAME'])
        if tag == 'MODE':
            if value == 'SPECTRAL':
                self.gardenGraph.tick_color = self.kivy_instance.main_app.theme_cls.accent_color
                self.gardenGraph.x_grid_label = self.s['GRAPH_LABEL_X']
            if value == 'NORMAL':
                self.gardenGraph.tick_color = [0, 0, 0, 0]
                self.gardenGraph.x_grid_label = False
            self.UpdateNameButton()
            self.gardenGraph.UpdatePlotSettings()
        if tag == 'EXPRESSION':
            self.UpdateNameButton()
        if tag == 'TARGET_VALUE':
            temp = []
            for i in range(msettings.get('MAX_HISTORY_VALUES')):
                temp.append((i, value))
            self.gardenGraph.target_value_plot.points = temp
            self.target_value = value
        if tag == 'SHOW_TARGET_VALUE':
            self.target_value = self.s['TARGET_VALUE']
            self.gardenGraph.UpdatePlotSettings('TARGET')

    def Resize(self, target_height):
        self.height = target_height

    def Toggle(self, setting: str, do_clear=False):
        self.s[setting] = not self.s[setting]
        if do_clear:
            self.ClearGraph()

    def DialogGraphSettingsOpen(self):
        self.kivy_instance.UnselectAll(excepted=self)
        self.isChosen = False
        if not self.accented:
            self.AccentIt()
        self.dialogGraphSettings.Open()

    def RemoveMe(self):
        self.gardenGraph.isDeleting = True
        self.kivy_instance.main_container.RemoveGraph(self)

    def isIndirect(self):
        return self.s['IS_INDIRECT']

    def UpdateThread(self):
        if self.s['NAME'] != 'None':
            if not self.isIndirect():
                out = self.var.GetValue()
                if 'ERROR' not in str(out):
                    self.main_value = float(out)
                    if self.isBadExpression:
                        self.isBadExpression = False
                else:
                    if not self.isBadExpression:
                        self.isBadExpression = True
                        Logger.debug(f'GraphUpdate: WARNING! {out}')
            else:
                out = self.var.GetValue(self.s['EXPRESSION'])
                if 'ERROR' not in str(out):
                    self.main_value = float(out)
                    if self.isBadExpression:
                        self.isBadExpression = False
                else:
                    if not self.isBadExpression:
                        self.isBadExpression = True
                        Logger.debug(f'GraphUpdate: WARNING! {out}')

            if not self.isBadExpression:
                self.avgBuffer.addValue(self.main_value)
                self.avg_value = self.avgBuffer.getAverage()

    def UpdateGraph(self):
        if self.s['NAME'] != 'None':
            if not self.isBadExpression:
                if self.s['MODE'] == 'NORMAL':
                    if self.s['SHOW_MAIN_VALUE']:
                        if self.s['SHOW_TARGET_VALUE']:
                            if self.main_value > self.target_value:
                                sign = '>'
                            elif self.main_value < self.target_value:
                                sign = '<'
                            else:
                                sign = '='
                            self.ids.graph_current_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.primary_color) + "]" + str(round(self.main_value, self.s['GRAPH_ROUND_DIGITS'])) + " " + sign + " " + str(self.target_value) + "[/color]"
                        else:
                            self.ids.graph_current_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.primary_color) + "]" + str(round(self.main_value, self.s['GRAPH_ROUND_DIGITS'])) + "[/color]"
                    else:
                        self.ids.graph_current_value.text = ''
                    if self.s['SHOW_AVG_VALUE']:
                        self.ids.graph_avg_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.accent_color) + f"]AVG{self.avgBuffer.getLenAVG()}: " + str(round(self.avg_value, self.s['GRAPH_ROUND_DIGITS'])) + "[/color]"
                    else:
                        self.ids.graph_avg_value.text = ''
                    self.gardenGraph.UpdatePlot('AVG', self.avgBuffer.getBuffer())
                    self.gardenGraph.UpdatePlot('MAIN', self.var.GetHistory())
                elif self.s['MODE'] == 'SPECTRAL':
                    size, spectral, maxes, avg, sigma = self.var.GetSpectral(2)
                    self.gardenGraph.UpdatePlot('SPECTRAL', spectral)
                    self.ids.graph_current_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.primary_color) + "]N: " + str(size) + "[/color]"
                    self.ids.graph_avg_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.accent_color) + "]"
                    end = '\n'
                    for i in range(len(maxes)):
                        self.ids.graph_avg_value.text += f'max{i + 1} = ({str(round_to(maxes[i][0], self.s["GRAPH_ROUND_DIGITS"]))}, {str(round_to(maxes[i][1], self.s["GRAPH_ROUND_DIGITS"]))})' + end
                    self.ids.graph_avg_value.text += f'μ (avg, мат. ожидание) = {round_to(avg, self.s["GRAPH_ROUND_DIGITS"])}' + end
                    self.ids.graph_avg_value.text += f'σ (ср. кв. откл.) = {round_to(sigma, self.s["GRAPH_ROUND_DIGITS"])}'
                    self.ids.graph_avg_value.text += "[/color]"
            else:
                self.ids.graph_current_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.error_color) + "]" + 'ERROR!' + "[/color]"
                self.ids.graph_avg_value.text = ''

            self.isStartup = False

    # Return True if there are not labvar with 'name'
    def CheckCollisionName(self, _name):
        if _name in client.names:
            return False
        else:
            return True

    def UpdateNameButton(self):
        self.ids.graph_name.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.text_color) + "]" + f"{self.s['NAME']}" + "[/color]"
        self.ids.graph_mode.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.text_color) + "]" + f"{self.s['MODE']}" + "[/color]"

    def UpdateName(self, name, _clear_expression=False, _clear_graph=False):
        self.s['NAME'] = name
        if _clear_expression:
            self.s['EXPRESSION'] = ''
        if _clear_graph:
            self.ClearGraph()

    def ClearGraphLow(self):
        if self.var:
            self.var.ClearHistory()
        if self.gardenGraph:
            self.gardenGraph.ClearPlot()
        if self.avgBuffer:
            self.avgBuffer.clear()

    def ClearGraph(self):
        threading.Thread(target=self.ClearGraphLow).start()

    def UnChooseIt(self):
        if self.isChosen:
            self.isChosen = False
            self.UnAccentIt()

    def SwitchChooseIt(self, state):
        if state == 'hold' and not self.kivy_instance.selected:
            if not self.isChosen:
                self.isChosen = True
                self.AccentIt()
                self.kivy_instance.Selected(self)
            else:
                self.isChosen = False
                self.UnAccentIt()
                self.kivy_instance.Unselected(self)
            self.WasHold = True
        elif not self.WasHold:
            if state == 'release' and self.kivy_instance.selected:
                if not self.isChosen:
                    self.isChosen = True
                    self.AccentIt()
                    self.kivy_instance.Selected(self)
                else:
                    self.isChosen = False
                    self.UnAccentIt()
                    self.kivy_instance.Unselected(self)
        else:
            self.WasHold = False

    def AccentIt(self):
        self.accented = True
        color = self.kivy_instance.main_app.theme_cls.accent_color
        color[3] = 0.1
        anim = Animation(md_bg_color=color, duration=0.1) + Animation(line_color=self.kivy_instance.main_app.theme_cls.primary_color, duration=0.1)
        anim.start(self.ids.mdcard_id)
        anim = Animation(padding=[5, 5, 5, 5], duration=0.1)
        anim.start(self)

    def UnAccentIt(self):
        self.accented = False
        anim = Animation(md_bg_color=self.kivy_instance.main_app.theme_cls.bg_light, duration=0.1) + Animation(line_color=[0, 0, 0, 0], duration=0.1)
        anim.start(self.ids.mdcard_id)
        anim = Animation(padding=[0, 0, 0, 0], duration=0.1)
        anim.start(self)

    def ToggleMode(self):
        current_mode_index = self.modes.index(self.s['MODE'])
        new_mode_index = current_mode_index + 1 if current_mode_index < len(self.modes) - 1 else 0
        new_mode = self.modes[new_mode_index]
        self.s['MODE'] = new_mode
        return new_mode

