from libs.kivyapp import KivyApp
from kivy.uix.popup import Popup
from kivy.properties import StringProperty


class EnterEndpointPopup(Popup):
    endpoint = StringProperty("opc.tcp://")

    def SaveEndpoint(self):
        KivyApp.instance.ids.endpoint_label.text = str(self.ids.endpoint_input.text)
        self.dismiss()