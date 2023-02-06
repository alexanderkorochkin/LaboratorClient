from kivymd.uix.list import IRightBodyTouch, OneLineIconListItem
from kivy.metrics import dp
from libs.settings.settingsJSON import *
import logging
import uuid

from kivymd.app import MDApp
from libs.opcua.opcuaclient import client
from libs.toolConfigurator import LabVar, IndirectVariable, ServerVariable

from kivymd.uix.menu import MDDropdownMenu
from kivy.animation import Animation

from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivy_garden.graph import Graph, LinePlot
from kivy.logger import Logger, LOG_LEVELS, LoggerHistory
from kivy.lang import Builder
from kivy.factory import Factory

from libs.dialogs import *
from libs.layoutManager import LayoutManager
from kivy.utils import get_hex_from_color as get_hex
from kivy.utils import get_color_from_hex as get_color
from kivy.utils import rgba

Logger.setLevel(LOG_LEVELS["debug"])


class GardenGraph(Graph):
    def __init__(self, _graph_instance=None, **kwargs):
        super().__init__(**kwargs)
        self.graph_instance = _graph_instance
        self.plot = LinePlot(color=KivyApp.theme_cls.primary_color, line_width=self.graph_instance.s['GRAPH_LINE_THICKNESS'])
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
            self.var = ServerVariable(client, self.kivy_instance, self.s['NAME'])

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
    def CheckName(self, name):
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
            self.var = ServerVariable(client, self.kivy_instance, self.s['NAME'])
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
        self.ids.graph_labvar_name_button.text = '{}:{}'.format(self.s['NAME'], self.s['MODE'])

    def _SetMode(self, _mode):
        self.s['MODE'] = _mode
        if _mode != 'NORMAL':
            self.kivy_instance.main_app.hide_widget_only(
                self.ids.graph_main_text)
        else:
            self.kivy_instance.main_app.show_widget_only(
                self.ids.graph_main_text)
        self._UpdateNameButton()


def ResizeGraphCallback(instance, value):
    if value[0] > value[1]:
        KivyApp.kivy_instance.main_container.columns = 2
        if len(KivyApp.kivy_instance.main_container.GraphArr) > 1:
            for element in KivyApp.kivy_instance.main_container.GraphArr:
                element.height = 0.5 * (KivyApp.kivy_instance.ids.view_port.height - PADDING)
        else:
            for element in KivyApp.kivy_instance.main_container.GraphArr:
                element.height = (KivyApp.kivy_instance.ids.view_port.height - PADDING)
    if value[0] <= value[1]:
        KivyApp.kivy_instance.main_container.columns = 1
        for element in KivyApp.kivy_instance.main_container.GraphArr:
            element.height = (1 / 3) * (KivyApp.kivy_instance.ids.view_port.height - PADDING)


def animate_graph_removal(wid, method):
    # animate shrinking widget width
    anim = Animation(opacity=0, height=0, duration=0.5, t='out_expo')
    anim.bind(on_complete=method)
    t = wid.gardenGraph._trigger
    ts = wid.gardenGraph._trigger_size
    wid.gardenGraph.unbind(center=ts, padding=ts, precision=ts, plots=ts, x_grid=ts,
              y_grid=ts, draw_border=ts)
    wid.gardenGraph.unbind(xmin=t, xmax=t, xlog=t, x_ticks_major=t, x_ticks_minor=t,
              xlabel=t, x_grid_label=t, ymin=t, ymax=t, ylog=t,
              y_ticks_major=t, y_ticks_minor=t, ylabel=t, y_grid_label=t,
              font_size=t, label_options=t, x_ticks_angle=t)
    anim.start(wid)


class GContainer(MDBoxLayout):
    gcontainer = ObjectProperty(None)
    scrollview = ObjectProperty(None)
    columns = NumericProperty(None)

    def __init__(self, _kivy_instance, **kwargs):
        super().__init__(**kwargs)
        self.kivy_instance = _kivy_instance
        self.bind(size=ResizeGraphCallback)
        self.GraphArr = []
        self.columns = 1

    def isContainsGraphWithName(self, _labvar_name):
        for graph in self.GraphArr:
            if graph.s['NAME'] == _labvar_name:
                return True
        return False

    def RefreshAll(self):
        for gr in self.GraphArr:
            gr.ClearGraph()

    def AddGraph(self, _settings=None):
        graphbox = None
        if self.columns == 1:
            graphbox = GraphBox(self.kivy_instance, self.columns, settings=_settings)
            self.GraphArr.append(graphbox)
            self.gcontainer.add_widget(graphbox)

        if self.columns == 2:
            if len(self.GraphArr) == 0:
                graphbox = GraphBox(self.kivy_instance, self.columns, settings=_settings)
                self.GraphArr.append(graphbox)
                self.gcontainer.add_widget(graphbox)
                self.GraphArr[0].SetHeight((self.kivy_instance.ids.view_port.height - PADDING))
            else:
                if len(self.GraphArr) == 1:
                    graphbox = GraphBox(self.kivy_instance, self.columns, settings=_settings)
                    self.GraphArr.append(graphbox)
                    self.gcontainer.add_widget(graphbox)
                    self.GraphArr[0].SetHeight(0.5 * (self.kivy_instance.ids.view_port.height - PADDING))
                else:
                    if len(self.GraphArr) > 1:
                        graphbox = GraphBox(self.kivy_instance, self.columns, settings=_settings)
                        self.GraphArr.append(graphbox)
                        self.gcontainer.add_widget(graphbox)

        Logger.debug("GRAPH: Graph [{}] with HASH: {} is added!".format(graphbox.s['NAME'], graphbox.s['HASH']))

    def GetGraphByHASH(self, _hash):
        for x in self.GraphArr:
            if x.s['HASH'] == _hash:
                return x
        return None

    def RemoveGraphByHASH(self, _hash):
        animate_graph_removal(self.GetGraphByHASH(_hash), self.RemoveGraph)

    def RemoveGraph(self, anim, graph):
        if len(self.GraphArr) > 0:

            temp = graph

            if self.columns == 1:
                self.gcontainer.remove_widget(temp)
                self.GraphArr.remove(temp)

            if self.columns == 2:
                if len(self.GraphArr) == 1:
                    self.gcontainer.remove_widget(temp)
                    self.GraphArr.remove(temp)
                else:
                    if len(self.GraphArr) == 2:
                        self.gcontainer.remove_widget(temp)
                        self.GraphArr.remove(temp)
                        self.GraphArr[0].SetHeight((self.kivy_instance.ids.view_port.height - PADDING))
                    else:
                        if len(self.GraphArr) > 2:
                            self.gcontainer.remove_widget(temp)
                            self.GraphArr.remove(temp)

            Logger.debug("GRAPH: Graph [{}] with HASH: {} is removed!".format(temp.s['NAME'], temp.s['HASH']))


class Item(OneLineIconListItem):
    left_icon = StringProperty()


class LaboratorClient(MDScreen):
    endpoint = StringProperty()

    def __init__(self, _main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_container = GContainer(self)
        self.main_app = _main_app
        self.LabVarArr = []

        # self.LabVarArr.append(LabVar(0, -1, '*tK(tC)', 'NONE_PORT', 'NONE_MULTIPLIER', expression='1arg + 273'))

        menu_items = [
            {
                "text": 'Добавить график',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'plus',
                "font_size": sp(12),
                "on_release": self.AddGraph,
            },
            {
                "text": 'Обновить графики',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'refresh',
                "font_size": sp(12),
                "on_release": self.RefreshAll,
            },
            {
                "text": 'Показать лог' if msettings.get('HIDE_LOG_BY_DEFAULT') else 'Скрыть лог',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'math-log',
                "font_size": sp(12),
                "on_release": self.main_app.ToggleLog,
            },
            {
                "text": 'Настройки',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'cog-outline',
                "font_size": sp(12),
                "on_release": self.main_app.open_main_settings,
            },
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.menu_button,
            items=menu_items,
            width_mult=4,
            max_height=0,
        )

    def Prepare(self, dt):
        self.ids.view_port.add_widget(self.main_container)
        self.endpoint = msettings.get('LAST_IP')

    def GetGraphByHASH(self, _hash):
        return self.main_container.GetGraphByHASH(_hash)

    def AddGraph(self, _settings=None):
        self.main_container.AddGraph(_settings)
        if _settings is None:
            self.menu.dismiss()

    def RefreshAll(self):
        self.main_container.RefreshAll()
        self.menu.dismiss()

    def RemoveGraphByHASH(self, _hash):
        self.main_container.RemoveGraphByHASH(_hash)

    def LabVarArrConfigure(self, path):
        Logger.debug("LabVarConf: Getting configuration from server...")
        arr = client.GetVarsFromNode(client.lab_node)

        for var in arr:
            for child in client.lab_node.get_children():
                if str(child.get_browse_name()).find(str(var.name)) != -1:
                    var.browse_name = str(child.get_browse_name())
                    var.node_id = str(child)
                    Logger.debug("PARSEVARS: [" + var.name + "], the browse_name is: [" + str(
                        var.browse_name) + "], NodeId: [" + var.node_id + "]")

        self.LabVarArr = arr

    def Reconnection(self, dt):
        if client.GetReconnectNumber() <= msettings.get('MAX_RECONNECTIONS_NUMBER'):
            if client.isReconnecting():
                if not client.isConnected():
                    client._isReconnecting = True
                    client.Disconnect()
                    self.Connect()
                    if not client.isConnected():
                        Clock.schedule_once(self.Reconnection, dt)
                        client.ReconnectNumberInc()
                    else:
                        client.ReconnectNumberZero()
                else:
                    client._isReconnecting = False
                    client.ReconnectNumberZero()
            else:
                client.ReconnectNumberZero()
        else:
            self.Disconnect()

    def ConnectLow(self, dt):
        try:
            client.Connect(self.endpoint)
            self.LabVarArrConfigure(msettings.get('CONFIGURATION_PATH'))
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.endpoint_label.disabled = True
            Logger.debug("CONNECT: Connected to {}!".format(self.endpoint))
            self.ids.info_log.text = "Connected to {}!".format(self.endpoint)
            Logger.debug("CONNECT: Parsed!")
            msettings.set('allSettings', 'LAST_IP', self.endpoint)
        except Exception:
            if not client.isReconnecting():
                self.ids.btn_connect.disabled = False
                self.ids.btn_disconnect.disabled = True
                self.ids.endpoint_label.disabled = False
                self.ids.info_log.text = "Error while connecting... Disconnected!"
                Logger.error("CONNECT: Error while connecting... Disconnected!")
            else:
                self.ids.info_log.text = "Connection lost! Error while reconnecting... (" + str(client.GetReconnectNumber()) + ')'
                Logger.error("CONNECT: Connection lost! Error while reconnecting... (" + str(client.GetReconnectNumber()) + ')')

    def Connect(self):
        self.ids.info_log.text = "Trying connect to {}!".format(self.endpoint)
        self.ids.btn_connect.disabled = True
        Clock.schedule_once(self.ConnectLow, 0)

    def Disconnect(self):
        client._isReconnecting = False
        try:
            client.Disconnect()
            self.ids.btn_disconnect.disabled = True
            self.ids.btn_connect.disabled = False
            self.ids.endpoint_label.disabled = False
            self.ids.info_log.text = "Disconnected from {}!".format(self.endpoint)
            Logger.debug("CONNECT: Disconnected from {}!".format(self.endpoint))
        except Exception:
            self.ids.btn_disconnect.disabled = False
            self.ids.btn_connect.disabled = True
            self.ids.endpoint_label.disabled = True
            self.ids.info_log.text = "Error while disconnecting..."
            Logger.info("CONNECT: Error while disconnecting...")

    def Update(self, dt):
        if client.isConnected():
            #try:
                for graph in self.main_container.GraphArr:
                    graph.Update()

            # except Exception:
            #     client._isConnected = False
            #     client._isReconnecting = True
            #     self.ids.btn_disconnect.disabled = False
            #     self.ids.btn_connect.disabled = True
            #     self.ids.info_log.text = "Connection lost! Trying to reconnect..."
            #     Logger.debug("UPDATE: Connection lost! Trying to reconnect...")
            #     self.Reconnection(msettings.get('RECONNECTION_TIME'))

    def GetLabVarByName(self, name):
        for labvar in self.LabVarArr:
            if labvar.name == name:
                return labvar
        return None


class FullLogHandler(logging.Handler):

    def __init__(self, _kivy_instance, _label, level=logging.NOTSET):
        super(FullLogHandler, self).__init__(level=level)
        self.label = _label
        self.kivy_instance = _kivy_instance

    def emit(self, record):
        def f(dt=None):
            self.label.text = "\n".join(list(map(self.format, LoggerHistory.history[::-1])))
            self.label.scroll_y = 0
        Clock.schedule_once(f)


class KivyApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kivy_instance = None
        self.settings_widget = None
        self.title = "Laborator Client"
        self.dialogEndpoint = None
        self.hiddenWidgets = []
        self.layoutManager = None

    def on_stop(self):
        try:
            client.Disconnect()
            self.layoutManager.SaveLayout()
        except Exception:
            Logger.error("KivyApp: Error while disconnecting on app stop!")

    def on_start(self):
        Clock.schedule_once(self.kivy_instance.Prepare, 1)
        Clock.schedule_once(self.layout, 1)
        Clock.schedule_interval(self.kivy_instance.Update, int(msettings.get('KIVY_UPDATE_FUNCTION_TIME')))

    def layout(self, dt):
        if msettings.get('USE_LAYOUT'):
            self.layoutManager.LoadLayout()

    @staticmethod
    def LoadKV():
        for filename in os.listdir(os.path.join("libs", "kv")):
            Builder.load_file(os.path.join("libs", "kv", filename))

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.set_colors("Orange", "300", "50", "800", "Gray", "600", "50", "800")
        self.LoadKV()
        self.kivy_instance = LaboratorClient(self)

        Logger.addHandler(FullLogHandler(self, self.kivy_instance.ids.log_label, logging.DEBUG))

        if msettings.get("HIDE_LOG_BY_DEFAULT"):
            self.hide_widget(self.kivy_instance.ids.log_box)
        else:
            self.hide_widget(self.kivy_instance.ids.view_port)

        self.dialogEndpoint = DialogEndpoint(self)
        self.layoutManager = LayoutManager(self.kivy_instance)

        return self.kivy_instance

    def build_config(self, config):
        config.setdefaults('allSettings', settings_defaults)
        config.setdefaults('GraphSettings', graph_settings_defaults)
        msettings.instance = self.config

    def build_settings(self, settings):
        self.settings_widget = settings
        settings.add_json_panel('Основные настройки', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        print(config, section, key, value)

    def create_settings(self):
        if self.settings_cls is None:
            from libs.settings.settings_mod import SettingsWithNoMenu
            self.settings_cls = SettingsWithNoMenu
        else:
            self.settings_cls = Factory.get(self.settings_cls)
        s = self.settings_cls()
        self.build_settings(s)
        if self.use_kivy_settings:
            s.add_kivy_panel()
        s.bind(on_close=self.close_settings,
               on_config_change=self._on_config_change)
        return s

    def ToggleLog(self):
        wid1 = self.kivy_instance.ids.log_box
        wid2 = self.kivy_instance.ids.view_port
        self.swap_widgets_visibility(wid1, wid2)
        if self.kivy_instance.menu.items[2]['text'] == 'Показать лог':
            self.kivy_instance.menu.items[2]['text'] = 'Скрыть лог'
        else:
            self.kivy_instance.menu.items[2]['text'] = 'Показать лог'
        self.kivy_instance.menu.dismiss()

    # Swaps visibility of widgets. Wid1 are hiding permanently.(self.ids.log_box, self.ids.view_port)
    def swap_widgets_visibility(self, wid1, wid2):
        if wid1 not in self.hiddenWidgets and wid2 not in self.hiddenWidgets:
            self.hide_widget(wid1)
        elif wid1 in self.hiddenWidgets and wid2 in self.hiddenWidgets:
            self.hide_widget(wid2)
        else:
            self.hide_widget(wid1)
            self.hide_widget(wid2)

    def show_widget_only(self, wid):
        if wid in self.hiddenWidgets:
            self.hiddenWidgets.remove(wid)
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs

    def hide_widget_only(self, wid):
        if wid not in self.hiddenWidgets:
            self.hiddenWidgets.append(wid)
            wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True

    # Hides or shows widget
    def hide_widget(self, wid):
        if wid not in self.hiddenWidgets:
            self.hiddenWidgets.append(wid)
            wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True
        else:
            self.hiddenWidgets.remove(wid)
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs

    def menu_open(self):
        self.kivy_instance.menu.open()

    def open_main_settings(self):
        self.open_settings()
        self.kivy_instance.menu.dismiss()


KivyApp = KivyApp()

# Программа получает на вход готовые приведенные параметры, выводит их графики,
# считает косвенные параметры, считает спектральные параметры, среднее значение...

# TODO Научиться считать косвенные параметры по измеряемым и выводить на график
# TODO Научиться делать статистический анализ
# TODO Научиться подключаться к LabView
