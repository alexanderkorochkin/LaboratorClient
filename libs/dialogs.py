import math

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.pickers import MDColorPicker

from kivy.core.window import Window

from typing import Union

from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ObjectProperty, OptionProperty
from kivymd.uix.list.list import OneLineAvatarIconListItem

from kivy.utils import get_hex_from_color
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.textfield import MDTextField

from libs.opcua.opcuaclient import client
from libs.settings.settingsJSON import *


class MDDialogFix(MDDialog):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(size=self.update_height,
                    on_maximize=self.update_height,
                    on_restore=self.update_height,
                    on_minimize=self.update_height)
        Window.bind(on_maximize=self.update_width,
                    on_restore=self.update_width,
                    on_minimize=self.update_width)
        self.MINIMAL_WIDTH_VERTICAL = msettings.get('DIALOG_MINIMUM_HEIGHT_VERTICAL')
        self.MAXIMUM_WIDTH_HORIZONTAL = msettings.get('DIALOG_MAXIMUM_HEIGHT_HORIZONTAL')

    def update_width(self, *args) -> None:
        if Window.width - dp(48) < self.MINIMAL_WIDTH_VERTICAL:
            self.width = Window.width - dp(48)
        elif self.MINIMAL_WIDTH_VERTICAL <= Window.width - dp(48) < self.MAXIMUM_WIDTH_HORIZONTAL:
            self.width = self.MINIMAL_WIDTH_VERTICAL
        else:
            self.width = self.MAXIMUM_WIDTH_HORIZONTAL

    def update_height(self, *args) -> None:
        self._spacer_top = \
            Window.height - dp(48) - dp(100) \
            if self.content_cls.ids.content_cls_box.height + dp(50) > Window.height - dp(48) - dp(100) \
            else self.content_cls.ids.content_cls_box.height + dp(50)


class MDDialogSizer(MDDialog):
    def __init__(self, app, fixed=False, **kwargs):
        super().__init__(**kwargs)
        Window.bind(size=self.update_height,
                    on_maximize=self.update_height,
                    on_restore=self.update_height,
                    on_minimize=self.update_height)
        Window.bind(on_maximize=self.update_width,
                    on_restore=self.update_width,
                    on_minimize=self.update_width)
        self.fixed = fixed
        self.app = app
        self.MAXIMUM_WIDTH = dp(500)
        self.DIALOG_MINIMUM_HEIGHT_VERTICAL = msettings.get('DIALOG_MINIMUM_HEIGHT_VERTICAL')
        self.DIALOG_MAXIMUM_HEIGHT_HORIZONTAL = msettings.get('DIALOG_MAXIMUM_HEIGHT_HORIZONTAL')

    def update_width(self, *args) -> None:
        if not self.fixed:
            if Window.width - dp(48) < self.MAXIMUM_WIDTH:
                self.width = Window.width - dp(48)
            elif self.MAXIMUM_WIDTH <= Window.width - dp(48):
                self.width = self.MAXIMUM_WIDTH
        else:
            if Window.width - dp(48) < self.DIALOG_MINIMUM_HEIGHT_VERTICAL:
                self.width = Window.width - dp(48)
            elif self.DIALOG_MINIMUM_HEIGHT_VERTICAL <= Window.width - dp(48) < self.DIALOG_MAXIMUM_HEIGHT_HORIZONTAL:
                self.width = self.DIALOG_MINIMUM_HEIGHT_VERTICAL
            else:
                self.width = self.DIALOG_MAXIMUM_HEIGHT_HORIZONTAL

    def update_height(self, *args) -> None:
        if self.type == 'confirmation':
            self.ids.container.height = Window.height - dp(48) - dp(100)
            self.ids.scroll.height = Window.height - dp(48) - dp(100) - dp(100)
        else:
            if not self.fixed:
                self._spacer_top = \
                    Window.height - dp(48) - dp(100) \
                    if self.content_cls.height + dp(20) > Window.height - dp(48) - dp(100) \
                    else self.content_cls.height + dp(20)
            else:
                self._spacer_top = \
                    Window.height - dp(48) - dp(100) \
                        if self.content_cls.ids.content_cls_box.height + dp(50) > Window.height - dp(48) - dp(100) \
                        else self.content_cls.ids.content_cls_box.height + dp(50)


class LDialogGraphSettingsContent(MDBoxLayout):

    app = ObjectProperty(None)

    labvar_name = StringProperty("None")
    mode = StringProperty("NORMAL")
    max_spectral_buffer_size = NumericProperty(0)
    show_avg_value = BooleanProperty(False)
    show_main_value = BooleanProperty(False)
    show_avg_graph = BooleanProperty(False)
    show_intime_graph = BooleanProperty(False)
    show_main_graph = BooleanProperty(False)
    main_graph_color = StringProperty('#FFFFFF')
    avg_color = StringProperty('#FFFFFF')
    intime_graph_color = StringProperty('#FFFFFF')
    graph_round_digits = NumericProperty(0)
    label_x = BooleanProperty(False)
    label_y = BooleanProperty(False)
    expression = StringProperty('')

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.instance = None

    def Toggle(self, tag):
        if tag == 'GRAPH_LABEL_X':
            self.label_x = not self.label_x
            self.instance.s['GRAPH_LABEL_X'] = self.label_x
        if tag == 'GRAPH_LABEL_Y':
            self.label_y = not self.label_y
            self.instance.s['GRAPH_LABEL_Y'] = self.label_y
        if tag == 'SHOW_MAIN_VALUE':
            self.instance.Toggle('SHOW_MAIN_VALUE')
            self.show_main_value = self.instance.s['SHOW_MAIN_VALUE']
        if tag == 'SHOW_AVG_VALUE':
            self.instance.Toggle('SHOW_AVG_VALUE')
            self.show_avg_value = self.instance.s['SHOW_AVG_VALUE']
        if tag == 'SHOW_MAIN_GRAPH':
            self.instance.Toggle('SHOW_MAIN_GRAPH', True)
            self.instance.gardenGraph.TogglePlot()
            self.show_main_graph = self.instance.s['SHOW_MAIN_GRAPH']
        if tag == 'SHOW_AVG_GRAPH':
            self.instance.Toggle('SHOW_AVG_GRAPH', True)
            self.instance.gardenGraph.TogglePlot()
            self.show_avg_graph = self.instance.s['SHOW_AVG_GRAPH']
        if tag == 'SHOW_INTIME_GRAPH':
            self.instance.Toggle('SHOW_INTIME_GRAPH', True)
            self.instance.gardenGraph.TogglePlot()
            self.show_intime_graph = self.instance.s['SHOW_INTIME_GRAPH']
        if tag == 'NEXT_MODE':
            if self.mode == 'NORMAL':
                self.instance.s['MODE'] = 'SPECTRAL'
                self.mode = 'SPECTRAL'
            else:
                self.instance.s['MODE'] = 'NORMAL'
                self.mode = 'NORMAL'
            self.app.dialogGraphSettings.dialog.title = self.mode

    def SelectVariable(self, name):
        if name == 'Новое выражение':
            self.app.dialogTextInput.Open('name', 'Название переменной', 'SAVE', 'CANCEL', self.Rename, '', 'Имя должно быть уникальным', self.instance)
        else:
            self.ChangeDirectName(name)

    def ChangeDirectName(self, new_name):
        self.labvar_name = new_name
        self.app.dialogGraphSettings.dialog.title = self.labvar_name
        self.instance.s['NAME'] = self.labvar_name

    def SetPrecision(self, precision):
        self.graph_round_digits = int(precision)
        self.instance.s['GRAPH_ROUND_DIGITS'] = int(precision)

    def SetSpectralSize(self, size):
        self.max_spectral_buffer_size = int(size)
        self.instance.s['MAX_SPECTRAL_BUFFER_SIZE'] = int(size)

    def SetExpression(self, expression):
        self.expression = expression
        self.instance.s['EXPRESSION'] = expression

    def Rename(self, new_name):
        self.labvar_name = '*' + new_name
        self.app.dialogGraphSettings.dialog.title = self.labvar_name
        self.instance.s['NAME'] = self.labvar_name

    def RemoveGraph(self):
        # self.m_parent.isDeleting = True
        self.app.dialogGraphSettings.Close()
        self.instance.RemoveMe()

    def ClearGraph(self):
        self.app.dialogGraphSettings.Close()
        self.instance.ClearGraph()

    def Rebase(self, instance):
        self.instance = instance
        self.graph_round_digits = instance.s['GRAPH_ROUND_DIGITS']
        self.labvar_name = instance.s['NAME']
        self.mode = instance.s['MODE']
        self.max_spectral_buffer_size = instance.s['MAX_SPECTRAL_BUFFER_SIZE']
        self.show_avg_graph = instance.s['SHOW_AVG_GRAPH']
        self.show_intime_graph = instance.s['SHOW_INTIME_GRAPH']
        self.show_main_graph = instance.s['SHOW_MAIN_GRAPH']
        self.show_main_value = instance.s['SHOW_MAIN_VALUE']
        self.show_avg_value = instance.s['SHOW_AVG_VALUE']
        self.main_graph_color = instance.s['MAIN_GRAPH_COLOR']
        self.avg_color = instance.s['AVG_COLOR']
        self.intime_graph_color = instance.s['INTIME_GRAPH_COLOR']
        self.label_x = instance.s['GRAPH_LABEL_X']
        self.label_y = instance.s['GRAPH_LABEL_Y']
        self.expression = instance.s['EXPRESSION']


class LDialogGraphSettings:

    def __init__(self, main_app):
        self.dialog = None
        self.app = main_app
        self.instance = None

        self._cancel_text = 'CANCEL'
        self._confirm_action = None

    def PreCache(self):
        self.RealOpen()
        self.dialog.dismiss(force=True)

    def RealOpen(self):
        if not self.dialog:
            self.dialog = MDDialogSizer(
                app=self.app,
                fixed=True,
                title='title',
                content_cls=LDialogGraphSettingsContent(self.app),
                type="custom",
                buttons=[
                    MDFlatButton(
                        text=self._cancel_text,
                        theme_text_color="Custom",
                        text_color=self.app.theme_cls.primary_color,
                        on_release=self.Close,
                    )
                ],
            )
            self.dialog.MAXIMUM_WIDTH = dp(400)
        self.dialog.open()
        self.dialog.update_height()

    # instance is graph class, calling this dialog
    def Open(self, instance):
        self.instance = instance
        self.Rebase(instance)
        self.RealOpen()

    def Close(self, *args):
        self.app.layoutManager.SaveLayout()
        self.dialog.dismiss(force=True)

    def Rebase(self, instance):
        self.dialog.title = f"{instance.s['NAME']}"
        self.dialog.content_cls.Rebase(instance)


class LDialogEnterString:

    def __init__(self, main_app):
        self.dialog = None
        self.app = main_app
        self.instance = None

        self._type = "string"
        self._title = 'title'
        self._confirm_text = 'confirm_text'
        self._cancel_text = 'cancel_text'
        self._confirm_action = None
        self._text = 'text'
        self._hint_text = 'hint_text'

    def PreCache(self):
        self.RealOpen()
        self.dialog.dismiss(force=True)

    def RealOpen(self):
        if not self.dialog:
            self.dialog = MDDialogSizer(
                app=self.app,
                title=self._title,
                content_cls=MDTextField(text=self._text, hint_text=self._hint_text),
                type="custom",
                buttons=[
                    MDFlatButton(
                        text=self._cancel_text,
                        theme_text_color="Custom",
                        text_color=self.app.theme_cls.primary_color,
                        on_release=self.Close,
                    ),
                    MDRaisedButton(
                        text=self._confirm_text,
                        on_release=self.Confirm,
                    ),
                ],
            )
            self.dialog.MAXIMUM_WIDTH = dp(400)
        self.dialog.content_cls._hint_text_font_size = sp(10)
        self.dialog.open()

    def Open(self, mytype, title, confirm_text, cancel_text, confirm_action, text, hint_text, instance=None):
        changed = False
        if instance and mytype == 'name':
            self.instance = instance
        if self._type != mytype:
            self._type = mytype
            changed = True
        if self._title != title:
            self._title = title
            changed = True
        if self._confirm_text != confirm_text:
            self._confirm_text = confirm_text
            changed = True
        if self._cancel_text != cancel_text:
            self._cancel_text = cancel_text
            changed = True
        if self._confirm_action != confirm_action:
            self._confirm_action = confirm_action
            changed = True
        if self._text != text:
            self._text = text
            changed = True
        if self._hint_text != hint_text:
            self._hint_text = hint_text
            changed = True
        if changed:
            self.Rebase()
        self.RealOpen()

    def Close(self, *args):
        self.instance = None
        self.dialog.content_cls.hint_text = self._hint_text
        self.dialog.dismiss(force=True)

    def CheckCollisionName(self, name):
        return self.instance.CheckCollisionName(name)

    def Validate(self):
        validate = True
        s = self._text
        if self._type == 'int':
            if s[0] in ('-', '+'):
                validate = s[1:].isdigit()
            else:
                validate = s.isdigit()
        elif self._type == 'float':
            self._text.replace(",", ".")
            validate = s.replace(".", "").isnumeric()
        elif self._type == 'bool':
            validate = s.lower() in ['true', '1']
        elif self._type == 'name':
            validate = self.CheckCollisionName(s)
        return validate

    def Confirm(self, *args):
        self._text = self.dialog.content_cls.text
        if self.Validate():
            self.Close()
            if self._confirm_action:
                self._confirm_action(self._text)
        else:
            self.dialog.content_cls.hint_text = f'Неверный ввод! Тип данных: {str(self._type)}'

    def Rebase(self):
        self.dialog.title = self._title
        self.dialog.buttons[0].text = self._cancel_text
        self.dialog.buttons[1].text = self._confirm_text
        self.dialog.content_cls.text = self._text
        self.dialog.content_cls.hint_text = self._hint_text


class LDialogList:

    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.app = main_app
        self.select_action = None
        self.items = []

    def PreCache(self):
        self.RealOpen()
        self.dialog.dismiss(force=True)

    def RealOpen(self):
        if not self.dialog:

            self.items = []
            self.items.append(ItemConfirm(text='Новое выражение'))
            for name in client.names:
                self.items.append(ItemConfirm(text=name))

            self.dialog = MDDialogSizer(
                app=self.app,
                type="confirmation",
                items=self.items,
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.app.theme_cls.primary_color,
                        on_release=self.Close,
                    ),
                    MDRaisedButton(
                        text="SELECT",
                        theme_text_color="Custom",
                        text_color=self.app.theme_cls.secondary_text_color,
                        on_release=self.Select,
                    ),
                ],
            )
        self.dialog.update_height()
        self.dialog.update_width()
        self.dialog.open()

    def Open(self, select_action):
        self.select_action = select_action
        self.RealOpen()

    def Select(self, *args):
        active_n = -1
        active_nn = -1
        for item in self.dialog.items:
            active_n += 1
            if item.ids.check.active:
                active_nn = active_n
                item.ids.check.active = False
                break
        if active_nn > -1:
            if self.select_action:
                self.select_action(self.items[active_nn].text)
            self.Close()

    def Close(self, *args):
        self.select_action = None
        self.dialog.dismiss()

    def Rebase(self):
        self.items = []
        self.items.append(ItemConfirm(text='Новое выражение'))
        for name in client.names:
            self.items.append(ItemConfirm(text=name))

        self.dialog = MDDialogSizer(
            app=self.app,
            type="confirmation",
            items=self.items,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=self.app.theme_cls.primary_color,
                    on_release=self.Close,
                ),
                MDRaisedButton(
                    text="SELECT",
                    theme_text_color="Custom",
                    text_color=self.app.theme_cls.secondary_text_color,
                    on_release=self.Select,
                ),
            ],
        )


class SnackbarMod(Snackbar, ButtonBehavior):
    dismiss_action = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.isTouched = False
        self.old_coord = None
        self.distance = 0
        self.initial_pos = None

        from libs.kivyapp import KivyApp

        self.bg_color = KivyApp.theme_cls.bg_normal
        self.ids.text_bar.text_color = KivyApp.theme_cls.accent_color
        self.ids.text_bar.text_style = 'Body2'
        radius = self.height * 0.2
        self.radius = [radius, radius, radius, radius]
        # self.elevation = 0

    def on_touch_down(self, touch):
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if not self.disabled:
            for button in self.buttons:
                if button.collide_point(touch.x, touch.y):
                    button.on_touch_down(touch)
            self.isTouched = True
            self.old_coord = touch.pos[1]
            if not self.initial_pos:
                self.initial_pos = self.pos
            return True

    def on_touch_move(self, touch, *args):
        if self.isTouched:
            new_coord = touch.pos[1]
            dy = new_coord - self.old_coord
            if self.initial_pos[1] > self.pos[1] + dy:
                self.pos[1] += dy
                self.distance += dy
                self.old_coord = new_coord
            if abs(self.distance) > self.height / 1.5:
                self.isTouched = False
                anim = Animation(y=-2*self.height, d=0.2)
                anim.bind(
                    on_complete=lambda *args: self.dismiss()
                )
                anim.start(self)

    def on_dismiss(self, *args):
        if self.dismiss_action:
            self.dismiss_action()
        super(SnackbarMod, self).on_dismiss()


def SnackbarMessage(text):
    from libs.kivyapp import KivyApp

    snackbar = SnackbarMod()
    snackbar.text = text
    snackbar.bg_color = KivyApp.theme_cls.bg_normal
    snackbar.ids.text_bar.text_color = KivyApp.theme_cls.accent_color
    snackbar.ids.text_bar.text_style = 'Body1'

    length_text = len(text) + 20
    offset = dp(20)
    size = Window.width - (offset * 2) if Window.width < length_text * 10 + 20 else length_text * 10 + 20
    snackbar.snackbar_x = (Window.width / 2) - (size / 2)
    snackbar.snackbar_y = offset + KivyApp.kivy_instance.ids.controls_panel_port.height - dp(5) if KivyApp.d_ori == 'vertical' else offset
    snackbar.size_hint_x = None
    snackbar.width = size

    radius = snackbar.height * 0.2
    snackbar.radius = [radius, radius, radius, radius]
    # snackbar.elevation = 3
    snackbar.ids.text_bar.halign = 'center'
    snackbar.open()


def SnackbarMessageAction(text, accept_button_text, accept_action, cancel_action=None, cancel_button_text='CANCEL'):
    from libs.kivyapp import KivyApp

    snackbar = SnackbarMod()
    snackbar.text = text

    length_text = len(text) + len(accept_button_text) + len(cancel_button_text) + 20
    offset = dp(20)
    size = Window.width - (offset * 2) if Window.width < length_text * 10 + 20 else length_text * 10 + 20
    snackbar.snackbar_x = (Window.width / 2) - (size / 2)
    snackbar.snackbar_y = offset + KivyApp.kivy_instance.ids.controls_panel_port.height - dp(5) if KivyApp.d_ori == 'vertical' else offset
    snackbar.size_hint_x = None
    snackbar.width = size

    radius = snackbar.height * 0.2
    snackbar.radius = [radius, radius, radius, radius]
    # snackbar.elevation = 3
    snackbar.ids.text_bar.halign = 'left'
    snackbar.dismiss_action = cancel_action

    def on_accept(arg):
        accept_action()
        snackbar.dismiss()

    snackbar.buttons = [
        MDRaisedButton(
            text=accept_button_text,
            on_release=on_accept,
            # elevation=0
        ),
        MDFlatButton(
            text=cancel_button_text,
            text_color=(1, 1, 1, 1),
            on_release=snackbar.dismiss,
        ),
    ]

    snackbar.open()


class ItemConfirm(OneLineAvatarIconListItem):
    divider = None

    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False


class DialogGraphSettingsContent(MDBoxLayout):
    labvar_name = StringProperty("None")
    mode = StringProperty("NORMAL")

    max_spectral_buffer_size = NumericProperty(0)

    show_avg_value = BooleanProperty(False)
    show_main_value = BooleanProperty(False)

    show_avg_graph = BooleanProperty(False)
    show_intime_graph = BooleanProperty(False)
    show_main_graph = BooleanProperty(False)

    main_graph_color = StringProperty('#FFFFFF')
    avg_color = StringProperty('#FFFFFF')
    intime_graph_color = StringProperty('#FFFFFF')

    graph_round_digits = NumericProperty(0)

    label_x = BooleanProperty(False)
    label_y = BooleanProperty(False)
    expression = StringProperty('')

    def __init__(self, _parent, **kwargs):
        super().__init__(**kwargs)
        self.m_parent = _parent
        self.dialog = self.m_parent.dialog
        self.dialogListLabVar = DialogListLabVar(self)
        self.dialogEnterString = DialogEnterString(self.m_parent.graph_instance, self)
        self.color_picker = None

        self.graph_round_digits = self.m_parent.graph_instance.s['GRAPH_ROUND_DIGITS']
        self.labvar_name = self.m_parent.graph_instance.s['NAME']
        self.mode = self.m_parent.graph_instance.s['MODE']
        self.max_spectral_buffer_size = self.m_parent.graph_instance.s['MAX_SPECTRAL_BUFFER_SIZE']
        self.show_avg_graph = self.m_parent.graph_instance.s['SHOW_AVG_GRAPH']
        self.show_intime_graph = self.m_parent.graph_instance.s['SHOW_INTIME_GRAPH']
        self.show_main_graph = self.m_parent.graph_instance.s['SHOW_MAIN_GRAPH']
        self.show_main_value = self.m_parent.graph_instance.s['SHOW_MAIN_VALUE']
        self.show_avg_value = self.m_parent.graph_instance.s['SHOW_AVG_VALUE']
        self.main_graph_color = self.m_parent.graph_instance.s['MAIN_GRAPH_COLOR']
        self.avg_color = self.m_parent.graph_instance.s['AVG_COLOR']
        self.intime_graph_color = self.m_parent.graph_instance.s['INTIME_GRAPH_COLOR']
        self.label_x = self.m_parent.graph_instance.s['GRAPH_LABEL_X']
        self.label_y = self.m_parent.graph_instance.s['GRAPH_LABEL_Y']
        self.expression = self.m_parent.graph_instance.s['EXPRESSION']

        self.colorpicker_target = None

    def CheckCollisionName(self, name):
        return self.m_parent.graph_instance.CheckCollisionName(name)

    def Set(self, tag, value):
        if tag == 'EXPRESSION':
            self.expression = value
        if tag == 'MAX_SPECTRAL_BUFFER_SIZE':
            self.max_spectral_buffer_size = int(value)
        if tag == 'GRAPH_ROUND_DIGITS':
            self.graph_round_digits = int(value)
        self.m_parent.graph_instance.s[tag] = value

    def Toggle(self, tag):
        if tag == 'GRAPH_LABEL_X':
            self.label_x = self.m_parent.graph_instance.s['GRAPH_LABEL_X'] = not self.m_parent.graph_instance.s['GRAPH_LABEL_X']
        if tag == 'GRAPH_LABEL_Y':
            self.label_y = self.m_parent.graph_instance.s['GRAPH_LABEL_Y'] = not self.m_parent.graph_instance.s['GRAPH_LABEL_Y']
        if tag == 'SHOW_MAIN_VALUE':
            self.m_parent.graph_instance.Toggle('SHOW_MAIN_VALUE')
            self.show_main_value = self.m_parent.graph_instance.s['SHOW_MAIN_VALUE']
        if tag == 'SHOW_AVG_VALUE':
            self.m_parent.graph_instance.Toggle('SHOW_AVG_VALUE')
            self.show_avg_value = self.m_parent.graph_instance.s['SHOW_AVG_VALUE']
        if tag == 'SHOW_MAIN_GRAPH':
            self.m_parent.graph_instance.Toggle('SHOW_MAIN_GRAPH', True)
            self.m_parent.graph_instance.gardenGraph.TogglePlot()
            self.show_main_graph = self.m_parent.graph_instance.s['SHOW_MAIN_GRAPH']
        if tag == 'SHOW_AVG_GRAPH':
            self.m_parent.graph_instance.Toggle('SHOW_AVG_GRAPH', True)
            self.m_parent.graph_instance.gardenGraph.TogglePlot()
            self.show_avg_graph = self.m_parent.graph_instance.s['SHOW_AVG_GRAPH']
        if tag == 'SHOW_INTIME_GRAPH':
            self.m_parent.graph_instance.Toggle('SHOW_INTIME_GRAPH', True)
            self.m_parent.graph_instance.gardenGraph.TogglePlot()
            self.show_intime_graph = self.m_parent.graph_instance.s['SHOW_INTIME_GRAPH']
        if tag == 'NEXT_MODE':
            self.mode = self.m_parent.graph_instance.NextMode()
            self.m_parent.dialog.title = f"{self.m_parent.graph_instance.s['NAME']}:{self.m_parent.graph_instance.s['MODE']}"
        if 'COLOR' in tag:
            self.color_picker = MDColorPicker(size_hint=(0.6, 0.6))
            if tag == 'MAIN_GRAPH_COLOR':
                self.color_picker.default_color = self.m_parent.graph_instance.s['MAIN_GRAPH_COLOR']
            if tag == 'AVG_COLOR':
                self.color_picker.default_color = self.m_parent.graph_instance.s['AVG_COLOR']
            if tag == 'INTIME_GRAPH_COLOR':
                self.color_picker.default_color = self.m_parent.graph_instance.s['INTIME_GRAPH_COLOR']
            self.color_picker.open()
            self.colorpicker_target = tag
            self.color_picker.bind(on_release=self.save_color)

    def removeIt(self):
        self.m_parent.isDeleting = True
        self.m_parent.Close()
        self.m_parent.graph_instance.RemoveMe()

    def Refresh(self):
        self.m_parent.Close()
        self.m_parent.graph_instance.ClearGraph()

    def save_color(self, instance_color_picker: MDColorPicker, type_color: str, selected_color: Union[list, str]):
        if self.colorpicker_target == 'MAIN_GRAPH_COLOR':
            self.main_graph_color = get_hex_from_color(selected_color)
            self.m_parent.graph_instance.s['MAIN_GRAPH_COLOR'] = self.main_graph_color
            self.m_parent.graph_instance.gardenGraph.UpdatePlotColor(plot_name='MAIN')
        if self.colorpicker_target == 'AVG_COLOR':
            self.avg_color = get_hex_from_color(selected_color)
            self.m_parent.graph_instance.s['AVG_COLOR'] = self.avg_color
            self.m_parent.graph_instance.gardenGraph.UpdatePlotColor(plot_name='AVG')

        self.color_picker.dismiss(force=True)
        self.colorpicker_target = None


class DialogGraphSettings:

    def __init__(self, _graph_instance, **kwargs):
        super().__init__(**kwargs)
        self.graph_instance = _graph_instance
        self.dialog = None
        self.dialog_cls = None
        self.isDeleting = False

    def Open(self, silent=False):
        if not self.dialog_cls:
            self.dialog_cls = DialogGraphSettingsContent(self)
        if not self.dialog:
            self.dialog = MDDialogFix(
                title=f"{self.graph_instance.s['NAME']}:{self.graph_instance.s['MODE']}",
                type="custom",
                content_cls=self.dialog_cls,
                on_pre_dismiss=self.PreDismiss,
                buttons=[
                    MDFlatButton(
                        text="CLOSE",
                        theme_text_color="Custom",
                        text_color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color,
                        on_release=self.Close,
                    )
                ],
            )
        self.dialog.update_height()
        self.dialog.update_width()
        if silent:
            self.dialog.open(animation=False)
        else:
            self.dialog.open()

    def PreDismiss(self, *args):
        if not self.isDeleting:
            self.graph_instance.UnAccentIt()
            self.isDeleting = False

    def Close(self, *args):
        Clock.schedule_once(self.graph_instance.kivy_instance.main_app.layoutManager.SaveLayout, 0)
        self.dialog.dismiss(force=True)


class ChipsContent(MDBoxLayout):
    init_text = StringProperty('')
    hint_text = StringProperty('')

    def __init__(self, _graph, _parent, init_text, hint_text):
        super().__init__()
        self.graph_instance = _graph
        self.m_parent = _parent
        self.init_text = init_text
        self.hint_text = hint_text
        self.bind(height=self.on_height)

    def on_height(self, *args):
        self.m_parent.dialog.update_height()

    def ChipReleased(self, instance):
        self.ids.my_text_field.text += f'[{instance.text}]'


class DialogEnterString:

    def __init__(self, _graph, _parent, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.graph_instance = _graph
        self.m_parent = _parent
        self.state = None
        self.text_field = None
        self.init_text = None
        self.title = None
        self.hint_text = None
        self._need_connection = None

    def onResize(self, *args):
        pass

    def Open(self, state, init_text, title, hint_text, _need_connection=False):
        self.title = title
        self.init_text = init_text
        self.hint_text = hint_text
        self._need_connection = _need_connection
        if _need_connection:
            kivy_instance = self.graph_instance.kivy_instance
            if not client.isConnected():
                SnackbarMessageAction('Подключитесь к серверу!', 'CONNECT', kivy_instance.Connect)
                return True

        if state == "edit_name" and '*' not in init_text:
            SnackbarMessage("Нельзя поменять название этой переменной!")
        else:
            if state == "edit_name":
                init_text = init_text[1:]
            self.state = state

            if self.state == "expression":

                self.dialog = MDDialog(
                    title=title,
                    # elevation=0,
                    auto_dismiss=False,
                    type="custom",
                    content_cls=ChipsContent(self.graph_instance, self, init_text, hint_text),
                    buttons=[
                        MDFlatButton(
                            text="CANCEL",
                            theme_text_color="Custom",
                            text_color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color,
                            on_release=self.Cancel,
                        ),
                        MDFlatButton(
                            text="ENTER",
                            theme_text_color="Custom",
                            text_color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color,
                            on_release=self.Enter,
                        )
                    ],
                )
                Window.bind(on_resize=self.onResize)
            else:
                self.text_field = MDTextField(
                    text=init_text,
                    hint_text=hint_text,
                )

                self.dialog = MDDialog(
                    title=title,
                    # elevation=0,
                    auto_dismiss=False,
                    type="custom",
                    content_cls=self.text_field,
                    buttons=[
                        MDFlatButton(
                            text="CANCEL",
                            theme_text_color="Custom",
                            text_color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color,
                            on_release=self.Cancel,
                        ),
                        MDFlatButton(
                            text="ENTER",
                            theme_text_color="Custom",
                            text_color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color,
                            on_release=self.Enter,
                        )
                    ],
                )
            self.dialog.open()

    def Cancel(self, *args):
        self.state = None
        self.dialog.dismiss(force=True)

    def Enter(self, *args):
        if self.state == 'expression':
            self.dialog.content_cls.ids.my_text_field.text = self.dialog.content_cls.ids.my_text_field.text.strip().replace('  ', ' ')
            if self.dialog.content_cls.ids.my_text_field.text != '' and self.graph_instance.CheckCollisionName(self.dialog.content_cls.ids.my_text_field.text):
                self.m_parent.Set('EXPRESSION', self.dialog.content_cls.ids.my_text_field.text)
                self.state = None
                self.dialog.dismiss(force=True)
            else:
                SnackbarMessage("Некорректный ввод!")
        elif self.state == 'spectral_size':
            self.text_field.text = self.text_field.text.strip().replace(' ', '')
            if self.text_field.text != '' and self.text_field.text.isdecimal():
                self.text_field.text = str(2 ** round(math.log2(int(self.text_field.text))))
                self.m_parent.Set('MAX_SPECTRAL_BUFFER_SIZE', int(self.text_field.text))
                SnackbarMessage("Изменения будут применены после перезагрузки приложения!")
                self.state = None
                self.dialog.dismiss(force=True)
            else:
                SnackbarMessage("Некорректный ввод!")
        elif self.state == 'precision':
            self.text_field.text = self.text_field.text.strip().replace(' ', '')
            if self.text_field.text != '' and self.text_field.text.isdecimal():
                self.m_parent.Set('GRAPH_ROUND_DIGITS', int(self.text_field.text))
                self.state = None
                self.dialog.dismiss(force=True)
            else:
                SnackbarMessage("Некорректный ввод!")
        else:
            if self.text_field.text.strip().replace(' ', '') != '':
                if self.state == 'edit_name':
                    default_name = '*' + self.text_field.text
                    self.graph_instance.UpdateName(default_name, _clear_graph=True)
                    self.m_parent.m_parent.labvar_name = default_name
                    self.m_parent.m_parent.dialog.title = f"{default_name}:{self.graph_instance.s['MODE']}"
                    self.state = None
                    self.dialog.dismiss(force=True)
                    self.m_parent.m_parent.Close()
                    self.m_parent.m_parent.Open()
                if self.state == 'new_var':
                    default_name = '*' + self.text_field.text
                    self.graph_instance.UpdateName(default_name, _clear_graph=True, _clear_expression=True)
                    self.m_parent.m_parent.labvar_name = default_name
                    self.m_parent.dialog.title = f"{default_name}:{self.graph_instance.s['MODE']}"
                    self.state = None
                    self.dialog.dismiss(force=True)
                    self.m_parent.m_parent.m_parent.Close()
                    self.m_parent.m_parent.m_parent.Open()
            else:
                SnackbarMessage("Некорректный ввод!")


class DialogListLabVar:

    def __init__(self, _parent, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.m_parent = _parent
        self.items = []
        self.default_name = '*TEST'
        self.new_dialog = DialogEnterString(self.m_parent.m_parent.graph_instance, self)

    def Open(self):
        kivy_instance = self.m_parent.m_parent.graph_instance.kivy_instance
        if not client.isConnected():
            SnackbarMessageAction("Подключитесь к серверу!", 'CONNECT', kivy_instance.Connect)
        else:
            if not self.dialog:
                self.items.append(ItemConfirm(text='Новое выражение'))
                for name in client.names:
                    self.items.append(ItemConfirm(text=name))
                self.dialog = MDDialogFix(
                    type="confirmation",
                    items=self.items,
                    buttons=[
                        MDFlatButton(
                            text="CANCEL",
                            theme_text_color="Custom",
                            text_color=kivy_instance.main_app.theme_cls.primary_color,
                            on_release=self.Close,
                        ),
                        MDRaisedButton(
                            text="SELECT",
                            theme_text_color="Custom",
                            text_color=kivy_instance.main_app.theme_cls.secondary_text_color,
                            on_release=self.Select,
                        ),
                    ],
                )
            self.dialog.update_height()
            self.dialog.update_width()
            self.dialog.open()

    def Select(self, *args):
        active_n = -1
        active_nn = -1
        for item in self.dialog.items:
            active_n += 1
            if item.ids.check.active:
                active_nn = active_n
                item.ids.check.active = False
                break
        if active_nn > -1:
            if active_nn > 0:
                self.m_parent.m_parent.graph_instance.UpdateName(self.items[active_nn].text, _clear_graph=True)
                self.m_parent.labvar_name = self.items[active_nn].text
                self.m_parent.m_parent.dialog.title = f"{self.items[active_nn].text}:{self.m_parent.m_parent.graph_instance.s['MODE']}"

                self.dialog.dismiss()
                self.m_parent.m_parent.Close()
                self.m_parent.m_parent.Open()
            else:
                self.new_dialog.Open('new_var', '', 'Название переменной', 'Название должно быть уникальным')
                self.dialog.dismiss()

    def Close(self, *args):
        self.dialog.dismiss()
