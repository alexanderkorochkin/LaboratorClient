from libs.settings.settingsJSON import msettings
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.behaviors import TouchRippleBehavior
from kivy.uix.button import Button
from kivy.utils import get_color_from_hex


class RectangleFlatButton(TouchRippleBehavior, Button):
    primary_color = get_color_from_hex(msettings.get('THEME_MAIN_COLOR'))
    ripple_color_base = get_color_from_hex(msettings.get('THEME_SECOND_COLOR'))
    disabled = BooleanProperty(False)

    def on_touch_down(self, touch):
        if not self.disabled:
            collide_point = self.collide_point(touch.x, touch.y)
            if collide_point:
                touch.grab(self)
                self.ripple_show(touch)
            return super(RectangleFlatButton, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.ripple_fade()
        return super(RectangleFlatButton, self).on_touch_up(touch)


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

