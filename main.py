import socket

from opcua import Client
from kivy.app import App
from kivy.clock import Clock
# from kivy.uix.button import Button
# from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
# from kivy.uix.label import Label
from kivy.properties import StringProperty
from kivy.lang import Builder

Builder.load_file('main.kv')


class ClientUPCUA(Client):

    def __init__(self, url, **kwargs):
        super().__init__(url)
        self.connect()
        self.root = self.get_root_node()
        self.myvar = self.root.get_child(["0:Objects", "2:MyObject", "2:MyVariable"])
        self.obj = self.root.get_child(["0:Objects", "2:MyObject"])


class BoxIncoming(Widget):
    text_incoming = StringProperty()

    def __init__(self, **kwargs):
        super(BoxIncoming, self).__init__(**kwargs)
        self.text_incoming = "none"

    def changeText(self, text):
        self.text_incoming = text


def update_it(self):
    text = str(LaboratorClientApp().Clienter.myvar.get_value())
    LaboratorClientApp().Box.changeText(text)


class LaboratorClientApp(App):
    Clienter = ClientUPCUA("opc.tcp://" + "192.168.1.67" + ":4840/freeopcua/server/")
    Box = BoxIncoming()

    def build(self):
        return self.Box

    def on_start(self):
        Clock.schedule_interval(update_it, 1)

    def on_stop(self):
        pass


if __name__ == "__main__":
    LaboratorClientApp().run()
