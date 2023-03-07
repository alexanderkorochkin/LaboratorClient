import math
import uuid
from re import split

from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar

from libs.dialogs import DialogGraphSettings
from libs.gardengraph.init import Graph, LinePlot, BarPlot
from libs.opcua.opcuaclient import client
from libs.settings.settingsJSON import *
from libs.variables import DirectVariable, IndirectVariable


def color2hex(color):
    return '#' + ''.join(['{0:02x}'.format(int(x * 255)) for x in color])


def hex2color(s, opacity=-1.0):

    if s.startswith('#'):
        return hex2color(s[1:], opacity)

    value = [int(x, 16) / 255.
             for x in split('([0-9a-f]{2})', s.lower()) if x != '']
    if opacity > 0:
        if len(value) == 3:
            value.append(opacity)
        if len(value) == 4:
            value[3] = opacity
    else:
        if len(value) == 3:
            value.append(1.0)
    return value


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

        self.label = MDLabel(text='FFF', **self.label_options)

    def SetMode(self, mode):
        if mode == 'SPECTRAL':
            self.remove_plot(self.plot)
            self.remove_plot(self.avg_plot)
            self.remove_plot(self.intime_plot)
            self.xmax = self.graph_instance.s['MAX_VARIABLE_BUFFER_SIZE'] / 2 + 1
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

        if arr:
            if plot_name == 'AVG':
                if not self.isDeleting:
                    temp = []
                    for i in range(len(arr)):
                        temp.append([i, arr[i]])
                    self.avg_plot.points = temp

            if plot_name == 'MAIN':
                if not self.isDeleting:
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
                if not self.isDeleting:
                    temp_points = []
                    for i in range(len(arr)):
                        temp_points.append([arr[i][0], arr[i][1]])
                    self.spectral_plot.points = temp_points

                    self.xmin = 0
                    self.xmax = 0.5
                    self.x_ticks_major = (self.xmax - self.xmin) / 5

                    _yarr = [arr[i][1] for i in range(len(arr))]
                    self.ymax = round(((max(_yarr) + min(_yarr)) / 2) + abs(
                        self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] * (
                                    max(_yarr) - ((max(_yarr) + min(_yarr)) / 2))))
                    self.ymin = 0
                    self.y_ticks_major = (self.ymax - self.ymin) / 4
                    if self.y_ticks_major == 0.:
                        self.ymax = 1
                        self.ymin = 0
                        self.y_ticks_major = (self.ymax - self.ymin) / 4

                    # self.label.text = '1'
                    # self.label.texture_update()
                    # self.label.size = self.label.texture_size
                    # half_ts = self.label.texture_size[0] / 2.
                    # self.label.pos_hint = None, None
                    # self.label.size_hint = None, None
                    # self.label.pos = self.label.texture_size[0] / 2., 0
                    # self.remove_widget(self.label)
                    # self.add_widget(self.label)

    def ClearPlot(self, _plot='ALL'):
        self.plot.points = []
        self.avg_plot.points = []
        self.intime_plot.points = []
        self.spectral_plot.points = []
        self.ymax = 1
        self.ymin = 0
        self.xmax = msettings.get('MAX_HISTORY_VALUES') + 1 if self.graph_instance.s['MODE'] == 'NORMAL' else self.graph_instance.s['MAX_VARIABLE_BUFFER_SIZE'] + 1
        self.xmin = 0

    def SetDeleting(self):
        self.isDeleting = True


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
        self.gardenGraph = None
        self.kivy_instance = _kivy_instance
        self.avgBuffer = AVGBuffer(self)
        self.dialogGraphSettings = DialogGraphSettings(self)

        self.MODES = ['NORMAL', 'SPECTRAL']

        self.s = graph_settings_defaults.copy()
        self.s['HASH'] = uuid.uuid4().hex

        if settings is not None:
            self.ApplyLayout(settings)

        self.gardenGraph = GardenGraph(border_color=[1, 1, 1, 0],
                                       y_ticks_major=0,
                                       y_ticks_minor=0,
                                       x_ticks_major=12,
                                       x_ticks_minor=0,
                                       xlog=False,
                                       ylog=False,
                                       tick_color=[0, 0, 0, 0.2],
                                       background_color=[1, 1, 1, 0],
                                       y_grid_label=self.s['GRAPH_LABEL_Y'],
                                       x_grid_label=self.s['GRAPH_LABEL_X'],
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

        self.ids.garden_graph_placer.add_widget(self.gardenGraph)
        self._SetMode(self.s['MODE'])
        self.gardenGraph.TogglePlot()
        self.gardenGraph.SetMode(self.s['MODE'])
        self.gardenGraph.UpdatePlotColor()
        self._UpdateNameButton()

    def ac(self, s, settings):
        if settings[s]:
            self.s[s] = settings[s]

    def acf(self, s, settings, function):
        if settings[s]:
            function(settings[s])

    def acff(self, s, settings, function):
        if settings[s]:
            function(settings)

    def ApplyLayout(self, settings):

        self.acf('NAME', settings, self.UpdateName)
        self.s['MODE'] = settings['MODE']

        self.s['MAX_VARIABLE_BUFFER_SIZE'] = settings['MAX_VARIABLE_BUFFER_SIZE']

        self.s['GRAPH_ADDITIONAL_SPACE_Y'] = settings['GRAPH_ADDITIONAL_SPACE_Y']
        self.s['GRAPH_BUFFER_AVG_SIZE'] = settings['GRAPH_BUFFER_AVG_SIZE']
        self.s['GRAPH_ROUND_DIGITS'] = settings['GRAPH_ROUND_DIGITS']

        self.s['SHOW_MAIN_VALUE'] = settings['SHOW_MAIN_VALUE']
        self.s['SHOW_AVG_VALUE'] = settings['SHOW_AVG_VALUE']

        self.s['SHOW_MAIN_GRAPH'] = settings['SHOW_MAIN_GRAPH']
        self.s['SHOW_AVG_GRAPH'] = settings['SHOW_AVG_GRAPH']
        self.s['SHOW_INTIME_GRAPH'] = settings['SHOW_INTIME_GRAPH']

        self.s['MAIN_GRAPH_COLOR'] = settings['MAIN_GRAPH_COLOR']
        self.s['AVG_COLOR'] = settings['AVG_COLOR']
        self.s['INTIME_GRAPH_COLOR'] = settings['INTIME_GRAPH_COLOR']

        self.s['MAIN_GRAPH_LINE_THICKNESS'] = settings['MAIN_GRAPH_LINE_THICKNESS']
        self.s['AVG_GRAPH_LINE_THICKNESS'] = settings['AVG_GRAPH_LINE_THICKNESS']
        self.s['INTIME_GRAPH_LINE_THICKNESS'] = settings['INTIME_GRAPH_LINE_THICKNESS']

        self.s['AVG_GRAPH_OPACITY'] = settings['AVG_GRAPH_OPACITY']

        self.s['GRAPH_LABEL_X'] = settings['GRAPH_LABEL_X']
        self.s['GRAPH_LABEL_Y'] = settings['GRAPH_LABEL_Y']

        if settings['IS_INDIRECT']:
            self.s['IS_INDIRECT'] = True
            self.var = IndirectVariable(client, self.kivy_instance, self.s['MAX_VARIABLE_BUFFER_SIZE'])
            self.acf('EXPRESSION', settings, self.SetExpression)
        else:
            self.s['IS_INDIRECT'] = False
            self.var = DirectVariable(client, self.kivy_instance, self.s['MAX_VARIABLE_BUFFER_SIZE'], self.s['NAME'])

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

    def SetSpectralBufferSize(self, value):
        self.s['MAX_VARIABLE_BUFFER_SIZE'] = value

    def SetExpression(self, expression):
        self.s['EXPRESSION'] = expression

    def toggle_y_grid_label(self):
        self.Toggle('GRAPH_LABEL_Y')
        self.gardenGraph.y_grid_label = self.s['GRAPH_LABEL_Y']
        return self.s['GRAPH_LABEL_Y']

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
        self._SetMode(self.MODES[good_i])
        return self.s['MODE']

    def SetHeight(self, height):
        self.height = height

    def isIndirect(self):
        if self.s['NAME'].find('*') != -1:
            self.s['IS_INDIRECT'] = True
            return True
        else:
            self.s['IS_INDIRECT'] = False
            return False

    def Toggle(self, setting: str, do_clear=False):
        self.s[setting] = not self.s[setting]
        if do_clear:
            self.ClearGraph()

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
    def CheckCollizionName(self, name):
        for labvar in self.kivy_instance.LabVarArr:
            if labvar.name == name:
                return False
        return True

    def UpdateName(self, name, _clear_expression=True):
        self.s['NAME'] = name
        self._UpdateNameButton()
        self.UpdateVarName(_clear_expression)
        self.ClearGraph()

    def UpdateVarName(self, _clear_expression=True):
        if self.s['NAME'].find('*') != -1:
            self.var = IndirectVariable(client, self.kivy_instance, self.s['MAX_VARIABLE_BUFFER_SIZE'])
            self.s['IS_INDIRECT'] = True
            if _clear_expression:
                self.SetExpression('')
        else:
            self.s['IS_INDIRECT'] = False
            self.var = DirectVariable(client, self.kivy_instance, self.s['MAX_VARIABLE_BUFFER_SIZE'], self.s['NAME'])
            if _clear_expression:
                self.SetExpression('')

    def GetName(self):
        return self.s['NAME']

    def ClearPlot(self):
        if self.gardenGraph:
            self.gardenGraph.ClearPlot()
        if self.avgBuffer:
            self.avgBuffer.Clear()

    def ClearGraph(self):
        if self.var:
            self.var.ClearHistory()
        self.ClearPlot()

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

    def _UpdateNameButton(self):
        self.ids.graph_labvar_name_button.text = f"{self.s['NAME']}:{self.s['MODE']}"

    def _SetMode(self, _mode):
        self.s['MODE'] = _mode
        if _mode == 'SPECTRAL':
            self.gardenGraph.SetMode(_mode)
            self.s['GRAPH_LABEL_X'] = True
            self.gardenGraph.x_grid_label = True
        if _mode == 'NORMAL':
            self.gardenGraph.SetMode(_mode)
            self.s['GRAPH_LABEL_X'] = False
            self.gardenGraph.x_grid_label = False
        self._UpdateNameButton()
