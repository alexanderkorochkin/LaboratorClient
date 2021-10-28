import socket

# from opcua import Client
from kivy.app import App
# from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


def get_local_ip():
    return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
            [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


class LaboratorClientApp(App):

    def build(self):
        layoutStart = BoxLayout(orientation='vertical')
        ip_label = Label(text=get_local_ip(), font_size=12)
        text_label = Label(text=get_local_ip(), font_size=12)
        layoutStart.add_widget(ip_label)
        layoutStart.add_widget(text_label)
        return layoutStart

    def on_start(self):
        pass

    def on_stop(self):
        pass


if __name__ == "__main__":
    LaboratorClientApp().run()
