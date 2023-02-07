import uuid

from kivy.core.window import Window
from kivy_garden.graph import Graph, LinePlot
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import Snackbar
from kivy.utils import get_hex_from_color as get_hex

from libs.dialogs import DialogGraphSettings
from libs.opcua.opcuaclient import client
from libs.settings.settingsJSON import *
from libs.variables import DirectVariable, IndirectVariable


class GardenGraph(Graph):
    def __init__(self, _graph_instance=None, **kwargs):
        super().__init__(**kwargs)
        self.graph_instance = _graph_instance
        self.plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color, line_width=self.graph_instance.s['GRAPH_LINE_THICKNESS'])
        self.plot.points = []
        self.add_plot(self.plot)
        self.size_hint = [1, 1]
        self.padding = 0
        self.pos_hint = None, None
        self.isDeleting = False

    def UpdatePlot(self, _arr):
        if _arr:
            if not self.isDeleting:
                temp = []
                for i in range(len(_arr)):
                    temp.append([i, _arr[i][1]])
                self.plot.points = temp

                _yarr = [_arr[i][1] for i in range(len(_arr))]
                self.ymax = round(((max(_yarr) + min(_yarr)) / 2) + abs(self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] * (max(_yarr) - ((max(_yarr) + min(_yarr)) / 2))))
                self.ymin = round(((max(_yarr) + min(_yarr)) / 2) - abs(self.graph_instance.s['GRAPH_ADDITIONAL_SPACE_Y'] * (-min(_yarr) + ((max(_yarr) + min(_yarr)) / 2))))
                self.y_ticks_major = (self.ymax - self.ymin)/4
                if self.y_ticks_major == 0:
                    self.ymax = 1
                    self.ymin = -1
                    self.y_ticks_major = (self.ymax - self.ymin) / 4

    def ClearPlot(self):
        self.plot.points = [(0, 0)]
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
        self.lastavg = 0

    def AddValue(self, value):
        if len(self.buffer) == self.graph_instance.s['GRAPH_BUFFER_AVG_SIZE']:
            self.buffer = self.buffer[self.graph_instance.s['GRAPH_BUFFER_AVG_SIZE'] - len(self.buffer) + 1:]
        self.buffer.append(float(value))

    def GetAVG(self):
        if len(self.buffer) != 0:
            return round(sum(self.buffer)/len(self.buffer), self.graph_instance.s['GRAPH_ROUND_DIGITS'])
        else:
            return 0

    def Clear(self):
        self.buffer.clear()


class GraphBox(MDBoxLayout):

    def __init__(self, _kivy_instance, _cols, settings=None, **kwargs):
        super().__init__(**kwargs)
        self.main_value = 0.
        self.avg_value = 0.
        self.isConfigured = False
        self.var = None

        self.MODES = ['NORMAL', 'SPECTRAL']

        self.s = {
            'NAME': graph_settings_defaults['NAME'],
            'MODE': graph_settings_defaults['MODE'],
            'GRAPH_ADDITIONAL_SPACE_Y': graph_settings_defaults['GRAPH_ADDITIONAL_SPACE_Y'],
            'GRAPH_BUFFER_AVG_SIZE': graph_settings_defaults['GRAPH_BUFFER_AVG_SIZE'],
            'GRAPH_ROUND_DIGITS': graph_settings_defaults['GRAPH_ROUND_DIGITS'],
            'GRAPH_LINE_THICKNESS': graph_settings_defaults['GRAPH_LINE_THICKNESS'],
            'HASH': uuid.uuid4().hex,
            'SHOW_AVG': graph_settings_defaults['SHOW_AVG'],
            'AVG_COLOR': graph_settings_defaults['AVG_COLOR'],
            'GRAPH_LABEL_X': graph_settings_defaults['GRAPH_LABEL_X'],
            'GRAPH_LABEL_Y': graph_settings_defaults['GRAPH_LABEL_Y'],
            'IS_INDIRECT': False,
            'EXPRESSION': 'Empty'
        }

        self.size_hint = [1, None]
        self.kivy_instance = _kivy_instance
        self.isBadExpression = False

        self.gardenGraph = GardenGraph(border_color=[1, 1, 1, 0],
                                       x_ticks_major=int(msettings.get('MAX_HISTORY_VALUES'))/8,
                                       x_ticks_minor=5,
                                       y_ticks_major=3,
                                       y_ticks_minor=2,
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
                                       label_options={
                                            'color': '#121212',  # color of tick labels and titles
                                            'bold': False},
                                       _graph_instance=self)

        self.ids.garden_graph_placer.add_widget(self.gardenGraph)

        if _cols == 1:
            self.height = (1 / 3) * (self.kivy_instance.ids.view_port.height - PADDING)
        else:
            if _cols == 2:
                if len(self.kivy_instance.main_container.GraphArr) == 0:
                    self.height = (self.kivy_instance.ids.view_port.height - PADDING)
                else:
                    self.height = 0.5 * (self.kivy_instance.ids.view_port.height - PADDING)

        if settings is not None:
            self.ApplyLayout(settings)

        self.avgBuffer = AVGBuffer(self)
        self.dialogGraphSettings = DialogGraphSettings(self)

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
        self.s['GRAPH_LINE_THICKNESS'] = settings['GRAPH_LINE_THICKNESS']
        self.s['SHOW_AVG'] = settings['SHOW_AVG']
        self.s['AVG_COLOR'] = settings['AVG_COLOR']
        self.s['GRAPH_LABEL_X'] = settings['GRAPH_LABEL_X']
        self.s['GRAPH_LABEL_Y'] = settings['GRAPH_LABEL_Y']

        if settings['IS_INDIRECT']:
            self.s['IS_INDIRECT'] = True
            self.var = IndirectVariable(client, self.kivy_instance)
            self.acf('EXPRESSION', settings, self.SetExpression)
        else:
            self.s['IS_INDIRECT'] = False
            self.var = DirectVariable(client, self.kivy_instance, self.s['NAME'])

    def SetExpression(self, expression):
        self.s['EXPRESSION'] = expression

    def toggle_x_grid_label(self):
        value = not self.s['GRAPH_LABEL_X']
        self.s['GRAPH_LABEL_X'] = value
        return value

    def toggle_y_grid_label(self):
        value = not self.s['GRAPH_LABEL_Y']
        self.s['GRAPH_LABEL_Y'] = value
        return value

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

    def TurnONAVG(self):
        self.s['SHOW_AVG'] = True
        self.avgBuffer.Clear()

    def TurnOFFAVG(self):
        self.s['SHOW_AVG'] = False

    def SwitchAVG(self):
        self.TurnOFFAVG() if self.s['SHOW_AVG'] else self.TurnONAVG()

    def GetAVGState(self):
        return self.s['SHOW_AVG']

    def Update(self):
        if self.s['NAME'] != 'None':
            _value = 0
            if not self.isIndirect():
                _value = round(self.var.GetValue(), self.s['GRAPH_ROUND_DIGITS'])
                self._UpdateGardenGraph(self.var.GetHistory())
                if self.isBadExpression and _value:
                    self.isBadExpression = False
            else:
                temp_value = self.var.GetValue(self.s['EXPRESSION'])
                if type(temp_value) is not str:
                    _value = round(temp_value, self.s['GRAPH_ROUND_DIGITS'])
                    self._UpdateGardenGraph(self.var.GetHistory())
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
                if self.s['MODE'] == 'NORMAL':
                    if self.s['SHOW_AVG']:
                        self.avgBuffer.AddValue(_value)
                        self.avg_value = self.avgBuffer.GetAVG()
                        self.ids.graph_main_text.text = str(_value) + " [color=" + self.s[
                            'AVG_COLOR'] + "](AVG: " + str(self.avg_value) + ")[/color]"
                    else:
                        self.ids.graph_main_text.text = str(_value)
                if self.s['MODE'] == 'SPECTRAL':
                    pass
            else:
                self.ids.graph_main_text.text = "[color=" + get_hex((0.8, 0.3, 0.3)) + "]" + 'BAD EXPRESSION!' + "[/color]"

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

    def AccentIt(self):
        self.ids.mdcard_id.md_bg_color = self.kivy_instance.main_app.theme_cls.primary_color

    def UnAccentIt(self):
        self.ids.mdcard_id.md_bg_color = self.kivy_instance.main_app.theme_cls.accent_color

    def _UpdateGardenGraph(self, _arr):
        if self.s['MODE'] == 'NORMAL':
            self.gardenGraph.UpdatePlot(_arr)
        if self.s['MODE'] == 'SPECTRAL':
            pass

    def _UpdateNameButton(self):
        self.ids.graph_labvar_name_button.text = f"{self.s['NAME']}:{self.s['MODE']}"

    def _SetMode(self, _mode):
        self.s['MODE'] = _mode
        if _mode != 'NORMAL':
            self.kivy_instance.main_app.hide_widget_only(
                self.ids.graph_main_text)
        else:
            self.kivy_instance.main_app.show_widget_only(
                self.ids.graph_main_text)
        self._UpdateNameButton()
