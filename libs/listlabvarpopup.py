from libs.kivyapp import KivyApp
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from libs.touchablelabel import TouchableLabel


class ListLabVarPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.isNotOpened = True

    def open(self, _id, *largs, **kwargs):
        if self.isNotOpened:
            for element in KivyApp.instance.LabVarArr:
                temp = TouchableLabel()
                temp.text = element.name
                temp.size_hint_y = None
                temp.size[1] = '50sp'
                temp.id = _id
                temp.bind(on_release=self.SelectedVarCallback)
                self.ids.list_box.add_widget(temp)
            self.isNotOpened = False
        super(ListLabVarPopup, self).open()

    def SelectedVarCallback(self, instance):
        KivyApp.instance.GraphContainer.GraphArr[instance.id].SetLabVarName(instance.text)
        KivyApp.instance.GraphContainer.GraphArr[instance.id].SetLabVarValue(str("0"))
        self.dismiss()

