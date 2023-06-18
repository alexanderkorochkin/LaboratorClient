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
    display_name = StringProperty('None')
    labvar_name = StringProperty('None')

    def __init__(self, main_app=None, settings=None, **kwargs):
        super(ControlButton, self).__init__(**kwargs)
        self.accented = False
        self.isHolden = False
        self.always_release = False
        self.main_app = main_app
        self.doUpdate = True
        self.isPressed = False

        self.line_color = [0, 0, 0, 0]
        self.line_width = dp(1)

        self._event = None
        self.timeout = msettings.get('KIVY_HOLD_TIME')

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
        self.ids.control_icon.icon = self.icon_states[0]

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

    def Update(self, *args):
        if self.doUpdate:
            if self.s['NAME'] != 'None':
                value = str_to_variable(client.GetValueFromName(self.s['NAME']))
                if isinstance(value, bool):
                    self.control_state = value
                    self.ids.control_icon.icon = self.icon_states[int(value)]
                    self.md_bg_color = self.bg_states[int(value)]
                    self.ids.control_icon.color = self.text_states[int(value)]
                    self.ids.control_text.color = self.text_states[int(value)]
                else:
                    Logger.debug(f'ControlUpdate: Variable {self.s["NAME"]} is not a boolean!')
                    self.control_state = True
                    self.ids.control_icon.icon = 'alert-circle-outline'
                    self.md_bg_color = [0.8, 0, 0, 0.8]
                    self.ids.control_icon.color = self.text_states[1]
                    self.ids.control_text.color = self.text_states[1]

    def on_dict(self, tag, value):
        if tag == 'DISPLAY_NAME':
            self.display_name = value
        if tag == 'NAME':
            self.labvar_name = value
        if tag == 'ICON_ON':
            self.icon_states[1] = value
            self.ids.control_icon.icon = self.icon_states[self.control_state]
        if tag == 'ICON_OFF':
            self.icon_states[0] = value
            self.ids.control_icon.icon = self.icon_states[self.control_state]

    def AccentIt(self):
        self.accented = True
        color = self.main_app.theme_cls.primary_color
        color[3] = 0.1
        anim = Animation(md_bg_color=color, duration=0.1)
        anim.start(self)
        anim = Animation(line_color=self.main_app.theme_cls.primary_color, duration=0.1)
        anim.start(self)

    def UnAccentIt(self):
        self.accented = False
        anim = Animation(md_bg_color=self.main_app.theme_cls.bg_light, duration=0.1)
        anim.start(self)
        anim = Animation(line_color=[0, 0, 0, 0], duration=0.1)
        anim.start(self)

    def RemoveMe(self):
        self.main_app.kivy_instance.RemoveControl(self)

    def CheckCollisionName(self, labvar_name):
        pass

    def BlockUpdate(self, *args):
        self.main_app.kivy_instance.doUpdateControls = False

    def UnblockUpdate(self, *args):
        self.main_app.kivy_instance.doUpdateControls = True

    def _cancel(self):
        if self._event:
            self._event.cancel()

    def on_press(self):
        self.BlockUpdate()
        self._cancel()
        self._event = Clock.schedule_once(self.on_hold, self.timeout)

    def on_touch_up(self, touch):
        self.UnblockUpdate()
        super().on_touch_up(touch)

    def on_hold(self, *args):
        self.isHolden = True
        self.AccentIt()
        self.main_app.dialogControlSettings.Open(self, help_id='control_settings')

    def on_release(self):
        self._cancel()
        if not self.isHolden:
            # self.control_state = not self.control_state
            client.SetValueOnServer(self.s['NAME'], str(not self.control_state))
            self.UnblockUpdate()
        else:
            self.isHolden = False
