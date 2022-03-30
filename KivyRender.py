import time

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import ObjectProperty


from OPCUAClient import client
from urllib.parse import urlparse


CurrentLayout = "IPEnterWindow"


class WindowManager(ScreenManager):
    pass


class MainScreen(Screen):

    label_text = ObjectProperty(None)

    class UpdateIt(object):

        def __init__(self, instance):
            super().__init__()
            self._instance = instance

        def datachange_notification(self, node, val, data):
            self._instance.ids.label_text.text = str(val)

    def Connect(self):
        try:
            client.Connect()
            handler = self.UpdateIt(self)
            sub = client.create_subscription(1000, handler)
            sub.subscribe_data_change(client.myVar)
        except Exception:
            self.ids.label_text.text = "Error while connecting..."
            self.ids.button_connect.disabled = False


class IPEnterScreen(Screen):

    is_focused_once = 0

    def FocusedOnce(self):
        if self.is_focused_once == 0:
            self.ids.text_endpoint.foreground_color = (0, 0, 0, 1)
            self.ids.text_endpoint.text = "opc.tcp://" + "192.168.1.22" + ":4840"
            self.is_focused_once = 1

    def ApplyURL(self):
        client.server_url = urlparse(self.ids.text_endpoint.text)
        client.url = urlparse(self.ids.text_endpoint.text)


kv = Builder.load_file('KivyRender.kv')


class KivyRenderApp(App):

    def __init__(self):
        super().__init__()

    def on_stop(self):
        if client.isConnected():
            client.close()

    # Обновление всех данных
    def update_data(self):
        pass

    # Строим GUI
    def build(self):
            return kv
