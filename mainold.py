from opcua import Client
from kivy.app import App
from kivy.clock import Clock
# from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from kivy.lang import Builder

Builder.load_file('main.kv')


class ClientOPCUA(Client):

    def __init__(self, url, **kwargs):
        super().__init__(url)
        self.connect()
        self.root = self.get_root_node()
        self.myvar = self.root.get_child(["0:Objects", "2:lab1", "2:MyVariable"])
        self.lab1 = self.root.get_child(["0:Objects", "2:lab1"])

    def dDisconnect(self):
        self.disconnect()


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
    Clienter = ClientOPCUA("opc.tcp://" + "192.168.1.22" + ":4840")
    Box = BoxIncoming()

    def build(self):
        return self.Box

    def on_start(self):
        Clock.schedule_interval(update_it, 1)

    def on_stop(self):
        self.Clienter.dDisconnect()


if __name__ == "__main__":
    LaboratorClientApp().run()
