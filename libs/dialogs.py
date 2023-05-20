import math
import threading
from threading import main_thread

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
from kivymd.uix.list.list import OneLineAvatarIconListItem, BaseListItem, OneLineIconListItem

from kivy.utils import get_hex_from_color
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

from libs.opcua.opcuaclient import client
from libs.settings.settingsJSON import *
from libs.utils import keycodes


class MDDialogSizer(MDDialog):

    def __init__(self, app, key_handler=None, fixed=False, height_compensation=0., **kwargs):
        super().__init__(**kwargs)
        self.key_handler = key_handler
        self.isOpen = False
        Window.bind(
            on_maximize=self.update_size,
            on_restore=self.update_size,
            size=self.update_size)
                    # on_maximize=self.update_height,
                    # on_restore=self.update_height,
                    # on_minimize=self.update_height
        # Window.bind(on_maximize=self.update_width,
        #             on_restore=self.update_width,
        #             on_minimize=self.update_width)

        Window.bind(on_keyboard=self.on_keyboard_handler)
        self.fixed = fixed
        self.height_compensation = height_compensation
        self.app = app
        self.update_number = 0
        self.SKIP_FRAMES_ON_UPDATE = 1
        self.MAXIMUM_WIDTH = dp(500)
        self.DIALOG_MINIMUM_HEIGHT_VERTICAL = msettings.get('DIALOG_MINIMUM_HEIGHT_VERTICAL')
        self.DIALOG_MAXIMUM_HEIGHT_HORIZONTAL = msettings.get('DIALOG_MAXIMUM_HEIGHT_HORIZONTAL')

    def on_keyboard_handler(self, _window, key, *_args):
        if self.key_handler:
            self.key_handler(_window, key)

    def create_items(self) -> None:
        height = 0

        for item in self.items:
            if issubclass(item.__class__, BaseListItem):
                height += item.height  # calculate height contents
                self.edit_padding_for_item(item)
                self.ids.box_items.add_widget(item)

        if height > Window.height:
            self.ids.scroll.height = self.get_normal_height()
        else:
            self.ids.scroll.height = height

    def update_size_low(self, *args):
        self.update_height(args)
        self.update_width(args)

    def update_size(self, *args):
        self.update_size_low()

    def update_width(self, *args) -> None:
        if not self.fixed:
            if Window.width - dp(48) < self.MAXIMUM_WIDTH:
                self.width = Window.width - dp(48)
            elif self.MAXIMUM_WIDTH <= Window.width - dp(48):
                self.width = self.MAXIMUM_WIDTH
        else:
            if Window.width - dp(48) < self.DIALOG_MINIMUM_HEIGHT_VERTICAL:
                self.width = Window.width - dp(48)
            else:
                self.width = self.DIALOG_MINIMUM_HEIGHT_VERTICAL

    def update_height_low(self, *args):
        if self.update_number > self.SKIP_FRAMES_ON_UPDATE:
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
                        Window.height - dp(48) - dp(100) + self.height_compensation \
                            if self.content_cls.ids.content_cls_box.height + dp(50) > Window.height - dp(48) - dp(100) + self.height_compensation \
                            else self.content_cls.ids.content_cls_box.height + dp(50)
        else:
            self.update_number = self.update_number + 1
            Clock.schedule_once(self.update_height_low)


    def update_height(self, *args) -> None:
        self.update_number = 0
        Clock.schedule_once(self.update_height_low)

class LDialogGraphSettingsContent(MDBoxLayout):

    app = ObjectProperty(None)

    labvar_name = StringProperty("None")
    mode = StringProperty("NORMAL")
    spectral_buffer_size = NumericProperty(0)
    avg_buffer_size = NumericProperty(0)
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
    target_value = NumericProperty(0)
    show_target_value = BooleanProperty(True)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.instance = None
        self.dialog = None

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
            self.instance.gardenGraph.UpdatePlotSettings(recombine=False)
            self.show_main_graph = self.instance.s['SHOW_MAIN_GRAPH']
        if tag == 'SHOW_AVG_GRAPH':
            self.instance.Toggle('SHOW_AVG_GRAPH', True)
            self.instance.gardenGraph.UpdatePlotSettings(recombine=False)
            self.show_avg_graph = self.instance.s['SHOW_AVG_GRAPH']
        if tag == 'SHOW_INTIME_GRAPH':
            self.instance.Toggle('SHOW_INTIME_GRAPH', True)
            self.instance.gardenGraph.UpdatePlotSettings(recombine=False)
            self.show_intime_graph = self.instance.s['SHOW_INTIME_GRAPH']
        if tag == 'SHOW_TARGET_VALUE':
            self.instance.Toggle('SHOW_TARGET_VALUE', False)
            self.instance.gardenGraph.UpdatePlotSettings(recombine=False)
            self.show_target_value = self.instance.s['SHOW_TARGET_VALUE']
        if tag == 'NEXT_MODE':
            self.mode = self.instance.ToggleMode()
            self.dialog.update_height()

    def SelectVariable(self, name):
        if name == 'Новое выражение':
            self.app.dialogTextInput.Open('name', 'Название переменной', 'SAVE', 'CANCEL', self.Rename, '', 'Имя должно быть уникальным', self.instance)
        else:
            self.ChangeDirectName(name)

    def SetTargetValue(self, value):
        self.target_value = float(value)
        self.instance.s['TARGET_VALUE'] = float(value)

    def SetPrecision(self, precision):
        self.graph_round_digits = int(precision)
        self.instance.s['GRAPH_ROUND_DIGITS'] = int(precision)

    def SetSpectralBufferSize(self, size):
        self.spectral_buffer_size = int(size)
        self.instance.s['SPECTRAL_BUFFER_SIZE'] = int(size)

    def SetAVGBufferSize(self, size):
        self.avg_buffer_size = int(size)
        self.instance.s['AVG_BUFFER_SIZE'] = int(size)

    def SetExpression(self, expression):
        self.expression = expression
        self.instance.s['EXPRESSION'] = expression

    def ChangeDirectName(self, new_name):
        self.labvar_name = new_name
        self.app.dialogGraphSettings.dialog.title = self.labvar_name
        self.instance.s['NAME'] = self.labvar_name
        self.dialog.update_height()

    def Rename(self, new_name):
        self.labvar_name = '*' + new_name
        self.app.dialogGraphSettings.dialog.title = self.labvar_name
        self.instance.s['NAME'] = self.labvar_name
        self.dialog.update_height()

    def RemoveGraph(self):
        # self.m_parent.isDeleting = True
        self.app.dialogGraphSettings.Close()
        self.instance.RemoveMe()

    def ClearGraph(self):
        self.app.dialogGraphSettings.Close()
        self.instance.ClearGraph()

    def Rebase(self, instance, dialog):
        self.dialog = dialog
        self.instance = instance
        self.graph_round_digits = instance.s['GRAPH_ROUND_DIGITS']
        self.labvar_name = instance.s['NAME']
        self.mode = instance.s['MODE']
        self.spectral_buffer_size = instance.s['SPECTRAL_BUFFER_SIZE']
        self.avg_buffer_size = instance.s['AVG_BUFFER_SIZE']
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
        self.target_value = instance.s['TARGET_VALUE']
        self.show_target_value = instance.s['SHOW_TARGET_VALUE']


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
                on_pre_dismiss=self.UnselectGraph,
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
        self.dialog.update_width()

    def SelectGraph(self, *args):
        if self.instance:
            self.instance.AccentIt()

    def UnselectGraph(self, *args):
        Clock.schedule_once(self.app.layoutManager.SaveLayout, 2)
        if self.instance:
            self.instance.UnAccentIt()

    # instance is graph class, calling this dialog
    def Open(self, instance):
        self.instance = instance
        self.SelectGraph()
        self.Rebase(instance)
        self.RealOpen()

    def Close(self, *args):
        self.dialog.dismiss(force=True)

    def Rebase(self, instance):
        self.dialog.title = f"{instance.s['NAME']}"
        self.dialog.content_cls.Rebase(instance, self.dialog)


class Item(OneLineIconListItem):
    left_icon = StringProperty()


class LDialogMenuContent(MDBoxLayout):

    def __init__(self, app, dialog_class, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.dialog_class = dialog_class
        self.items = [
            Item(
                text='Добавить график',
                height=dp(48),
                left_icon='plus-box',
                font_style='Body1',
                on_release=self.AddGraph
            ),
            Item(
                text='Добавить несколько графиков',
                height=dp(48),
                left_icon='plus-box-multiple',
                font_style='Body1',
                on_release=self.AddGraphs
            ),
            Item(
                text='Добавить кнопку',
                height=dp(48),
                left_icon='card-plus',
                font_style='Body1',
                on_release=self.AddControl
            ),
            Item(
                text='Обновить графики',
                height=dp(48),
                left_icon='refresh',
                font_style='Body1',
                on_release=self.RefreshAll
            ),
            Item(
                text='Показать лог',
                height=dp(48),
                left_icon='math-log',
                font_style='Body1',
                on_release=self.ToggleLog
            ),
            Item(
                text='Скрывать кнопки' if self.app.kivy_instance.show_controls_menu else 'Показывать кнопки',
                height=dp(48),
                left_icon='ticket',
                font_style='Body1',
                on_release=self.ToggleControls
            ),
            Item(
                text='Настройки',
                height=dp(48),
                left_icon='cog-outline',
                font_style='Body1',
                on_release=self.OpenSettings
            )
        ]

    def AddGraph(self, *args):
        self.dialog_class.Close()
        Clock.schedule_once(self.app.kivy_instance.AddGraphManual, 0.2)

    def AddGraphs(self, *args):
        self.dialog_class.Close()
        self.app.kivy_instance.AddGraphs()

    def AddControl(self, *args):
        self.app.kivy_instance.AddControl()
        self.items[5].text = 'Скрывать кнопки' if self.app.kivy_instance.show_controls_menu else 'Показывать кнопки'
        self.dialog_class.Close()

    def RefreshAll(self, *args):
        self.app.kivy_instance.RefreshAll()
        self.dialog_class.Close()

    def ToggleLog(self, *args):
        self.app.toggle_log()
        self.items[4].text = 'Скрыть лог' if self.items[4].text == 'Показать лог' else 'Показать лог'
        self.dialog_class.Close()

    def ToggleControls(self, *args):
        self.app.kivy_instance.SwapShowControlsMenu()
        self.items[5].text = 'Скрывать кнопки' if self.app.kivy_instance.show_controls_menu else 'Показывать кнопки'
        self.dialog_class.Close()

    def OpenSettings(self, *args):
        self.app.open_settings()
        self.dialog_class.Close()

    def Rebase(self):
        for item in self.items:
            self.ids.items_box.add_widget(item)


class LDialogMenu:

    def __init__(self, main_app, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.app = main_app

    def PreCache(self):
        self.RealOpen()
        self.dialog.dismiss(force=True)

    def RealOpen(self):
        if not self.dialog:

            self.dialog = MDDialogSizer(
                app=self.app,
                type="custom",
                content_cls=LDialogMenuContent(self.app, self),
                fixed=True,
            )
            self.dialog.content_cls.Rebase()
            self.dialog.ids.container.padding = ["24dp", "0dp", "8dp", "0dp"]
            self.dialog.remove_widget(self.dialog.ids.title)
            self.dialog.remove_widget(self.dialog.ids.text)
            self.dialog.remove_widget(self.dialog.ids.scroll)
            self.dialog.height_compensation = dp(100)
        self.dialog.open()
        self.dialog.update_height()
        self.dialog.update_width()

    def Open(self):
        self.RealOpen()

    def Close(self, *args):
        self.dialog.dismiss()

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
        self.dialog.isOpen = False
        self.dialog.dismiss(force=True)

    def on_keyboard(self, _window, key):
        if self.dialog.isOpen:
            if key == keycodes['enter']:
                self.Confirm()
                return True

    def RealOpen(self):
        if not self.dialog:
            self.dialog = MDDialogSizer(
                app=self.app,
                key_handler=self.on_keyboard,
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
                ]
            )
            self.dialog.MAXIMUM_WIDTH = dp(400)
        self.dialog.content_cls._hint_text_font_size = sp(10)
        self.dialog.isOpen = True
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
        self.dialog.isOpen = False
        self.dialog.dismiss(force=True)

    def CheckCollisionName(self, name):
        return self.instance.CheckCollisionName(name)

    def Validate(self):
        validate = True
        s = self._text
        if self._type == 'int':
            validate = s.isdigit()
        elif self._type == 'sint':
            if s[0] in ('-', '+'):
                validate = s[1:].isdigit()
            else:
                validate = s.isdigit()
        elif self._type == 'float':
            self._text.replace(",", ".")
            validate = s.replace(".", "").isnumeric()
        elif self._type == 'sfloat':
            self._text.replace(",", ".")
            if s[0] in ('-', '+'):
                validate = s[1:].replace(".", "").isnumeric()
            else:
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

        # self.dialog.items = self.items
        self.dialog.update_items(self.items)

        # self.dialog = MDDialogSizer(
        #     app=self.app,
        #     type="confirmation",
        #     items=self.items,
        #     buttons=[
        #         MDFlatButton(
        #             text="CANCEL",
        #             theme_text_color="Custom",
        #             text_color=self.app.theme_cls.primary_color,
        #             on_release=self.Close,
        #         ),
        #         MDRaisedButton(
        #             text="SELECT",
        #             theme_text_color="Custom",
        #             text_color=self.app.theme_cls.secondary_text_color,
        #             on_release=self.Select,
        #         ),
        #     ],
        # )


class ItemConfirm(OneLineAvatarIconListItem):
    divider = None

    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False


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
