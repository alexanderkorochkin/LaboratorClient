import uuid

from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import Snackbar

from libs.utils import *
from libs.dialogs import DialogGraphSettings
from libs.gardengraph.init import Graph, LinePlot
from libs.opcua.opcuaclient import client
from libs.settings.settingsJSON import *
from libs.variables import DirectVariable, IndirectVariable

from kivy.logger import Logger


class DictCallback(dict):

    graph_instance = None
    isSilent = True

    def __setitem__(self, item, value):
        old_name = self['NAME']
        old_value = self[item]
        super(DictCallback, self).__setitem__(item, value)
        if not self.isSilent:
            if old_value != value:
                Logger.debug(f'GraphDict: [{old_name}]:[{item}] changed to [{value}]')
            else:
                Logger.debug(f'GraphDict: [{old_name}]:[{item}] is still [{value}]')
            self.graph_instance.on_dict(item, value)


class AVGBuffer:
    def __init__(self, _graph_instance):
        self.graph_instance = _graph_instance
        self.isExecuted = True
        self.buffer = []
        self.avg_buffer = []
        self.lastavg = 0

    def CountAVGHistory(self, value):
        if len(self.avg_buffer) == msettings.get('MAX_HISTORY_VALUES'):
            self.avg_buffer = self.avg_buffer[msettings.get('MAX_HISTORY_VALUES') - len(self.avg_buffer) + 1:]
        self.avg_buffer.append(float(value))

    def AddValue(self, value):
        if len(self.buffer) == self.graph_instance.s['GRAPH_BUFFER_AVG_SIZE']:
            self.buffer = self.buffer[self.graph_instance.s['GRAPH_BUFFER_AVG_SIZE'] - len(self.buffer) + 1:]
        self.buffer.append(float(value))

    def GetAVG(self):
        average = 0
        if len(self.buffer) != 0:
            average = round(sum(self.buffer)/len(self.buffer), self.graph_instance.s['GRAPH_ROUND_DIGITS'])
        self.CountAVGHistory(average)
        return average

    def Clear(self):
        self.buffer.clear()
        self.avg_buffer.clear()


class GardenGraph(Graph):
    def __init__(self, _graph_instance=None, **kwargs):
        super().__init__(**kwargs)
        self.graph_instance = _graph_instance
        self.size_hint = [1, 1]
        self.pos_hint = None, None
        self.isDeleting = False
        self.y_precision = '% 0.0' + str(msettings.get('GRAPH_ROUND_DIGITS')) + 'f'
        self.x_precision = '% 0.01f'
        self.draw_border = False
        self.padding = '10dp'

        self.plot = LinePlot()
        self.plot.points = []

        self.avg_plot = LinePlot()
        self.avg_plot.points = []

        self.intime_plot = LinePlot()
        self.intime_plot.points = []

        self.spectral_plot = LinePlot()
        self.spectral_plot.points = []

    def SetMode(self, mode):
        if mode == 'SPECTRAL':
            self.remove_plot(self.plot)
            self.remove_plot(self.avg_plot)
            self.remove_plot(self.intime_plot)
            self.add_plot(self.spectral_plot)
        elif mode == 'NORMAL':
            self.remove_plot(self.spectral_plot)
            self.xmax = msettings.get('MAX_HISTORY_VALUES') + 1
            self.TogglePlot()

    def TogglePlot(self):
        if self.graph_instance.s['MODE'] == 'NORMAL':
            if self.graph_instance.s['SHOW_MAIN_GRAPH']:
                self.add_plot(self.plot)
            else:
                self.remove_plot(self.plot)
            if self.graph_instance.s['SHOW_AVG_GRAPH']:
                self.add_plot(self.avg_plot)
            else:
                self.remove_plot(self.avg_plot)
            if self.graph_instance.s['SHOW_INTIME_GRAPH']:
                self.add_plot(self.intime_plot)
            else:
                self.remove_plot(self.intime_plot)

    def UpdatePlotColor(self, plot_name="ALL"):
        if plot_name == 'ALL' or 'MAIN':
            self.remove_plot(self.plot)
            points_temp = self.plot.points
            self.plot = LinePlot(color=hex2color(self.graph_instance.s['MAIN_GRAPH_COLOR']), line_width=self.graph_instance.s['MAIN_GRAPH_LINE_THICKNESS'])
            self.plot.points = points_temp
            if self.spectral_plot not in self.plots and self.graph_instance.s['SHOW_MAIN_GRAPH']:
                self.add_plot(self.plot)
        if plot_name == 'ALL' or 'AVG':
            self.remove_plot(self.avg_plot)
            points_temp = self.avg_plot.points
            self.avg_plot = LinePlot(color=hex2color(self.graph_instance.s['AVG_COLOR'], self.graph_instance.s['AVG_GRAPH_OPACITY']), line_width=self.graph_instance.s['AVG_GRAPH_LINE_THICKNESS'])
            self.avg_plot.points = points_temp
            if self.spectral_plot not in self.plots and self.graph_instance.s['SHOW_AVG_GRAPH']:
                self.add_plot(self.avg_plot)
        if plot_name == 'ALL' or 'INTIME':
            self.remove_plot(self.intime_plot)
            points_temp = self.intime_plot.points
            self.intime_plot = LinePlot(color=hex2color(self.graph_instance.s['INTIME_GRAPH_COLOR']), line_width=self.graph_instance.s['INTIME_GRAPH_LINE_THICKNESS'])
            self.intime_plot.points = points_temp
            if self.spectral_plot not in self.plots and self.graph_instance.s['SHOW_INTIME_GRAPH']:
                self.add_plot(self.intime_plot)
        if plot_name == 'ALL' or 'SPECTRAL':
            self.remove_plot(self.spectral_plot)
            points_temp = self.spectral_plot.points
            self.spectral_plot = LinePlot(color=hex2color(self.graph_instance.s['MAIN_GRAPH_COLOR']), line_width=self.graph_instance.s['MAIN_GRAPH_LINE_THICKNESS'])
            self.spectral_plot.points = points_temp
            if self.graph_instance.s['MODE'] == 'SPECTRAL':
                self.add_plot(self.spectral_plot)

    def UpdatePlot(self, plot_name, arr: list):

        if arr and not self.isDeleting:
            if plot_name == 'AVG':
                temp = []
                for i in range(len(arr)):
                    temp.append([i, arr[i]])
                self.avg_plot.points = temp

            if plot_name == 'MAIN':
                temp_points = []
                temp_value_arr = []
                last_value = arr[-1][1]
                for i in range(len(arr)):
                    temp_points.append([i, arr[i][1]])
                for i in range(msettings.get('MAX_HISTORY_VALUES')):
                    temp_value_arr.append([i, last_value])
                self.plot.points = temp_points
                self.intime_plot.points = temp_value_arr

                _yarr = [arr[i][1] for i in range(len(arr))]
                self.ymax = round(((max(_yarr) + min(_yarr)) / 2) + abs(self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] * (max(_yarr) - ((max(_yarr) + min(_yarr)) / 2))))
                self.ymin = round(((max(_yarr) + min(_yarr)) / 2) - abs(self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] * (-min(_yarr) + ((max(_yarr) + min(_yarr)) / 2))))
                self.y_ticks_major = (self.ymax - self.ymin)/4
                if self.y_ticks_major == 0:
                    self.ymax = 1
                    self.ymin = -1
                    self.y_ticks_major = (self.ymax - self.ymin) / 4

            if plot_name == 'SPECTRAL':
                temp_points = []
                for i in range(len(arr)):
                    temp_points.append([arr[i][0], arr[i][1]])
                self.spectral_plot.points = temp_points

                self.xmin = 0
                self.xmax = 0.5
                self.x_ticks_major = (self.xmax - self.xmin) / 5

                _yarr = [arr[i][1] for i in range(len(arr))]
                self.ymax = round(((max(_yarr) + min(_yarr)) / 2) + abs(self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] * (max(_yarr) - ((max(_yarr) + min(_yarr)) / 2))))
                self.ymin = 0
                self.y_ticks_major = (self.ymax - self.ymin) / 4
                if self.y_ticks_major == 0.:
                    self.ymax = 1
                    self.ymin = 0
                    self.y_ticks_major = (self.ymax - self.ymin) / 4

    def ClearPlot(self, _plot='ALL'):
        self.plot.points = []
        self.avg_plot.points = []
        self.intime_plot.points = []
        self.spectral_plot.points = []
        self.ymax = 1
        self.ymin = 0
        self.xmax = msettings.get('MAX_HISTORY_VALUES') + 1 if self.graph_instance.s['MODE'] == 'NORMAL' else self.xmax
        self.xmin = 0

    def SetDeleting(self):
        self.isDeleting = True


class GraphBox(MDBoxLayout):

    graph_main_text_color = ObjectProperty([1, 1, 1, 0.0])

    def __init__(self, _kivy_instance, settings=None, **kwargs):
        super().__init__(**kwargs)
        self.WasHold = False
        self.main_value = 0.
        self.avg_value = 0.
        self.size_hint = [1, None]
        self.isBadExpression = False
        self.isStartup = True
        self.isChosen = False

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
                                       y_grid_label=False,
                                       x_grid_label=False,
                                       x_grid=False,
                                       y_grid=False,
                                       xmin=0,
                                       xmax=msettings.get('MAX_HISTORY_VALUES') + 1,
                                       ymin=-1,
                                       ymax=1,
                                       font_size='12sp',
                                       label_options={
                                           'color': '#FFFFFF',  # color of tick labels and titles
                                           'bold': False,
                                           'halign': 'center',
                                           'valign': 'middle',
                                       },
                                       _graph_instance=self)

        self.kivy_instance = _kivy_instance
        self.avgBuffer = AVGBuffer(self)
        self.dialogGraphSettings = DialogGraphSettings(self)

        self.MODES = ['NORMAL', 'SPECTRAL']

        self.s = DictCallback(graph_settings_defaults.copy())
        self.s.graph_instance = self
        self.s.isSilent = False
        self.s['HASH'] = uuid.uuid4().hex

        if settings:
            self.ApplyLayout(settings)

        self.ids.garden_graph_placer.add_widget(self.gardenGraph)
        self.gardenGraph.TogglePlot()
        self.gardenGraph.UpdatePlotColor()

    def apply_setting(self, tag, settings):
        if settings[tag]:
            self.s[tag] = settings[tag]

    def apply_with_function(self, tag, settings, function):
        if settings[tag]:
            function(settings[tag])

    def ApplyLayout(self, settings):

        self.apply_with_function('NAME', settings, self.UpdateName)

        for tag in settings.keys():
            if tag not in ('NAME',):
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
                self.var = IndirectVariable(client, self.kivy_instance, self.s['MAX_SPECTRAL_BUFFER_SIZE'])
            else:
                self.var = DirectVariable(client, self.kivy_instance, self.s['MAX_SPECTRAL_BUFFER_SIZE'], self.s['NAME'])
        if tag == 'MODE':
            if value == 'SPECTRAL':
                self.gardenGraph.tick_color = [0, 0, 0, 0.2]
                self.gardenGraph.SetMode(value)
                self.gardenGraph.x_grid_label = self.s['GRAPH_LABEL_X']
            if value == 'NORMAL':
                self.gardenGraph.tick_color = [0, 0, 0, 0]
                self.gardenGraph.SetMode(value)
                self.gardenGraph.x_grid_label = False
            self.UpdateNameButton()
        if tag == 'EXPRESSION':
            self.UpdateNameButton()

    def Resize(self, d_ori, d_type):
        number_graphs = len(self.kivy_instance.main_container.GraphArr)
        if d_ori == 'horizontal':
            if number_graphs == 1:
                self.height = self.kivy_instance.main_container.height
            elif number_graphs == 2 or number_graphs == 3 or number_graphs == 4:
                self.height = (1 / 2) * (self.kivy_instance.main_container.height - 1 * PADDING)
            else:
                if d_type == 'desktop':
                    self.height = (1 / msettings.get('ROW_HD')) * (self.kivy_instance.main_container.height - (msettings.get('ROW_HD') - 1) * PADDING)
                if d_type == 'tablet':
                    self.height = (1 / msettings.get('ROW_HT')) * (self.kivy_instance.main_container.height - (msettings.get('ROW_HT') - 1) * PADDING)
                if d_type == 'mobile':
                    self.height = (1 / msettings.get('ROW_HM')) * (self.kivy_instance.main_container.height - (msettings.get('ROW_HM') - 1) * PADDING)
        elif d_ori == 'vertical':
            if d_type == 'desktop':
                self.height = (1 / msettings.get('ROW_VD')) * (self.kivy_instance.main_container.height - (msettings.get('ROW_VD') - 1) * PADDING)
            if d_type == 'tablet':
                self.height = (1 / msettings.get('ROW_VT')) * (self.kivy_instance.main_container.height - (msettings.get('ROW_VT') - 1) * PADDING)
            if d_type == 'mobile':
                self.height = (1 / msettings.get('ROW_VM')) * (self.kivy_instance.main_container.height - (msettings.get('ROW_VM') - 1) * PADDING)

    def Toggle(self, setting: str, do_clear=False):
        self.s[setting] = not self.s[setting]
        if do_clear:
            self.ClearGraph()

    def DialogGraphSettingsOpen(self):
        self.dialogGraphSettings.Open()

    def RemoveMe(self):
        self.kivy_instance.main_container.RemoveGraphByHASH(self.s['HASH'])

    def NextMode(self):
        i = 0
        good_i = -1
        for mode in self.MODES:
            if mode == self.s['MODE']:
                good_i = i
            i += 1
        if good_i == len(self.MODES) - 1:
            good_i = 0
        else:
            good_i += 1
        self.s['MODE'] = self.MODES[good_i]
        return self.s['MODE']

    def isIndirect(self):
        return self.s['IS_INDIRECT']

    def Update(self):
        if self.s['NAME'] != 'None':
            if not self.isIndirect():
                self.main_value = round(self.var.GetValue(), self.s['GRAPH_ROUND_DIGITS'])
                if self.isBadExpression and self.main_value:
                    self.isBadExpression = False
            else:
                temp_value = self.var.GetValue(self.s['EXPRESSION'])
                if type(temp_value) is not str:
                    self.main_value = round(temp_value, self.s['GRAPH_ROUND_DIGITS'])
                    if self.isBadExpression:
                        self.isBadExpression = False
                else:
                    if not self.isBadExpression:
                        self.isBadExpression = True
                        snackBar = Snackbar(
                            text=f"[{self.s['NAME']}]: Неверное имя аргумента: {temp_value}!",
                            snackbar_x="10sp",
                            snackbar_y="10sp",
                        )
                        snackBar.size_hint_x = (Window.width - (snackBar.snackbar_x * 2)) / Window.width
                        snackBar.open()

            if not self.isBadExpression:

                self.avgBuffer.AddValue(self.main_value)
                self.avg_value = self.avgBuffer.GetAVG()

                text = ''
                if self.s['MODE'] == 'NORMAL':
                    if self.s['SHOW_MAIN_VALUE']:
                        text = "[color=" + self.s['MAIN_GRAPH_COLOR'] + "]" + str(self.main_value) + "[/color]"
                    if self.s['SHOW_AVG_VALUE']:
                        if text != '':
                            text += ' '
                        text = text + "[color=" + self.s['AVG_COLOR'] + "]AVG: " + str(self.avg_value) + "[/color]"
                else:
                    text = "[color=" + self.s['MAIN_GRAPH_COLOR'] + "]" + str(len(self.var.values_history)) + "[/color]"
                self.ids.graph_main_text.text = text

                if self.s['MODE'] == 'NORMAL':
                    self.gardenGraph.UpdatePlot('MAIN', self.var.GetHistory())
                    self.gardenGraph.UpdatePlot('AVG', self.avgBuffer.avg_buffer)
                elif self.s['MODE'] == 'SPECTRAL':
                    self.gardenGraph.UpdatePlot('SPECTRAL', self.var.GetSpectral())

            else:
                self.ids.graph_main_text.text = "[color=" + color2hex((0.8, 0.3, 0.3)) + "]" + 'BAD EXPRESSION!' + "[/color]"

            if self.s['SHOW_MAIN_VALUE'] or self.s['SHOW_AVG_VALUE']:
                self.graph_main_text_color = [0, 0, 0, 0.2]
            if self.isStartup:
                self.graph_main_text_color = [0, 0, 0, 0.2]

            self.isStartup = False

    # Return True if there are not labvar with 'name'
    def CheckCollisionName(self, name):
        for labvar in self.kivy_instance.LabVarArr:
            if labvar.name == name:
                return False
        return True

    def UpdateNameButton(self):
        if self.s['IS_INDIRECT']:
            self.ids.graph_labvar_name_button.text = f"{self.s['NAME']}:{truncate_string(self.s['EXPRESSION'], 20)}:{self.s['MODE']}"
        else:
            self.ids.graph_labvar_name_button.text = f"{self.s['NAME']}:{self.s['MODE']}"

    def UpdateName(self, name, _clear_expression=False, _clear_graph=False):
        self.s['NAME'] = name
        if _clear_expression:
            self.s['EXPRESSION'] = ''
        if _clear_graph:
            self.ClearGraph()

    def ClearGraph(self):
        if self.var:
            self.var.ClearHistory()
        if self.gardenGraph:
            self.gardenGraph.ClearPlot()
        if self.avgBuffer:
            self.avgBuffer.Clear()

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
        self.ids.mdcard_id.md_bg_color = self.kivy_instance.main_app.theme_cls.primary_color

    def UnAccentIt(self):
        self.ids.mdcard_id.md_bg_color = self.kivy_instance.main_app.theme_cls.accent_color
