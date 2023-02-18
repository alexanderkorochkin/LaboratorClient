from kivy.clock import Clock
from kivymd.material_resources import DEVICE_TYPE
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDRoundFlatButton
from kivymd.uix.chip import MDChip
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.pickers import MDColorPicker

from kivy.core.window import Window

from typing import Union

from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, ColorProperty, NumericProperty
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
        if self.type == 'custom':
            if Window.width - sp(48) < self.MINIMAL_WIDTH_VERTICAL:
                self.width = Window.width - sp(48)
            elif self.MINIMAL_WIDTH_VERTICAL <= Window.width - sp(48) < self.MAXIMUM_WIDTH_HORIZONTAL:
                self.width = self.MINIMAL_WIDTH_VERTICAL
            else:
                self.width = self.MAXIMUM_WIDTH_HORIZONTAL
        if self.type == 'confirmation':
            if Window.width - sp(48) < self.MINIMAL_WIDTH_VERTICAL:
                self.width = Window.width - sp(48)
            else:
                self.width = self.MINIMAL_WIDTH_VERTICAL

    def update_height(self, *args) -> None:
        if self.type == 'custom':
            self._spacer_top = \
                Window.height - sp(48) - sp(100) \
                if self.content_cls.ids.content_cls_box.height + sp(50) > Window.height - sp(48) - sp(100) \
                else self.content_cls.ids.content_cls_box.height + sp(50)
        if self.type == 'confirmation':
            height = 0
            for item in self.items:
                height += item.height
            if height > Window.height - sp(48) - sp(100):
                self.ids.scroll.height = Window.height - sp(48) - sp(100)
            else:
                self.ids.scroll.height = height


class DialogEndpointContent(MDBoxLayout):
    endpoint = StringProperty('None')

    def __init__(self, _endpoint, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = _endpoint


class DialogEndpoint:

    def __init__(self, _main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_app = _main_app
        self.dialog = None

    def Open(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Enter the endpoint",
                content_cls=DialogEndpointContent(self.main_app.kivy_instance.endpoint),
                elevation=0,
                type="custom",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.main_app.theme_cls.primary_color,
                        on_release=self.Close,
                    ),
                    MDRaisedButton(
                        text="SAVE",
                        theme_text_color="Custom",
                        text_color=self.main_app.theme_cls.secondary_text_color,
                        on_release=self.Save,
                    ),
                ],
            )
        self.dialog.open()

    def Save(self, *args):
        self.main_app.kivy_instance.endpoint = str(self.dialog.content_cls.ids.dialog_endpoint_text_input.text)
        self.dialog.dismiss(force=True)

    def Close(self, *args):
        self.dialog.dismiss(force=True)


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

    show_avg_value = BooleanProperty(False)
    show_main_value = BooleanProperty(False)

    show_avg_graph = BooleanProperty(False)
    show_intime_graph = BooleanProperty(False)
    show_main_graph = BooleanProperty(False)

    main_graph_color = StringProperty('#FFFFFF')
    avg_color = StringProperty('#FFFFFF')
    intime_graph_color = StringProperty('#FFFFFF')

    label_x = BooleanProperty(False)
    label_y = BooleanProperty(False)
    expression = StringProperty('')

    def __init__(self, _parent, _dialog, **kwargs):
        super().__init__(**kwargs)
        self.m_parent = _parent
        self.dialog = _dialog

        self.labvar_name = self.m_parent.graph_instance.GetName()
        self.mode = self.m_parent.graph_instance.s['MODE']

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

        self.color_picker = None
        self.colorpicker_target = None

        self.dialogListLabVar = DialogListLabVar(self)
        self.dialogEnterString = DialogEnterString(self.m_parent.graph_instance, self)

    def CheckCollizionName(self, name):
        return self.m_parent.graph_instance.CheckCollizionName(name)

    def SetExpression(self, expression):
        self.expression = expression
        self.m_parent.graph_instance.SetExpression(expression)

    def removeIt(self):
        self.m_parent.isDeleting = True
        self.m_parent.Close()
        self.m_parent.graph_instance.RemoveMe()

    def ToggleX(self):
        self.label_x = self.m_parent.graph_instance.toggle_x_grid_label()

    def ToggleY(self):
        self.label_y = self.m_parent.graph_instance.toggle_y_grid_label()

    def Refresh(self):
        self.m_parent.graph_instance.ClearGraph()

    def ChangeMode(self, _id):
        if _id == 'change_mode_button':
            self.mode = self.m_parent.graph_instance.NextMode()
            self.m_parent.dialog.title = f"{self.m_parent.graph_instance.s['NAME']}:{self.m_parent.graph_instance.s['MODE']}"

    def CheckboxPress(self, _id):
        if _id == 'show_main_value':
            self.m_parent.graph_instance.Toggle('SHOW_MAIN_VALUE')
            self.show_main_value = self.m_parent.graph_instance.s['SHOW_MAIN_VALUE']
        if _id == 'show_avg_value':
            self.m_parent.graph_instance.Toggle('SHOW_AVG_VALUE')
            self.show_avg_value = self.m_parent.graph_instance.s['SHOW_AVG_VALUE']
        if _id == 'show_main_graph':
            self.m_parent.graph_instance.Toggle('SHOW_MAIN_GRAPH', True)
            self.m_parent.graph_instance.gardenGraph.TogglePlot(plot='MAIN')
            self.show_main_graph = self.m_parent.graph_instance.s['SHOW_MAIN_GRAPH']
        if _id == 'show_avg_graph':
            self.m_parent.graph_instance.Toggle('SHOW_AVG_GRAPH', True)
            self.m_parent.graph_instance.gardenGraph.TogglePlot(plot='AVG')
            self.show_avg_graph = self.m_parent.graph_instance.s['SHOW_AVG_GRAPH']
        if _id == 'show_intime_graph':
            self.m_parent.graph_instance.Toggle('SHOW_INTIME_GRAPH', True)
            self.m_parent.graph_instance.gardenGraph.TogglePlot(plot='INTIME')
            self.show_intime_graph = self.m_parent.graph_instance.s['SHOW_INTIME_GRAPH']

    def OpenColorPicker(self, _colorpicker_target):
        self.color_picker = MDColorPicker(size_hint=(0.6, 0.6))

        if _colorpicker_target == 'MAIN':
            self.color_picker.default_color = self.m_parent.graph_instance.s['MAIN_GRAPH_COLOR']
        if _colorpicker_target == 'AVG':
            self.color_picker.default_color = self.m_parent.graph_instance.s['AVG_COLOR']
        if _colorpicker_target == 'INTIME':
            self.color_picker.default_color = self.m_parent.graph_instance.s['INTIME_GRAPH_COLOR']

        self.color_picker.open()
        self.colorpicker_target = _colorpicker_target
        self.color_picker.bind(on_release=self.save_color)

    def save_color(self, instance_color_picker: MDColorPicker, type_color: str, selected_color: Union[list, str]):
        if self.colorpicker_target == 'AVG':
            self.avg_color = get_hex_from_color(selected_color)
            self.m_parent.graph_instance.s['AVG_COLOR'] = self.avg_color
            self.m_parent.graph_instance.gardenGraph.UpdatePlotColor(plot='AVG')
        if self.colorpicker_target == 'MAIN':
            self.main_graph_color = get_hex_from_color(selected_color)
            self.m_parent.graph_instance.s['MAIN_GRAPH_COLOR'] = self.main_graph_color
            self.m_parent.graph_instance.gardenGraph.UpdatePlotColor(plot='MAIN')

        self.color_picker.dismiss(force=True)
        self.colorpicker_target = None


class DialogGraphSettings:

    def __init__(self, _graph_instance, **kwargs):
        super().__init__(**kwargs)
        self.graph_instance = _graph_instance
        self.dialog = None
        self.isDeleting = False

    def Open(self):
        self.graph_instance.AccentIt()
        self.dialog = MDDialogFix(
            title=f"{self.graph_instance.s['NAME']}:{self.graph_instance.s['MODE']}",
            elevation=0,
            type="custom",
            content_cls=DialogGraphSettingsContent(self, self.dialog),
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
        self.dialog.open()

    def PreDismiss(self, *args):
        if not self.isDeleting:
            self.graph_instance.UnAccentIt()
            self.isDeleting = False

    def Close(self, *args):
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
                snackbar = Snackbar(
                    text="Вы не подключены к серверу!",
                    snackbar_x="10sp",
                    snackbar_y="10sp",
                )

                def ds(arg):
                    Clock.schedule_once(kivy_instance.Connect, 1)
                    snackbar.dismiss()

                snackbar.size_hint_x = (Window.width - (snackbar.snackbar_x * 2)) / Window.width
                snackbar.buttons = [
                    MDFlatButton(
                        text="CONNECT",
                        text_color=(1, 1, 1, 1),
                        on_release=ds,
                    ),
                    MDFlatButton(
                        text="CANCEL",
                        text_color=(1, 1, 1, 1),
                        on_release=snackbar.dismiss,
                    ),
                ]
                snackbar.open()
                return True

        if state == "edit_name" and '*' not in init_text:
            snackbar = Snackbar(
                text="Нельзя поменять название этой переменной!",
                snackbar_x="10sp",
                snackbar_y="10sp",
            )
            snackbar.size_hint_x = (Window.width - (snackbar.snackbar_x * 2)) / Window.width
            snackbar.open()
        else:
            if state == "edit_name":
                init_text = init_text[1:]
            self.state = state

            if self.state == "expression":

                self.dialog = MDDialog(
                    title=title,
                    elevation=0,
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
                    hint_text=hint_text)

                self.dialog = MDDialog(
                    title=title,
                    elevation=0,
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
            if self.dialog.content_cls.ids.my_text_field.text.strip().replace(' ',
                                                                              '') != '' and self.graph_instance.CheckCollizionName(
                    self.dialog.content_cls.ids.my_text_field.text):
                self.m_parent.SetExpression(self.dialog.content_cls.ids.my_text_field.text)
                self.state = None
                self.dialog.dismiss(force=True)
            else:
                snackbar = Snackbar(
                    text="Некорректный ввод!",
                    snackbar_x="10sp",
                    snackbar_y="10sp",
                )
                snackbar.size_hint_x = (Window.width - (snackbar.snackbar_x * 2)) / Window.width
                snackbar.open()
        else:
            if self.text_field.text.strip().replace(' ', '') != '' and self.graph_instance.CheckCollizionName(
                    self.text_field.text):
                if self.state == 'edit_name':
                    default_name = '*' + self.text_field.text
                    self.graph_instance.UpdateName(default_name, _clear_expression=False)
                    self.m_parent.m_parent.labvar_name = default_name
                    self.m_parent.m_parent.dialog.title = f"{default_name}:{self.graph_instance.s['MODE']}"
                    self.state = None
                    self.dialog.dismiss(force=True)
                    self.m_parent.m_parent.Close()
                    self.m_parent.m_parent.Open()
                if self.state == 'new_var':
                    default_name = '*' + self.text_field.text
                    self.graph_instance.ClearPlot()
                    self.graph_instance.UpdateName(default_name)
                    self.m_parent.m_parent.labvar_name = default_name
                    self.m_parent.dialog.title = f"{default_name}:{self.graph_instance.s['MODE']}"

                    self.state = None
                    self.dialog.dismiss(force=True)
                    self.m_parent.m_parent.m_parent.Close()
                    self.m_parent.m_parent.m_parent.Open()
            else:
                snackbar = Snackbar(
                    text="Некорректный ввод!",
                    snackbar_x="10sp",
                    snackbar_y="10sp",
                )
                snackbar.size_hint_x = (Window.width - (snackbar.snackbar_x * 2)) / Window.width
                snackbar.open()


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
            snackbar = Snackbar(
                text="Вы не подключены к серверу!",
                snackbar_x="10sp",
                snackbar_y="10sp",
            )

            def ds(arg):
                Clock.schedule_once(kivy_instance.Connect, 1)
                snackbar.dismiss()

            snackbar.size_hint_x = (Window.width - (snackbar.snackbar_x * 2)) / Window.width
            snackbar.buttons = [
                MDFlatButton(
                    text="CONNECT",
                    text_color=(1, 1, 1, 1),
                    on_release=ds,
                ),
                MDFlatButton(
                    text="CANCEL",
                    text_color=(1, 1, 1, 1),
                    on_release=snackbar.dismiss,
                ),
            ]
            snackbar.open()
        else:
            self.items.clear()
            self.items.append(ItemConfirm(text='Новое выражение'))
            for element in kivy_instance.LabVarArr:
                self.items.append(ItemConfirm(text=element.name))
            if not self.dialog:
                self.dialog = MDDialogFix(
                    text='Выберите переменную',
                    elevation=0,
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
            else:
                self.dialog.update_items(self.items)
            self.dialog.update_height()
            self.dialog.update_width()
            self.dialog.open()

    def Select(self, *args):
        active_n = -1
        active_nn = -1
        for item in self.items:
            active_n += 1
            if item.ids.check.active:
                active_nn = active_n
                break
        if active_nn > -1:
            if active_nn > 0:
                self.m_parent.m_parent.graph_instance.ClearPlot()
                self.m_parent.m_parent.graph_instance.UpdateName(self.items[active_nn].text)
                self.m_parent.labvar_name = self.items[active_nn].text
                self.m_parent.m_parent.dialog.title = f"{self.items[active_nn].text}:{self.m_parent.m_parent.graph_instance.s['MODE']}"

                self.dialog.dismiss(force=True)
                self.m_parent.m_parent.Close()
                self.m_parent.m_parent.Open()
            else:
                self.new_dialog.Open('new_var', '', 'Название переменной', 'Название должно быть уникальным')
                self.dialog.dismiss(force=True)

    def Close(self, *args):
        self.dialog.dismiss(force=True)
