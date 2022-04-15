from kivy.uix.label import Label
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty, ListProperty
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.logger import Logger


class TouchableLabel(ButtonBehavior, Label):
    background_color = ListProperty((0.5, 0.5, 0.5, 0.5))
    background_color_rel = ListProperty((0.5, 0.5, 0.5, 0.5))
    background_color_press = ListProperty((0.5, 0.5, 0.5, 0.8))
    border_color = ListProperty((0, 0, 0, 1))
    text = StringProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def Pressed(self):
        self.background_color = self.background_color_press

    def Released(self):
        self.background_color = self.background_color_rel
        # Logger.debug("BTN_RELEASED: " + str(self) + ", pos: " + str(self.pos) + ", label_text: " + self.text)

    def GetText(self):
        return self.text

