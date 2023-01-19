from libs.settings.settingsJSON import *
import logging
import random

from kivymd.app import MDApp
from libs.opcua.opcuaclient import client
from libs.toolConfigurator import LabVar

from kivy.properties import NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivy_garden.graph import Graph, LinePlot
from kivy.logger import Logger, LOG_LEVELS, LoggerHistory
from kivy.lang import Builder
from kivy.factory import Factory

from libs.dialogs import *
from libs.layoutManager import LayoutManager

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

    def UpdatePlot(self, _arr):
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
    labvar_value = NumericProperty(0)
    avg_value = NumericProperty(0)
    labvar_name = StringProperty("None")
    hash = NumericProperty(0)

    def __init__(self, _kivy_instance, _cols, settings=None, **kwargs):
        super().__init__(**kwargs)

        if settings is None:
            self.s = {
                'NAME': graph_settings_defaults['NAME'],
                'MODE': graph_settings_defaults['MODE'],
                'GRAPH_ADDITIONAL_SPACE_Y': graph_settings_defaults['GRAPH_ADDITIONAL_SPACE_Y'],
                'GRAPH_BUFFER_AVG_SIZE': graph_settings_defaults['GRAPH_BUFFER_AVG_SIZE'],
                'GRAPH_ROUND_DIGITS': graph_settings_defaults['GRAPH_ROUND_DIGITS'],
                'GRAPH_LINE_THICKNESS': graph_settings_defaults['GRAPH_LINE_THICKNESS'],
                'HASH': random.randrange(100001, 999999)
            }
        else:
            self.s = settings

        self.labvar_name = self.s['NAME']
        self.size_hint = [1, None]
        self.kivy_instance = _kivy_instance
        self.current_touch = "None"

        self.avgBuffer = AVGBuffer(self)
        self.dialogGraphSettings = DialogGraphSettings(self)

        self.gardenGraph = GardenGraph(border_color=[1, 1, 1, 0],
                                       x_ticks_major=int(msettings.get('MAX_HISTORY_VALUES'))/8,
                                       x_ticks_minor=5,
                                       y_ticks_major=6,
                                       y_ticks_minor=5,
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

    def RemoveMe(self):
        self.kivy_instance.main_container.RemoveGraphByHASH(self.s['HASH'])

    def SetHeight(self, height):
        self.height = height

    def SetLabVarValue(self, labvar_value):
        self.labvar_value = labvar_value
        self.avgBuffer.AddValue(labvar_value)
        self.avg_value = self.avgBuffer.GetAVG()

    def SetLabVarName(self, _labvar_name):
        self.s['NAME'] = _labvar_name
        self.labvar_name = _labvar_name

    def GetLabVarName(self):
        return self.s['NAME']

    def UpdateGardenGraph(self, _arr):
        self.gardenGraph.UpdatePlot(_arr)

    def ClearPlot(self):
        self.gardenGraph.ClearPlot()
        self.avgBuffer.Clear()

    def ClearGraph(self, value=None):
        # Очищаем буфер прошлой переменной
        for labvar in self.kivy_instance.LabVarArr:
            if labvar.name == self.s['NAME']:
                labvar.ClearHistory()
        self.avgBuffer.Clear()
        self.gardenGraph.ClearPlot()
        self.current_touch = "None"


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


class Container(MDBoxLayout):
    container = ObjectProperty(None)
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

    def AddGraph(self, _settings=None):
        graphbox = None
        if self.columns == 1:
            graphbox = GraphBox(self.kivy_instance, self.columns, settings=_settings)
            self.GraphArr.append(graphbox)
            self.container.add_widget(graphbox)

        if self.columns == 2:
            if len(self.GraphArr) == 0:
                graphbox = GraphBox(self.kivy_instance, self.columns, settings=_settings)
                self.GraphArr.append(graphbox)
                self.container.add_widget(graphbox)
                self.GraphArr[0].SetHeight((self.kivy_instance.ids.view_port.height - PADDING))
            else:
                if len(self.GraphArr) == 1:
                    graphbox = GraphBox(self.kivy_instance, self.columns, settings=_settings)
                    self.GraphArr.append(graphbox)
                    self.container.add_widget(graphbox)
                    self.GraphArr[0].SetHeight(0.5 * (self.kivy_instance.ids.view_port.height - PADDING))
                else:
                    if len(self.GraphArr) > 1:
                        graphbox = GraphBox(self.kivy_instance, self.columns, settings=_settings)
                        self.GraphArr.append(graphbox)
                        self.container.add_widget(graphbox)

        Logger.debug("GRAPH: Graph [{}] with HASH: {} is added!".format(graphbox.s['NAME'], graphbox.s['HASH']))

    # def ShiftNumbering(self, _id):
    #     for element in self.GraphArr:
    #         if int(element.s.get('ID')) < int(_id):
    #             continue
    #         element.s.set('ID', str(int(element.s.get('ID')) - 1))

    def GetGraphByHASH(self, _hash):
        for x in self.GraphArr:
            if x.s['HASH'] == _hash:
                return x
        return None

    def RemoveGraphByHASH(self, _hash):
        self.RemoveGraph(self.GetGraphByHASH(_hash))

    def RemoveGraph(self, graph):
        if len(self.GraphArr) > 0:

            temp = graph

            if self.columns == 1:
                self.container.remove_widget(temp)
                self.GraphArr.remove(temp)

            if self.columns == 2:
                if len(self.GraphArr) == 1:
                    self.container.remove_widget(temp)
                    self.GraphArr.remove(temp)
                else:
                    if len(self.GraphArr) == 2:
                        self.container.remove_widget(temp)
                        self.GraphArr.remove(temp)
                        self.GraphArr[0].SetHeight((self.kivy_instance.ids.view_port.height - PADDING))
                    else:
                        if len(self.GraphArr) > 2:
                            self.container.remove_widget(temp)
                            self.GraphArr.remove(temp)

            Logger.debug("GRAPH: Graph [{}] with HASH: {} is removed!".format(temp.s['NAME'], temp.s['HASH']))


class LaboratorClient(MDScreen):
    endpoint = StringProperty()

    def __init__(self, _main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_container = Container(self)
        self.main_app = _main_app
        self.LabVarArr = []

    def Prepare(self, dt):
        self.ids.view_port.add_widget(self.main_container)
        self.endpoint = msettings.get('LAST_IP')

    def GetGraphByHASH(self, _hash):
        return self.main_container.GetGraphByHASH(_hash)

    def AddGraph(self, _settings=None):
        self.main_container.AddGraph(_settings)

    def RemoveGraphByHASH(self, _hash):
        self.main_container.RemoveGraphByHASH(_hash)

    @staticmethod
    def LabVarArrConfigure(path):
        if msettings.get('GET_FROM_SERVER') == 0:
            arr = []
            file = open(path, "r", encoding='utf-8')
            Logger.debug("LabVarConf: Opened file to configuration: " + str(path))
            for line in file:
                index, port, name, *multiplier = line.split("\t", 4)
                arr.append(LabVar(0, index, name, port, multiplier))
            file.close()
            return arr
        else:
            Logger.debug("LabVarConf: Getting configuration from server...")
            return client.GetVarsFromNode(client.lab_node)

    def ParseVars(self):
        for var in self.LabVarArr:
            for child in client.lab_node.get_children():
                if str(child.get_browse_name()).find(str(var.name)) != -1:
                    var.browse_name = str(child.get_browse_name())
                    var.node_id = str(child)
                    Logger.debug("PARSEVARS: [" + var.name + "], the browse_name is: [" + str(
                        var.browse_name) + "], NodeId: [" + var.node_id + "]")

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
            self.LabVarArr = self.LabVarArrConfigure(msettings.get('CONFIGURATION_PATH'))
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.endpoint_label.disabled = True
            Logger.debug("CONNECT: Connected to {}!".format(self.endpoint))
            self.ParseVars()
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
            try:
                # Заносим эти переменные в соответствующие графики
                for graph in self.main_container.GraphArr:
                    if graph.s['NAME'] != "None":
                        for labvar in self.LabVarArr:
                            if labvar.name == graph.s['NAME']:
                                _value = client.get_node(labvar.node_id).get_value()
                                labvar.value = _value
                                labvar.WriteHistory(_value)
                                graph.UpdateGardenGraph(labvar.GetHistory())
                                graph.SetLabVarValue(round(labvar.value, graph.s['GRAPH_ROUND_DIGITS']))
            except Exception:
                client._isConnected = False
                client._isReconnecting = True
                self.ids.btn_disconnect.disabled = False
                self.ids.btn_connect.disabled = True
                self.ids.info_log.text = "Connection lost! Trying to reconnect..."
                Logger.debug("UPDATE: Connection lost! Trying to reconnect...")
                self.Reconnection(msettings.get('RECONNECTION_TIME'))


class FullLogHandler(logging.Handler):

    def __init__(self, _kivy_instance, _label, level=logging.NOTSET):
        super(FullLogHandler, self).__init__(level=level)
        self.label = _label
        self.kivy_instance = _kivy_instance

    def emit(self, record):
        def f(dt=None):
            self.label.text = "\n".join(list(map(self.format, LoggerHistory.history[::-1])))
            # self.kivy_instance.instance.ids.log_scroll.scroll_y = 0
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

    # Swaps visibility of widgets. Wid1 are hiding permanently.
    def swap_widgets(self, wid1, wid2):
        if wid1 not in self.hiddenWidgets and wid2 not in self.hiddenWidgets:
            self.hide_widget(wid1)
        elif wid1 in self.hiddenWidgets and wid2 in self.hiddenWidgets:
            self.hide_widget(wid2)
        else:
            self.hide_widget(wid1)
            self.hide_widget(wid2)

    # Hides or shows widget
    def hide_widget(self, wid):
        if wid not in self.hiddenWidgets:
            self.hiddenWidgets.append(wid)
            wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True
        else:
            self.hiddenWidgets.remove(wid)
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs


KivyApp = KivyApp()

# Программа получает на вход готовые приведенные параметры, выводит их графики,
# считает косвенные параметры, считает спектральные параметры, среднее значение...

# TODO Реализовать свой стиль для кнопок, лэйблов, и т.д. для унификации интерфейса
# TODO Реализовать сохранение и подгрузку лэйаута
# TODO Реализовать индивидуальные настройки для графиков
# TODO Научиться считать косвенные параметры по измеряемым и выводить на график
# TODO Научиться делать статистический анализ
# TODO Научиться подключаться к LabView
