import os
from settings.config import *

import opcua
from kivy.app import App
from libs.opcua.opcuaclient import client
from libs.toolConfigurator import LabVar
from libs.touchablelabel import TouchableLabel

from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, partial
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock
from kivy import Config
from kivy.logger import Logger, LOG_LEVELS
from kivy.lang import Builder

Logger.setLevel(LOG_LEVELS["debug"])
Config.set('graphics', 'multisamples', '0')


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
            element.height = 0.3 * KivyApp.instance.ids.view_port.height


class ListLabValPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.isOpenedOnce = False

    def open(self, _id,  *largs, **kwargs):
        if not self.isOpenedOnce:
            for element in KivyApp.instance.LabVarArr:
                temp = TouchableLabel()
                temp.text = element.name
                temp.size_hint_y = None
                temp.size = [temp.size[0], '50sp']
                temp.id = _id
                temp.bind(on_release=self.SelectedVarCallback)
                self.ids.list_box.add_widget(temp)
            self.isOpenedOnce = True
        super(ListLabValPopup, self).open()

    def SelectedVarCallback(self, instance):
        KivyApp.instance.GraphContainer.GraphArr[instance.id].SetLabName(instance.text)
        self.dismiss()


class GraphBox(BoxLayout):
    id = NumericProperty(None)
    lab_value = NumericProperty(None)
    lab_name = StringProperty("None")

    def __init__(self, _cols, _id, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = [1, None]
        self.id = _id
        self.lab_value = 0

        if _cols == 1:
            self.height = (1/3) * KivyApp.instance.ids.view_port.height
        else:
            if _cols == 2:
                if len(KivyApp.instance.GraphContainer.GraphArr) == 0:
                    self.height = KivyApp.instance.ids.view_port.height
                else:
                    self.height = 0.5 * KivyApp.instance.ids.view_port.height

    def RemoveMe(self):
        KivyApp.instance.GraphContainer.RemoveGraphById(self.id)

    def SetHeight(self, height):
        self.height = height

    def SetLabValue(self, lab_value):
        self.lab_value = lab_value

    def SetLabName(self, lab_name):
        self.lab_name = lab_name


class GraphContainer(BoxLayout):
    container = ObjectProperty(None)
    scrollview = ObjectProperty(None)
    columns = NumericProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=ResizeGraphCallback)
        self.GraphArr = []
        self.columns = 1

    def AddGraph(self):

        if self.columns == 1:
            graph = GraphBox(self.columns, len(self.GraphArr))
            self.GraphArr.append(graph)
            self.ids.graph_container.add_widget(graph)

        if self.columns == 2:
            if len(self.GraphArr) == 0:
                graph = GraphBox(self.columns, len(self.GraphArr))
                self.GraphArr.append(graph)
                self.ids.graph_container.add_widget(graph)
                self.GraphArr[0].SetHeight(KivyApp.instance.ids.view_port.height)
            else:
                if len(self.GraphArr) == 1:
                    graph = GraphBox(self.columns, len(self.GraphArr))
                    self.GraphArr.append(graph)
                    self.ids.graph_container.add_widget(graph)
                    self.GraphArr[0].SetHeight(0.5 * KivyApp.instance.ids.view_port.height)
                else:
                    if len(self.GraphArr) > 1:
                        graph = GraphBox(self.columns, len(self.GraphArr))
                        self.GraphArr.append(graph)
                        self.ids.graph_container.add_widget(graph)

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


class LaboratorClient(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.GraphContainer = GraphContainer()
        self.LabVarArr = []

    def Prepare(self, dt):
        self.ids.view_port.add_widget(self.GraphContainer)

    def AddGraph(self):
        self.GraphContainer.AddGraph()

    def RemoveGraph(self):
        self.GraphContainer.RemoveGraph()

    def Update(self, dt):
        if client.isConnected():
            for lab_var in self.LabVarArr:
                _value = client.get_node(lab_var.node_id).get_value()
                lab_var.WriteHistory(_value)
                lab_var.value = _value

            for graph in self.GraphContainer.GraphArr:
                for lab_var in self.LabVarArr:
                    if lab_var.browse_name.find(str(graph.lab_name)) != -1:
                        graph.SetLabValue(round(lab_var.value, 2))

    @staticmethod
    def LabVarArrConfigure(path):
        arr = []
        file = open(path, "r")
        for line in file:
            index, port, name, *multiplier = line.split("\t", 4)
            arr.append(LabVar(0, index, name, port, multiplier))
        file.close()
        return arr

    def Connect(self):
        try:
            client.Connect(self.ids.endpoint_label.text)
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.info_log.color = [0, 1, 0, 1]
            self.ids.info_log.text = "Connected!"
        except Exception:
            self.ids.btn_connect.disabled = False
            self.ids.btn_disconnect.disabled = True
            self.ids.info_log.text = "Error while connecting..."

        self.LabVarArr = self.LabVarArrConfigure(os.path.join("settings", "databaseconfig.txt"))
        for var in self.LabVarArr:
            for child in client.lab_node.get_children():
                if str(child.get_browse_name()).find(str(var.name)) != -1:
                    var.browse_name = str(child.get_browse_name())
                    var.node_id = str(child)
                    print("[" + var.name + "], the browse_name is: [" + str(var.browse_name) + "], NodeId: [" + var.node_id + "]")

        self.ids.info_log.text = "Connected and parsed!"

    def Disconnect(self):
        try:
            client.Disconnect()
            self.ids.btn_disconnect.disabled = True
            self.ids.btn_connect.disabled = False
            self.ids.info_log.color = 1, 0, 0, 1
            self.ids.info_log.text = "Disconnected!"
        except Exception:
            self.ids.btn_disconnect.disabled = False
            self.ids.info_log.text = "Error while disconnecting..."


class KivyApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance = None

    def on_stop(self):
        if client.isConnected():
            client.Disconnect()

    def on_start(self):
        Clock.schedule_once(self.instance.Prepare, 1)
        Clock.schedule_interval(self.instance.Update, 1)

    @staticmethod
    def LoadKV():
        for filename in os.listdir(os.path.join("libs", "kv")):
            Builder.load_file(os.path.join("libs", "kv", filename))

    def build(self):
        self.LoadKV()
        laborator = LaboratorClient()
        self.instance = laborator
        return laborator


KivyApp = KivyApp()
