from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.toast import toast

from kivy.properties import StringProperty, ObjectProperty
from kivymd.uix.list.list import OneLineAvatarIconListItem


from libs.settings.settingsJSON import *


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

    def __init__(self, _parent, **kwargs):
        super().__init__(**kwargs)
        self.m_parent = _parent
        self.dialogListLabVar = DialogListLabVar(self)
        self.labvar_name = self.m_parent.graph_instance.GetLabVarName()

    def removeIt(self):
        self.m_parent.graph_instance.RemoveMe()
        self.m_parent.Close()

    def Refresh(self):
        self.m_parent.graph_instance.ClearGraph()


class DialogGraphSettings:

    def __init__(self, _graph_instance, **kwargs):
        super().__init__(**kwargs)
        self.graph_instance = _graph_instance
        self.dialog = None

    def Open(self):
        self.dialog = MDDialog(
            title="Graph [{}] settings".format(self.graph_instance.s['NAME']),
            elevation=0,
            type="custom",
            content_cls=DialogGraphSettingsContent(self),
            buttons=[
                MDFlatButton(
                    text="CLOSE",
                    theme_text_color="Custom",
                    text_color=self.graph_instance.kivy_instance.main_app.theme_cls.primary_color,
                    on_release=self.Close,
                )
            ],
        )
        self.dialog.open()

    def Close(self, *args):
        self.dialog.dismiss(force=True)


class DialogListLabVar:

    def __init__(self, _parent, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.m_parent = _parent
        self.items = []

    def Open(self):
        if len(self.m_parent.m_parent.graph_instance.kivy_instance.LabVarArr) == 0:
            toast("Вы не подключены к серверу!")
        else:
            self.items.clear()
            for element in self.m_parent.m_parent.graph_instance.kivy_instance.LabVarArr:
                self.items.append(ItemConfirm(text=element.name))
            if not self.dialog:
                self.dialog = MDDialog(
                    title="Variables list",
                    text="Choose necessary variable",
                    size_hint=(0.8, 1),
                    elevation=0,
                    type="confirmation",
                    items=self.items,
                    buttons=[
                        MDFlatButton(
                            text="CANCEL",
                            theme_text_color="Custom",
                            text_color=self.m_parent.m_parent.graph_instance.kivy_instance.main_app.theme_cls.primary_color,
                            on_release=self.Close,
                        ),
                        MDRaisedButton(
                            text="SELECT",
                            theme_text_color="Custom",
                            text_color=self.m_parent.m_parent.graph_instance.kivy_instance.main_app.theme_cls.secondary_text_color,
                            on_release=self.Select,
                        ),
                    ],
                )
            else:
                self.dialog.update_items(self.items)
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
            self.m_parent.m_parent.graph_instance.ClearPlot()
            self.m_parent.m_parent.graph_instance.SetLabVarName(self.items[active_nn].text)
            self.m_parent.labvar_name = self.items[active_nn].text
            self.m_parent.m_parent.graph_instance.SetLabVarValue(str("0"))
        self.dialog.dismiss(force=True)
        self.m_parent.m_parent.dialog.title = "Graph [{}] Settings".format(self.items[active_nn].text)

    def Close(self, *args):
        self.dialog.dismiss(force=True)
