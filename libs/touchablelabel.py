from kivy.uix.label import Label
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty, ListProperty
from kivy.uix.behaviors.button import ButtonBehavior


class TouchableLabel(ButtonBehavior, Label):
    background_color = ListProperty((0.5, 0.5, 0.5, 0.5))
    background_color_rel = ListProperty((0.5, 0.5, 0.5, 0.5))
    background_color_press = ListProperty((0.5, 0.5, 0.5, 0.8))
    border_color = ListProperty((0, 0, 0, 1))
    isPressed = False
    text = StringProperty("None")
    id = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def Pressed(self):
        self.background_color = self.background_color_press
        print("RELEASED: [", self, "] with label_text: ", self.text)

    def Released(self):
        self.background_color = self.background_color_rel

    def GetText(self):
        return self.text

