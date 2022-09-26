from libs.kivyapp import KivyApp
from kivy.uix.popup import Popup
from kivy.properties import StringProperty


class EnterEndpointPopup(Popup):
    endpoint = StringProperty('None')

    def open(self, _endpoint, *largs, **kwargs):
        self.endpoint = _endpoint
        super(EnterEndpointPopup, self).open()

    def SaveEndpoint(self):
        KivyApp.instance.endpoint = str(self.ids.endpoint_input.text)
        self.dismiss()
