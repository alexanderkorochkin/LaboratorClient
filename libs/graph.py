import uuid
from threading import Thread

from kivy.core.window import Window
from kivy.properties import ObjectProperty, ColorProperty, StringProperty
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDIcon
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.widget import MDWidget

from libs.utils import *
from libs.dialogs import DialogGraphSettings, SnackbarMessage
from libs.gardengraph.init import Graph, LinePlot, SmoothLinePlot, PointPlot, ScatterPlot
from libs.opcua.opcuaclient import client
from libs.settings.settingsJSON import *
from libs.variables import DirectVariable, IndirectVariable


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
            average = sum(self.buffer)/len(self.buffer)
        self.CountAVGHistory(average)
        return average

    def Clear(self):
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
        self.y_precision = '% 0.' + str(msettings.get('GRAPH_ROUND_DIGITS')) + 'f'
        self.x_precision = '% 0.01f'
        self.draw_border = False
        self.padding = '10dp'

        self.point_value_indicator = None
        self.point_value_indicator_disabled = True

        self.plot = LinePlot()
        self.plot.points = []

        self.avg_plot = LinePlot()
        self.avg_plot.points = []

        self.intime_plot = LinePlot()
        self.intime_plot.points = []

        self.spectral_plot = LinePlot()
        self.spectral_plot.points = []

        self.point_plot = ScatterPlot()
        self.point_plot.points = []

    def SetMode(self, mode):
        if mode == 'SPECTRAL':
            self.remove_plot(self.plot)
            self.remove_plot(self.avg_plot)
            self.remove_plot(self.intime_plot)
            self.remove_plot(self.point_plot)
            self.UpdatePlotColor('SPECTRAL')
        elif mode == 'NORMAL':
            self.remove_plot(self.spectral_plot)
            self.xmax = msettings.get('MAX_HISTORY_VALUES') + 1
            self.UpdatePlotColor('AVG')
            self.UpdatePlotColor('INTIME')
            self.UpdatePlotColor('MAIN')
            self.UpdatePlotColor('POINT')

    def TogglePlot(self):
        if self.graph_instance.s['MODE'] == 'NORMAL':
            if self.graph_instance.s['SHOW_AVG_GRAPH']:
                self.add_plot(self.avg_plot)
            else:
                self.remove_plot(self.avg_plot)
            if self.graph_instance.s['SHOW_INTIME_GRAPH']:
                self.add_plot(self.intime_plot)
            else:
                self.remove_plot(self.intime_plot)
            if self.graph_instance.s['SHOW_MAIN_GRAPH']:
                self.add_plot(self.plot)
            else:
                self.remove_plot(self.plot)

    def UpdatePlotColor(self, plot_name="ALL"):
        if plot_name == 'ALL' or 'AVG' and self.graph_instance.s['MODE'] == 'NORMAL':
            if self.graph_instance.s['SHOW_AVG_GRAPH']:
                self.remove_plot(self.avg_plot)
                points_temp = self.avg_plot.points
                self.avg_plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.accent_light, line_width=self.graph_instance.s['AVG_GRAPH_LINE_THICKNESS'])
                self.avg_plot.points = points_temp
                self.add_plot(self.avg_plot)
        if plot_name == 'ALL' or 'INTIME' and self.graph_instance.s['MODE'] == 'NORMAL':
            if self.graph_instance.s['SHOW_INTIME_GRAPH']:
                self.remove_plot(self.intime_plot)
                points_temp = self.intime_plot.points
                self.intime_plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.accent_color, line_width=self.graph_instance.s['INTIME_GRAPH_LINE_THICKNESS'])
                self.intime_plot.points = points_temp
                self.add_plot(self.intime_plot)
        if plot_name == 'ALL' or 'MAIN' and self.graph_instance.s['MODE'] == 'NORMAL':
            if self.graph_instance.s['SHOW_MAIN_GRAPH']:
                self.remove_plot(self.plot)
                points_temp = self.plot.points
                self.plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color, line_width=self.graph_instance.s['MAIN_GRAPH_LINE_THICKNESS'])
                self.plot.points = points_temp
                self.add_plot(self.plot)
        if plot_name == 'ALL' or 'POINT' and self.graph_instance.s['MODE'] == 'NORMAL':
            self.remove_plot(self.point_plot)
            points_temp = self.point_plot.points
            self.point_plot = ScatterPlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color, _radius=8)
            self.point_plot.points = points_temp
            self.add_plot(self.point_plot)
        if plot_name == 'ALL' or 'SPECTRAL':
            if self.graph_instance.s['MODE'] == 'SPECTRAL':
                self.remove_plot(self.spectral_plot)
                points_temp = self.spectral_plot.points
                self.spectral_plot = LinePlot(color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color, line_width=self.graph_instance.s['MAIN_GRAPH_LINE_THICKNESS'])
                self.spectral_plot.points = points_temp
                self.add_plot(self.spectral_plot)

    def UpdatePlot(self, plot_name, arr: list):

        if not self.isDeleting:

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

                # if not self.point_value_indicator:
                #     self.point_value_indicator = RPoint(size=[8, 8], size_hint=[None, None], color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color, pos_hint=[None, None])
                # else:
                #     if self.point_value_indicator not in self._plot_area.children:
                #         self._.add_widget(self.point_value_indicator)
                #     self.point_value_indicator.pos = self.get_widget_coord(temp_points[-1][0], temp_points[-1][1])

                self.add_plot(self.point_plot)
                self.point_plot.points = [(temp_points[-1][0], temp_points[-1][1])]

                # if self.point_value_indicator_disabled:
                #     self.point_value_indicator_disabled = False

            elif plot_name == 'SPECTRAL':

                # if not self.point_value_indicator_disabled and self.point_value_indicator:
                #     self._plot_area.remove_widget(self.point_value_indicator)
                #     self.point_value_indicator_disabled = True

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

    def ClearPlot(self, _plot='ALL'):
        self.plot.points = []
        self.avg_plot.points = []
        self.intime_plot.points = []
        self.spectral_plot.points = []

        if self.point_value_indicator:
            self.point_value_indicator.opacity = 0
            self.point_value_indicator = []
            self.point_value_indicator_disabled = True

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
        self.size_hint = [1, None]
        self.isBadExpression = False
        self.isStartup = True
        self.isChosen = False
        self.accented = False
        self.precached = False

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
        self.dialogGraphSettings = DialogGraphSettings(self)

        self.MODES = ['NORMAL', 'SPECTRAL']

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
        self.gardenGraph.TogglePlot()
        self.gardenGraph.UpdatePlotColor()

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
                self.var = IndirectVariable(client, self.kivy_instance, self.s['MAX_SPECTRAL_BUFFER_SIZE'])
            else:
                self.var = DirectVariable(client, self.kivy_instance, self.s['MAX_SPECTRAL_BUFFER_SIZE'], self.s['NAME'])
        if tag == 'MODE':
            if value == 'SPECTRAL':
                self.gardenGraph.tick_color = self.kivy_instance.main_app.theme_cls.accent_color
                self.gardenGraph.SetMode(value)
                self.gardenGraph.x_grid_label = self.s['GRAPH_LABEL_X']
            if value == 'NORMAL':
                self.gardenGraph.tick_color = [0, 0, 0, 0]
                self.gardenGraph.SetMode(value)
                self.gardenGraph.x_grid_label = False
            self.UpdateNameButton()
        if tag == 'EXPRESSION':
            self.UpdateNameButton()

    def PreCache(self):
        if not self.precached:
            self.precached = True
            self.dialogGraphSettings.Open()
            self.dialogGraphSettings.dialog.dismiss(force=True)

    def Resize(self, d_ori, d_type, container_height):
        number_graphs = len(self.kivy_instance.main_container.GraphArr)
        if d_ori == 'horizontal':
            if number_graphs == 1:
                self.height = container_height
            elif number_graphs == 2 or number_graphs == 3 or number_graphs == 4:
                if d_type == 'tablet':
                    self.height = (1 / msettings.get('ROW_HT')) * (container_height - (msettings.get('ROW_HT') - 1) * PADDING)
                else:
                    self.height = (1 / 2) * (container_height - 1 * PADDING)
            else:
                if d_type == 'desktop':
                    self.height = (1 / msettings.get('ROW_HD')) * (container_height - (msettings.get('ROW_HD') - 1) * PADDING)
                elif d_type == 'tablet':
                    self.height = (1 / msettings.get('ROW_HT')) * (container_height - (msettings.get('ROW_HT') - 1) * PADDING)
                elif d_type == 'mobile':
                    self.height = (1 / msettings.get('ROW_HM')) * (container_height - (msettings.get('ROW_HM') - 1) * PADDING)
        elif d_ori == 'vertical':
            if d_type == 'desktop':
                self.height = (1 / msettings.get('ROW_VD')) * (container_height - (msettings.get('ROW_VD') - 1) * PADDING)
            elif d_type == 'tablet':
                self.height = (1 / msettings.get('ROW_VT')) * (container_height - (msettings.get('ROW_VT') - 1) * PADDING)
            elif d_type == 'mobile':
                self.height = (1 / msettings.get('ROW_VM')) * (container_height - (msettings.get('ROW_VM') - 1) * PADDING)

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

    def Update(self, plots_only=False):
        if self.s['NAME'] != 'None':
            if not plots_only:
                if not self.isIndirect():
                    out = self.var.GetValue()
                    if 'ERROR' not in str(out):
                        self.main_value = float(out)
                        if self.isBadExpression:
                            self.isBadExpression = False
                    else:
                        if not self.isBadExpression:
                            self.isBadExpression = True
                            SnackbarMessage(f"[{self.s['NAME']}]: Ошибка при получении значения с сервера!")
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
                            SnackbarMessage(f"[{self.s['NAME']}]: Ошибка при вычислении выражения!")
                            Logger.debug(f'GraphUpdate: WARNING! {out}')

            if not self.isBadExpression:

                self.avgBuffer.AddValue(self.main_value)
                self.avg_value = self.avgBuffer.GetAVG()

                if self.s['MODE'] == 'NORMAL':
                    if self.s['SHOW_MAIN_VALUE']:
                        self.ids.graph_current_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.primary_color) + "]" + str(round(self.main_value, self.s['GRAPH_ROUND_DIGITS'])) + "[/color]"
                    else:
                        self.ids.graph_current_value.text = ''
                    if self.s['SHOW_AVG_VALUE']:
                        self.ids.graph_avg_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.accent_color) + f"]AVG{msettings.get('MAX_HISTORY_VALUES')}: " + str(round(self.avg_value, self.s['GRAPH_ROUND_DIGITS'])) + "[/color]"
                    else:
                        self.ids.graph_avg_value.text = ''
                    self.gardenGraph.UpdatePlot('AVG', self.avgBuffer.avg_buffer)
                    self.gardenGraph.UpdatePlot('MAIN', self.var.GetHistory())
                elif self.s['MODE'] == 'SPECTRAL':
                    spectral, maxes, avg, sigma = self.var.GetSpectral(2)
                    self.gardenGraph.UpdatePlot('SPECTRAL', spectral)
                    self.ids.graph_current_value.text = "[color=" + color2hex(self.kivy_instance.main_app.theme_cls.primary_color) + "]N: " + str(len(self.var.values_history)) + "[/color]"
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

