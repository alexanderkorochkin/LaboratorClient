from kivy.app import App
from OPCUAClient import client

from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy import Config
from kivy.logger import Logger, LOG_LEVELS

Logger.setLevel(LOG_LEVELS["debug"])
Config.set('graphics', 'multisamples', '0')


def ResizeGraphCallback(instance, value):
    if value[0] > value[1]:
        KivyFrame.instance.GraphContainer.columns = 2
        for element in KivyFrame.instance.GraphContainer.GraphArr:
            element.height = 0.5 * KivyFrame.instance.ids.view_port.height
    if value[0] <= value[1]:
        KivyFrame.instance.GraphContainer.columns = 1
        for element in KivyFrame.instance.GraphContainer.GraphArr:
            element.height = 0.3 * KivyFrame.instance.ids.view_port.height


class Graph(Button):
    def __init__(self, cols, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = [1, None]
        if cols == 1:
            self.height = 0.3 * KivyFrame.instance.ids.view_port.height
        else:
            if cols == 2:
                if len(KivyFrame.instance.GraphContainer.GraphArr) == 0:
                    self.height = KivyFrame.instance.ids.view_port.height
                else:
                    self.height = 0.5 * KivyFrame.instance.ids.view_port.height

    def SetHeight(self, height):
        self.height = height


class GraphContainer(BoxLayout):
    container = ObjectProperty(None)
    scrollview = ObjectProperty(None)
    columns = NumericProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=ResizeGraphCallback)
        self.GraphArr = []
        self.columns = 1

    # def adjust_scroll(self, bottom, dt):
    #     vp_height = self.ids.scroll_view.viewport_size[1]
    #     sv_height = self.ids.scroll_view.height
    #     print(bottom, vp_height, sv_height)
    #     self.ids.scroll_view.scroll_y = bottom / (vp_height - sv_height)

    def AddGraph(self):
        vp_height = self.ids.scroll_view.viewport_size[1]
        sv_height = self.ids.scroll_view.height

        if self.columns == 1:
            graph = Graph(self.columns)
            self.GraphArr.append(graph)
            self.ids.graph_container.add_widget(graph)

        if self.columns == 2:
            if len(self.GraphArr) == 0:
                graph = Graph(self.columns)
                self.GraphArr.append(graph)
                self.ids.graph_container.add_widget(graph)
                self.GraphArr[0].SetHeight(KivyFrame.instance.ids.view_port.height)
            else:
                if len(self.GraphArr) == 1:
                    graph = Graph(self.columns)
                    self.GraphArr.append(graph)
                    self.ids.graph_container.add_widget(graph)
                    self.GraphArr[0].SetHeight(0.5 * KivyFrame.instance.ids.view_port.height)
                else:
                    if len(self.GraphArr) > 1:
                        graph = Graph(self.columns)
                        self.GraphArr.append(graph)
                        self.ids.graph_container.add_widget(graph)

        # if vp_height > sv_height:  # otherwise there is no scrolling
        #     # calculate y value of bottom of scrollview in the viewport
        #     scroll = self.ids.scroll_view.scroll_y
        #     bottom = scroll * (vp_height - sv_height)
        #
        #     # use Clock.schedule_once because we need updated viewport height
        #     # this assumes that new widgets are added at the bottom
        #     # so the current bottom must increase by the widget height to maintain position
        #     Clock.schedule_once(partial(self.adjust_scroll, bottom + graph.height), 0)

    def RemoveGraph(self):
        if len(self.GraphArr) > 0:
            vp_height = self.ids.scroll_view.viewport_size[1]
            sv_height = self.ids.scroll_view.height

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
                        self.GraphArr[0].SetHeight(KivyFrame.instance.ids.view_port.height)
                    else:
                        if len(self.GraphArr) > 2:
                            self.ids.graph_container.remove_widget(temp)
                            self.GraphArr.remove(temp)

            # if vp_height > sv_height:  # otherwise there is no scrolling
            #     # calculate y value of bottom of scrollview in the viewport
            #     scroll = self.ids.scroll_view.scroll_y
            #     bottom = scroll / (vp_height - sv_height)
            #
            #     # use Clock.schedule_once because we need updated viewport height
            #     # this assumes that new widgets are added at the bottom
            #     # so the current bottom must decrease by the widget height to maintain position
            #     Clock.schedule_once(partial(self.adjust_scroll, bottom - temp.height), 0)


class LaboratorClientMain(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.GraphContainer = GraphContainer()

    def Prepare(self, dt):
        self.ids.view_port.add_widget(self.GraphContainer)

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
        self.instance = None

    def on_stop(self):
        if client.isConnected():
            client.Disconnect()

    def on_start(self):
        Clock.schedule_once(self.instance.Prepare, 1)
        Clock.schedule_interval(self.instance.Update, 1)

    def build(self):
        laborator = LaboratorClientMain()
        self.instance = laborator
        return laborator


KivyFrame = KivyFrameApp()
