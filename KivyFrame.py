from functools import partial

from kivy.app import App

from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.lang import Builder
from OPCUAClient import client


def ResizeCallback(instance, value):
    if "KivyFrame.GraphContainer" in str(instance):
        if value[0] > value[1]:
            instance.ids.graph_container.cols = 2
        if value[0] <= value[1]:
            instance.ids.graph_container.cols = 1


class Graph(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = [1, None]
        self.height = 250


class GraphContainer(BoxLayout):
    container = ObjectProperty(None)
    scrollview = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=ResizeCallback)
        self.GraphArr = []

    def adjust_scroll(self, bottom, dt):
        vp_height = self.ids.scroll_view.viewport_size[1]
        sv_height = self.ids.scroll_view.height
        self.ids.scroll_view.scroll_y = bottom / (vp_height - sv_height)

    def AddGraph(self):
        vp_height = self.ids.scroll_view.viewport_size[1]
        sv_height = self.ids.scroll_view.height

        graph = Graph()
        self.GraphArr.append(graph)
        self.ids.graph_container.add_widget(graph)

        if vp_height > sv_height:  # otherwise there is no scrolling
            # calculate y value of bottom of scrollview in the viewport
            scroll = self.ids.scroll_view.scroll_y
            bottom = scroll * (vp_height - sv_height)

            # use Clock.schedule_once because we need updated viewport height
            # this assumes that new widgets are added at the bottom
            # so the current bottom must increase by the widget height to maintain position
            Clock.schedule_once(partial(self.adjust_scroll, bottom + graph.height), -1)

    def RemoveGraph(self):
        if len(self.GraphArr) > 0:
            vp_height = self.ids.scroll_view.viewport_size[1]
            sv_height = self.ids.scroll_view.height

            temp = self.GraphArr[len(self.GraphArr) - 1]
            self.ids.graph_container.remove_widget(temp)
            self.GraphArr.remove(temp)

            if vp_height > sv_height:  # otherwise there is no scrolling
                # calculate y value of bottom of scrollview in the viewport
                scroll = self.ids.scroll_view.scroll_y
                bottom = scroll * (vp_height - sv_height)

                # use Clock.schedule_once because we need updated viewport height
                # this assumes that new widgets are added at the bottom
                # so the current bottom must increase by the widget height to maintain position
                Clock.schedule_once(partial(self.adjust_scroll, bottom - temp.height), -1)


class LaboratorClientMain(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.GraphContainer = GraphContainer()

    def Prepare(self, dt):
        self.ids.main_stack.add_widget(self.GraphContainer)

    def AddGraph(self):
        self.GraphContainer.AddGraph()

    def RemoveGraph(self):
        self.GraphContainer.RemoveGraph()

    def Update(self, dt):
        pass

    def Connect(self):
        try:
            client.Connect(self.ids.text_input.text)
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.info_log.color = [0, 1, 0, 1]
            self.ids.info_log.text = "Connected!"
        except Exception:
            self.ids.btn_connect.disabled = False
            self.ids.btn_disconnect.disabled = True
            self.ids.info_log.text = "Error while connecting..."

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


class KivyFrameApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_stop(self):
        if client.isConnected():
            client.Disconnect()

    def build(self):
        laborator = LaboratorClientMain()
        Clock.schedule_once(laborator.Prepare, -1)
        Clock.schedule_interval(laborator.Update, 1)
        return laborator


KivyFrame = KivyFrameApp()
