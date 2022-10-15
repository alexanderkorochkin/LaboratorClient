import os

from settings.settingsJSON import settings_defaults, settings_json, msettings

from kivy.app import App
from libs.opcua.opcuaclient import client
from libs.toolConfigurator import LabVar

from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.graph import Graph, LinePlot

from kivy.logger import Logger, LOG_LEVELS
from kivy.lang import Builder
Logger.setLevel(LOG_LEVELS["debug"])


def ResizeGraphCallback(instance, value):
    if value[0] > value[1]:
        KivyApp.instance.GraphContainer.columns = 2
        if len(KivyApp.instance.GraphContainer.GraphArr) > 1:
            for element in KivyApp.instance.GraphContainer.GraphArr:
                element.height = 0.5 * KivyApp.instance.ids.view_port.height
        else:
            for element in KivyApp.instance.GraphContainer.GraphArr:
                element.height = KivyApp.instance.ids.view_port.height
    if value[0] <= value[1]:
        KivyApp.instance.GraphContainer.columns = 1
        for element in KivyApp.instance.GraphContainer.GraphArr:
            element.height = (1 / 3) * KivyApp.instance.ids.view_port.height


class GardenGraph(Graph):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plot = LinePlot(color=[0, 0.8, 0, 0.9], line_width=msettings.get('GRAPH_LINE_THICKNESS'))
        self.plot.points = [(0, 0)]
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
        self.ymax = round(((max(_yarr) + min(_yarr)) / 2) + abs(msettings.get('GRAPH_ADDITIONAL_SPACE_Y') * (max(_yarr) - ((max(_yarr) + min(_yarr)) / 2))))
        self.ymin = round(((max(_yarr) + min(_yarr)) / 2) - abs(msettings.get('GRAPH_ADDITIONAL_SPACE_Y') * (-min(_yarr) + ((max(_yarr) + min(_yarr)) / 2))))
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
    def __init__(self, buffer_size):
        self.isExecuted = True
        self.buffer_size = buffer_size
        self.buffer = []
        self.lastavg = 0

    def AddValue(self, value):
        if len(self.buffer) == self.buffer_size:
            self.buffer = self.buffer[self.buffer_size - len(self.buffer) + 1:]
        self.buffer.append(float(value))

    def GetAVG(self):
        if len(self.buffer) != 0:
            return round(sum(self.buffer)/len(self.buffer), msettings.get('GRAPH_ROUND_DIGITS'))
        else:
            return 0

    def Clear(self):
        self.buffer.clear()


class GraphBox(BoxLayout):
    labvar_name = StringProperty("None")
    labvar_value = NumericProperty(0)
    avg_value = NumericProperty(0)

    def __init__(self, _cols, _id, **kwargs):
        super().__init__(**kwargs)
        self.avgBuffer = AVGBuffer(msettings.get('GRAPH_BUFFER_AVG_SIZE'))
        self.size_hint = [1, None]
        self.id = _id
        self.current_touch = "None"
        self.gardenGraph = GardenGraph(border_color=[0, 0, 0, 1],
                                       x_ticks_major=int(msettings.get('MAX_HISTORY_VALUES'))/8,
                                       x_ticks_minor=5,
                                       y_ticks_major=6,
                                       y_ticks_minor=5,
                                       tick_color=[0, 0, 0, 0.15],
                                       background_color=[1, 1, 1, 0],
                                       y_grid_label=False,
                                       x_grid_label=False,
                                       x_grid=True,
                                       y_grid=True,
                                       xmin=0,
                                       xmax=msettings.get('MAX_HISTORY_VALUES') + 1,
                                       ymin=-1,
                                       ymax=1)
        self.ids.garden_graph_placer.add_widget(self.gardenGraph)

        if _cols == 1:
            self.height = (1 / 3) * KivyApp.instance.ids.view_port.height
        else:
            if _cols == 2:
                if len(KivyApp.instance.GraphContainer.GraphArr) == 0:
                    self.height = KivyApp.instance.ids.view_port.height
                else:
                    self.height = 0.5 * KivyApp.instance.ids.view_port.height

    def DoubleSingleTap(self):
        if self.current_touch != "None":
            Clock.unschedule(self.ClearGraph)
            self.RemoveMe()
            self.current_touch = "None"
        else:
            self.current_touch = "touch"
            Clock.schedule_once(self.ClearGraph, msettings.get('KIVY_DOUBLETAP_TIME'))

    def RemoveMe(self):
        KivyApp.instance.GraphContainer.RemoveGraphById(self.id)

    def SetHeight(self, height):
        self.height = height

    def SetLabVarValue(self, labvar_value):
        self.labvar_value = labvar_value
        self.avgBuffer.AddValue(labvar_value)
        self.avg_value = self.avgBuffer.GetAVG()

    def SetLabVarName(self, labvar_name):
        self.labvar_name = labvar_name

    def UpdateGardenGraph(self, _arr):
        self.gardenGraph.UpdatePlot(_arr)

    def ClearPlot(self):
        self.gardenGraph.ClearPlot()
        self.avgBuffer.Clear()

    def ClearGraph(self, value):
        # Очищаем буфер прошлой переменной
        for labvar in KivyApp.instance.LabVarArr:
            if labvar.name == self.labvar_name:
                labvar.ClearHistory()
        self.avgBuffer.Clear()

        self.gardenGraph.ClearPlot()

        self.current_touch = "None"


class GraphContainer(BoxLayout):
    container = ObjectProperty(None)
    scrollview = ObjectProperty(None)
    columns = NumericProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=ResizeGraphCallback)
        self.GraphArr = []
        self.columns = 1

    def isContainsGraphWithName(self, _labvar_name):
        for graph in self.GraphArr:
            if graph.labvar_name == _labvar_name:
                return True
        return False

    def AddGraph(self):
        graphbox = None
        if self.columns == 1:
            graphbox = GraphBox(self.columns, len(self.GraphArr))
            self.GraphArr.append(graphbox)
            self.ids.graph_container.add_widget(graphbox)

        if self.columns == 2:
            if len(self.GraphArr) == 0:
                graphbox = GraphBox(self.columns, len(self.GraphArr))
                self.GraphArr.append(graphbox)
                self.ids.graph_container.add_widget(graphbox)
                self.GraphArr[0].SetHeight(KivyApp.instance.ids.view_port.height)
            else:
                if len(self.GraphArr) == 1:
                    graphbox = GraphBox(self.columns, len(self.GraphArr))
                    self.GraphArr.append(graphbox)
                    self.ids.graph_container.add_widget(graphbox)
                    self.GraphArr[0].SetHeight(0.5 * KivyApp.instance.ids.view_port.height)
                else:
                    if len(self.GraphArr) > 1:
                        graphbox = GraphBox(self.columns, len(self.GraphArr))
                        self.GraphArr.append(graphbox)
                        self.ids.graph_container.add_widget(graphbox)

        Logger.debug("GRAPH: Graph [" + graphbox.labvar_name + "] is added, id: " + str(len(self.GraphArr) - 1) + "!")

    def ShiftNumbering(self, _id):
        for element in self.GraphArr:
            if element.id < _id:
                continue
            element.id -= 1

    def RemoveGraphById(self, _id):
        if len(self.GraphArr) > 0:

            temp = self.GraphArr[_id]

            if self.columns == 1:
                self.ids.graph_container.remove_widget(temp)
                self.GraphArr.remove(temp)

            if self.columns == 2:
                if len(self.GraphArr) == 1:
                    self.ids.graph_container.remove_widget(temp)
                    self.GraphArr.remove(temp)
                else:
                    if len(self.GraphArr) == 2:
                        self.ids.graph_container.remove_widget(temp)
                        self.GraphArr.remove(temp)
                        self.GraphArr[0].SetHeight(KivyApp.instance.ids.view_port.height)
                    else:
                        if len(self.GraphArr) > 2:
                            self.ids.graph_container.remove_widget(temp)
                            self.GraphArr.remove(temp)

            self.ShiftNumbering(_id)
            Logger.debug("GRAPH: Graph [" + temp.labvar_name + "] with id: " + str(_id) + " is removed!")

    def RemoveGraph(self):
        if len(self.GraphArr) > 0:

            temp = self.GraphArr[len(self.GraphArr) - 1]

            if self.columns == 1:
                self.ids.graph_container.remove_widget(temp)
                self.GraphArr.remove(temp)

            if self.columns == 2:
                if len(self.GraphArr) == 1:
                    self.ids.graph_container.remove_widget(temp)
                    self.GraphArr.remove(temp)
                else:
                    if len(self.GraphArr) == 2:
                        self.ids.graph_container.remove_widget(temp)
                        self.GraphArr.remove(temp)
                        self.GraphArr[0].SetHeight(KivyApp.instance.ids.view_port.height)
                    else:
                        if len(self.GraphArr) > 2:
                            self.ids.graph_container.remove_widget(temp)
                            self.GraphArr.remove(temp)

            Logger.debug("GRAPH: Graph [" + temp.labvar_name + "] is removed!")


class LaboratorClient(BoxLayout):
    endpoint = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.GraphContainer = GraphContainer()
        self.LabVarArr = []

    def Prepare(self, dt):
        self.ids.view_port.add_widget(self.GraphContainer)
        self.endpoint = msettings.get('LAST_IP')

    def AddGraph(self):
        self.GraphContainer.AddGraph()

    def RemoveGraph(self):
        self.GraphContainer.RemoveGraph()

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

    def Connect(self):
        try:
            client.Connect(self.endpoint)
            self.LabVarArr = self.LabVarArrConfigure(msettings.get('CONFIGURATION_PATH'))
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.endpoint_label.disabled = True
            self.ids.info_log.color = [0, 1, 0, 1]
            self.ids.info_log.text = "Connected!"
            Logger.debug("CONNECT: Connected!")
            self.ParseVars()
            self.ids.info_log.text = "Connected!"
            Logger.debug("CONNECT: Connected and parsed!")
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

    def Disconnect(self):
        client._isReconnecting = False
        try:
            client.Disconnect()
            self.ids.btn_disconnect.disabled = True
            self.ids.btn_connect.disabled = False
            self.ids.endpoint_label.disabled = False
            self.ids.info_log.color = 1, 0, 0, 1
            self.ids.info_log.text = "Disconnected!"
            Logger.debug("CONNECT: Disconnected!")
        except Exception:
            self.ids.btn_disconnect.disabled = False
            self.ids.btn_connect.disabled = True
            self.ids.endpoint_label.disabled = True
            self.ids.info_log.text = "Error while disconnecting..."
            Logger.info("CONNECT: Error while disconnecting...")

    def Update(self, dt):
        if client.isConnected():
            try:
                # Обновляем только те переменные, что есть в графиках
                for labvar in self.LabVarArr:
                    if self.GraphContainer.isContainsGraphWithName(labvar.name):
                        _value = client.get_node(labvar.node_id).get_value()
                        labvar.value = _value
                        labvar.WriteHistory(_value)
                # Заносим эти переменные в соответствующие графики
                for graph in self.GraphContainer.GraphArr:
                    if graph.labvar_name != "None":
                        for labvar in self.LabVarArr:
                            if labvar.name == graph.labvar_name:
                                graph.UpdateGardenGraph(labvar.GetHistory())
                                graph.SetLabVarValue(round(labvar.value, msettings.get('GRAPH_ROUND_DIGITS')))
            except Exception:
                client._isConnected = False
                client._isReconnecting = True
                self.ids.btn_disconnect.disabled = False
                self.ids.btn_connect.disabled = True
                self.ids.info_log.color = 1, 0, 0, 1
                self.ids.info_log.text = "Connection lost! Trying to reconnect..."
                Logger.debug("UPDATE: Connection lost! Trying to reconnect...")
                self.Reconnection(msettings.get('RECONNECTION_TIME'))


class KivyApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance = None
        self.settings_widget = None

    def on_stop(self):
        try:
            client.Disconnect()
        except Exception:
            Logger.error("KivyApp: Error while disconnecting on app stop!")

    def on_start(self):
        Clock.schedule_once(self.instance.Prepare, 1)
        Clock.schedule_interval(self.instance.Update, int(msettings.get('KIVY_UPDATE_FUNCTION_TIME')))

    @staticmethod
    def LoadKV():
        for filename in os.listdir(os.path.join("libs", "kv")):
            Builder.load_file(os.path.join("libs", "kv", filename))

    def build(self):
        self.LoadKV()
        laborator = LaboratorClient()
        self.instance = laborator
        self.use_kivy_settings = False
        return laborator

    def build_config(self, config):
        config.setdefaults('allSettings', settings_defaults)
        msettings.instance = self.config

    def build_settings(self, settings):
        self.settings_widget = settings
        settings.add_json_panel('Основные настройки', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        print(config, section, key, value)


KivyApp = KivyApp()

# Программа получает на вход готовые приведенные параметры, выводит их графики,
# считает косвенные параметры, считает спектральные параметры, среднее значение...

# TODO Установить kivy в редактируем режиме
# TODO Реализовать свой стиль для кнопок, лэйблов, и т.д. для унификации интерфейса
# TODO Реализовать сохранение и подгрузку лэйаута
# TODO Реализовать индивидуальные настройки для графиков
# TODO Научиться считать косвенные параметры по измеряемым и выводить на график
# TODO Научиться делать статистический анализ
# TODO Научиться подключаться к LabView
