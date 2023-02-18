import uuid
import math
from re import split

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.label import Label
from libs.gardengraph.init import Graph, LinePlot, SmoothLinePlot
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.behaviors import BackgroundColorBehavior, CommonElevationBehavior

from libs.dialogs import DialogGraphSettings
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
        self.plot = LinePlot()
        self.plot.points = []
        self.size_hint = [1, 1]
        self.pos_hint = None, None
        self.isDeleting = False
        self.precision = '% 0.' + str(msettings.get('GRAPH_ROUND_DIGITS')) + 'f'
        self.draw_border = False
        self.padding = '10dp'

        self.avg_plot = LinePlot()
        self.avg_plot.points = []

        self.intime_plot = LinePlot()
        self.intime_plot.points = []

        self.TogglePlot()
        self.UpdatePlotColor()

    def TogglePlot(self, plot='ALL'):
        if plot == 'MAIN' or 'ALL':
            self.add_plot(self.plot) if self.graph_instance.s['SHOW_MAIN_GRAPH'] else self.remove_plot(self.plot)
        if plot == 'AVG' or 'ALL':
            self.add_plot(self.avg_plot) if self.graph_instance.s['SHOW_AVG_GRAPH'] else self.remove_plot(self.avg_plot)
        if plot == 'INTIME' or 'ALL':
            self.add_plot(self.intime_plot) if self.graph_instance.s['SHOW_INTIME_GRAPH'] else self.remove_plot(self.intime_plot)

    def UpdatePlotColor(self, plot="ALL"):
        if plot == 'ALL' or plot == 'MAIN':
            self.remove_plot(self.plot)
            points_temp = self.plot.points
            self.plot = LinePlot(color=hex2color(self.graph_instance.s['MAIN_GRAPH_COLOR']), line_width=self.graph_instance.s['MAIN_GRAPH_LINE_THICKNESS'])
            self.plot.points = points_temp
            self.add_plot(self.plot)
        if plot == 'ALL' or plot == 'AVG':
            self.remove_plot(self.avg_plot)
            points_temp = self.avg_plot.points
            self.avg_plot = LinePlot(color=hex2color(self.graph_instance.s['AVG_COLOR'], self.graph_instance.s['AVG_GRAPH_OPACITY']), line_width=self.graph_instance.s['AVG_GRAPH_LINE_THICKNESS'])
            self.avg_plot.points = points_temp
            self.add_plot(self.avg_plot)
        if plot == 'ALL' or plot == 'INTIME':
            self.remove_plot(self.intime_plot)
            points_temp = self.intime_plot.points
            self.intime_plot = LinePlot(color=hex2color(self.graph_instance.s['INTIME_GRAPH_COLOR']), line_width=self.graph_instance.s['INTIME_GRAPH_LINE_THICKNESS'])
            self.intime_plot.points = points_temp
            self.add_plot(self.intime_plot)

    def UpdatePlot(self, main_arr, avg_arr):

        if avg_arr:
            if not self.isDeleting:
                temp = []
                for i in range(len(avg_arr)):
                    temp.append([i, avg_arr[i]])
                self.avg_plot.points = temp

        if main_arr:
            if not self.isDeleting:

                temp_points = []
                temp_value_arr = []
                last_value = main_arr[-1][1]
                for i in range(len(main_arr)):
                    temp_points.append([i, main_arr[i][1]])
                for i in range(msettings.get('MAX_HISTORY_VALUES')):
                    temp_value_arr.append([i, last_value])
                self.plot.points = temp_points
                self.intime_plot.points = temp_value_arr

                _yarr = [main_arr[i][1] for i in range(len(main_arr))]
                self.ymax = round(((max(_yarr) + min(_yarr)) / 2) + abs(self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] * (max(_yarr) - ((max(_yarr) + min(_yarr)) / 2))))
                self.ymin = round(((max(_yarr) + min(_yarr)) / 2) - abs(self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] * (-min(_yarr) + ((max(_yarr) + min(_yarr)) / 2))))
                self.y_ticks_major = (self.ymax - self.ymin)/4
                if self.y_ticks_major == 0:
                    self.ymax = 1
                    self.ymin = -1
                    self.y_ticks_major = (self.ymax - self.ymin) / 4

    def ClearPlot(self, _plot='ALL'):
        self.plot.points = []
        self.avg_plot.points = []
        self.intime_plot.points = []
        self.ymin = 0
        self.ymax = 1
        self.xmin = 0
        self.xmax = msettings.get('MAX_HISTORY_VALUES') + 1

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
        self.kivy_instance = _kivy_instance
        self.avgBuffer = AVGBuffer(self)
        self.dialogGraphSettings = DialogGraphSettings(self)

        self.MODES = ['NORMAL', 'SPECTRAL']

        self.s = {
            'NAME': graph_settings_defaults['NAME'],
            'MODE': graph_settings_defaults['MODE'],

            'GRAPH_ADDITIONAL_SPACE_Y': graph_settings_defaults['GRAPH_ADDITIONAL_SPACE_Y'],
            'GRAPH_BUFFER_AVG_SIZE': graph_settings_defaults['GRAPH_BUFFER_AVG_SIZE'],
            'GRAPH_ROUND_DIGITS': graph_settings_defaults['GRAPH_ROUND_DIGITS'],
            'HASH': uuid.uuid4().hex,

            'SHOW_MAIN_VALUE': graph_settings_defaults['SHOW_MAIN_VALUE'],
            'SHOW_AVG_VALUE': graph_settings_defaults['SHOW_AVG_VALUE'],

            'SHOW_MAIN_GRAPH': graph_settings_defaults['SHOW_MAIN_GRAPH'],
            'SHOW_AVG_GRAPH': graph_settings_defaults['SHOW_AVG_GRAPH'],
            'SHOW_INTIME_GRAPH': graph_settings_defaults['SHOW_INTIME_GRAPH'],

            'MAIN_GRAPH_COLOR': graph_settings_defaults['MAIN_GRAPH_COLOR'],
            'AVG_COLOR': graph_settings_defaults['AVG_COLOR'],
            'INTIME_GRAPH_COLOR': graph_settings_defaults['INTIME_GRAPH_COLOR'],

            'MAIN_GRAPH_LINE_THICKNESS': graph_settings_defaults['MAIN_GRAPH_LINE_THICKNESS'],
            'AVG_GRAPH_LINE_THICKNESS': graph_settings_defaults['AVG_GRAPH_LINE_THICKNESS'],
            'INTIME_GRAPH_LINE_THICKNESS': graph_settings_defaults['INTIME_GRAPH_LINE_THICKNESS'],

            'AVG_GRAPH_OPACITY': graph_settings_defaults['AVG_GRAPH_OPACITY'],

            'GRAPH_LABEL_X': graph_settings_defaults['GRAPH_LABEL_X'],
            'GRAPH_LABEL_Y': graph_settings_defaults['GRAPH_LABEL_Y'],

            'IS_INDIRECT': False,
            'EXPRESSION': 'Empty'
        }

        if settings is not None:
            self.ApplyLayout(settings)

        self.gardenGraph = GardenGraph(border_color=[1, 1, 1, 0],
                                       x_ticks_major=0,
                                       x_ticks_minor=0,
                                       y_ticks_major=0,
                                       y_ticks_minor=0,
                                       tick_color=[1, 1, 1, 0],
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
                                            'halign': 'right',
                                            'valign': 'middle',
                                            },
                                       _graph_instance=self)

        self.ids.garden_graph_placer.add_widget(self.gardenGraph)
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
        self.acf('MODE', settings, self._SetMode)

        self.s['GRAPH_ADDITIONAL_SPACE_Y'] = settings['GRAPH_ADDITIONAL_SPACE_Y']
        self.s['GRAPH_BUFFER_AVG_SIZE'] = settings['GRAPH_BUFFER_AVG_SIZE']
        self.s['GRAPH_ROUND_DIGITS'] = settings['GRAPH_ROUND_DIGITS']

        self.s['SHOW_MAIN_VALUE'] = settings['SHOW_MAIN_GRAPH']
        self.s['SHOW_AVG_VALUE'] = settings['SHOW_MAIN_GRAPH']

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
            self.var = IndirectVariable(client, self.kivy_instance)
            self.acf('EXPRESSION', settings, self.SetExpression)
        else:
            self.s['IS_INDIRECT'] = False
            self.var = DirectVariable(client, self.kivy_instance, self.s['NAME'])

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

    def SetExpression(self, expression):
        self.s['EXPRESSION'] = expression

    def toggle_x_grid_label(self):
        self.Toggle('GRAPH_LABEL_X')
        self.gardenGraph.x_grid_label = self.s['GRAPH_LABEL_X']
        return self.s['GRAPH_LABEL_X']

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
                if self.s['SHOW_MAIN_VALUE']:
                    text = "[color=" + self.s[
                        'MAIN_GRAPH_COLOR'] + "]" + str(self.main_value) + "[/color]"
                if self.s['SHOW_AVG_VALUE']:
                    if text != '':
                        text += ' '
                    text = text + "[color=" + self.s[
                        'AVG_COLOR'] + "]AVG: " + str(self.avg_value) + "[/color]"
                self.ids.graph_main_text.text = text
            else:
                self.ids.graph_main_text.text = "[color=" + color2hex((0.8, 0.3, 0.3)) + "]" + 'BAD EXPRESSION!' + "[/color]"

            self.gardenGraph.UpdatePlot(self.var.GetHistory(), self.avgBuffer.avg_buffer)

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

    def UpdateVarName(self, _clear_expression=True):
        if self.s['NAME'].find('*') != -1:
            self.var = IndirectVariable(client, self.kivy_instance)
            self.s['IS_INDIRECT'] = True
            if _clear_expression:
                self.SetExpression('')
        else:
            self.s['IS_INDIRECT'] = False
            self.var = DirectVariable(client, self.kivy_instance, self.s['NAME'])
            if _clear_expression:
                self.SetExpression('')

    def GetName(self):
        return self.s['NAME']

    def ClearPlot(self):
        self.gardenGraph.ClearPlot()
        self.avgBuffer.Clear()

    def ClearGraph(self, value=None):
        # Очищаем буфер прошлой переменной
        self.var.ClearHistory()
        self.avgBuffer.Clear()
        self.gardenGraph.ClearPlot()

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
        if _mode != 'NORMAL':
            self.kivy_instance.main_app.hide_widget_only(
                self.ids.graph_main_text_holder)
        else:
            self.kivy_instance.main_app.show_widget_only(
                self.ids.graph_main_text_holder)
        self._UpdateNameButton()