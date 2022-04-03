from kivy.app import App
from OPCUAClient import client

from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.lang.builder import Builder
from kivy.logger import Logger, LOG_LEVELS

Logger.setLevel(LOG_LEVELS["debug"])


class LaboratorClientMain(BoxLayout):
    graph_container_main = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("FUCK4")

    def AddGraph(self):
        self.graph_container_main.AddGraph()

    def RemoveGraph(self):
        self.graph_container_main.RemoveGraph()

    def Update(self, dt):
        pass

    def Connect(self):
        pass

    def Disconnect(self):
        pass


class KivyFrameApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance = None
        print("FUCK3")

    def on_stop(self):
        if client.isConnected():
            client.Disconnect()

    def on_start(self):
        print("FUCK2")
        Clock.schedule_interval(self.instance.Update, 1)

    def build(self):
        print("FUCK1")
        laborator = LaboratorClientMain()
        self.instance = laborator
        return laborator


KivyFrame = KivyFrameApp()
