from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

from kivy.properties import StringProperty
from kivymd.uix.list.list import OneLineAvatarIconListItem


class DialogEndpointContent(MDBoxLayout):
    endpoint = StringProperty('None')

    def __init__(self, _endpoint, **kwargs):
        super().__init__(**kwargs)
        self.endpoint = _endpoint


class DialogEndpoint:

    def __init__(self, _instance, **kwargs):
        super().__init__(**kwargs)
        self.kivy_instance = _instance
        self.dialog = None

    def Open(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Enter the endpoint",
                content_cls=DialogEndpointContent(self.kivy_instance.instance.endpoint),
                elevation=0,
                type="custom",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.kivy_instance.theme_cls.primary_color,
                        on_release=self.dialogEndpointClose,
                    ),
                    MDFlatButton(
                        text="SAVE",
                        theme_text_color="Custom",
                        text_color=self.kivy_instance.theme_cls.primary_color,
                        on_release=self.dialogEndpointSave,
                    ),
                ],
            )
        self.dialog.open()

    def dialogEndpointSave(self, *args):
        self.kivy_instance.instance.endpoint = str(self.dialog.content_cls.ids.dialog_endpoint_text_input.text)
        self.dialog.dismiss(force=True)

    def dialogEndpointClose(self, *args):
        self.dialog.dismiss(force=True)


class ItemConfirm(OneLineAvatarIconListItem):
    divider = None

    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False


class DialogListLabVar:

    def __init__(self, _instance, **kwargs):
        super().__init__(**kwargs)
        self.kivy_instance = _instance
        self.dialog = None
        self._items = []
        self.id = None

    def Open(self, _id):
        self.id = _id
        temp_items = []
        for element in self.kivy_instance.instance.LabVarArr:
            temp_items.append(ItemConfirm(text=element.name))
        if len(temp_items) == 0:
            pass
        else:
            self._items.clear()
            self._items = temp_items
            if not self.dialog:
                self.dialog = MDDialog(
                    title="Variables list",
                    text="Choose necessary variable",
                    size_hint=(0.8, 1),
                    elevation=0,
                    type="confirmation",
                    items=self._items,
                    buttons=[
                        MDFlatButton(
                            text="CANCEL",
                            theme_text_color="Custom",
                            text_color=self.kivy_instance.theme_cls.primary_color,
                            on_release=self.DialogListLabVarClose,
                        ),
                        MDFlatButton(
                            text="SELECT",
                            theme_text_color="Custom",
                            text_color=self.kivy_instance.theme_cls.primary_color,
                            on_release=self.DialogListLabVarSelect,
                        ),
                    ],
                )
            else:
                self.dialog.update_items(self._items)
            self.dialog.open()

    def DialogListLabVarSelect(self, *args):
        active_n = -1
        active_nn = -1
        for item in self._items:
            active_n += 1
            if item.ids.check.active:
                active_nn = active_n
                break
        if active_nn > -1:
            self.kivy_instance.instance.GraphContainer.GraphArr[int(self.id)].ClearPlot()
            self.kivy_instance.instance.GraphContainer.GraphArr[int(self.id)].SetLabVarName(self._items[active_nn].text)
            self.kivy_instance.instance.GraphContainer.GraphArr[int(self.id)].SetLabVarValue(str("0"))
        self.dialog.dismiss(force=True)

    def DialogListLabVarClose(self, *args):
        self.dialog.dismiss(force=True)
