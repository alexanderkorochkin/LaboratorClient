import uuid

from kivy.properties import StringProperty, ColorProperty, BooleanProperty, OptionProperty, ReferenceListProperty, \
    ListProperty
from kivymd.uix.button import MDFillRoundFlatIconButton, MDRoundFlatIconButton, MDRectangleFlatIconButton, BaseButton

from libs.opcua.opcuaclient import client
from libs.settings.settingsJSON import *
from libs.utils import *


class ControlButton(BaseButton):

    doSpacing = BooleanProperty(True)
    control_state = BooleanProperty(False)
    icon_states = ListProperty(['', ''])
    mode = StringProperty('')
    text = StringProperty('')

    def __init__(self, main_app=None, settings=None, **kwargs):
        super(ControlButton, self).__init__(**kwargs)
        self.isHolden = False
        self.always_release = True
        self.main_app = main_app

        self.bind(control_state=self.on_control_state)

        self.bg_states = [self.main_app.theme_cls.bg_light, self.main_app.theme_cls.primary_color]
        self.text_states = [self.main_app.theme_cls.text_color, self.main_app.theme_cls.opposite_text_color]

        self._radius = self.main_app.main_radius

        self.s = DictCallback(controls_settings_defaults.copy(), cls=self, callback=self.on_dict, log=True)

        if settings:
            self.ApplyLayout(settings)
        else:
            self.ApplyLayout(self.s)
            self.s['HASH'] = uuid.uuid4().hex

        self.s.log = True

    def apply_setting(self, tag, settings):
        try:
            self.s[tag] = settings[tag]
        except Exception:
            return

    def apply_with_function(self, tag, settings, function):
        try:
            function(settings[tag])
        except Exception:
            return

    def ApplyLayout(self, settings):
        for tag in settings.keys():
            self.apply_setting(tag, settings)

    def on_control_state(self, *args):
        new_state = args[1]
        self.ids.control_icon.icon = self.icon_states[int(new_state)]
        self.md_bg_color = self.bg_states[int(new_state)]
        self.ids.control_icon.color = self.text_states[int(new_state)]
        self.ids.control_text.color = self.text_states[int(new_state)]

    def on_dict(self, tag, value):
        if tag == 'NAME':
            self.text = value
        if tag == 'MODE':
            if value == 'TOGGLE':
                self.mode = 'Toggle'
            elif value == 'HOLD':
                self.mode = 'Hold'
        if tag == 'ICON_ON':
            self.icon_states[1] = value
            self.on_control_state(self, self.control_state)
        if tag == 'ICON_OFF':
            self.icon_states[0] = value
            self.on_control_state(self, self.control_state)
        if tag == 'DEFAULT_STATE':
            self.control_state = value

    def on_press(self, *args):
        if self.s['MODE'] == 'HOLD':
            self.isHolden = True
            self.control_state = not self.control_state

    def on_release(self):
        if self.isHolden:
            self.isHolden = False
            self.control_state = not self.control_state
        else:
            # client.SetValueOnServer('test::TEST0', 'True')
            if self.s['MODE'] == 'TOGGLE':
                self.control_state = not self.control_state
