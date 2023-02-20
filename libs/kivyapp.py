import logging
import os

from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.uix.menu import MDDropdownMenu
from kivy.animation import Animation
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, OptionProperty, BooleanProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineIconListItem
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivy.logger import Logger, LOG_LEVELS, LoggerHistory
from kivy.lang import Builder
from kivy.factory import Factory

from libs.settings.settingsJSON import *
from libs.opcua.opcuaclient import client
from libs.graph import GraphBox
from libs.dialogs import DialogEndpoint, SnackbarMessage
from libs.layoutManager import LayoutManager

Logger.setLevel(LOG_LEVELS["debug"])


def animated_hide_widget_only(wid, method):
    anim = Animation(pos=(wid.pos[0], sp(10) - sp(200)), opacity=0, duration=0.2, t='in_quart')
    anim.bind(on_complete=method)
    anim.start(wid)


def animated_show_widget_only(wid, method):
    anim = Animation(pos=(wid.pos[0], sp(10)), opacity=1,  duration=0.2, t='out_quart')
    anim.bind(on_start=method)
    anim.start(wid)


def animate_graph_removal(wid, method):
    # animate shrinking widget width
    anim = Animation(opacity=0, height=0, duration=0.5, t='out_expo')
    anim.bind(on_complete=method)
    t = wid.gardenGraph._trigger
    ts = wid.gardenGraph._trigger_size
    wid.gardenGraph.unbind(center=ts, padding=ts, precision=ts, plots=ts, x_grid=ts,
                           y_grid=ts, draw_border=ts)
    wid.gardenGraph.unbind(xmin=t, xmax=t, xlog=t, x_ticks_major=t, x_ticks_minor=t,
                           xlabel=t, x_grid_label=t, ymin=t, ymax=t, ylog=t,
                           y_ticks_major=t, y_ticks_minor=t, ylabel=t, y_grid_label=t,
                           font_size=t, label_options=t, x_ticks_angle=t)
    anim.start(wid)


class GContainer(MDBoxLayout):
    gcontainer = ObjectProperty(None)
    scrollview = ObjectProperty(None)
    columns = NumericProperty(1)
    spacing_value = NumericProperty(sp(5))

    def __init__(self, _kivy_instance, **kwargs):
        super().__init__(**kwargs)
        self.kivy_instance = _kivy_instance
        self.GraphArr = []
        self.columns = 1

    def ResizeGraphs(self, d_ori, d_type):
        for graph in self.GraphArr:
            graph.Resize(d_ori, d_type)

    def UpdateColumns(self, d_ori, d_type):
        value = -1
        number_graphs = len(self.GraphArr)
        if d_ori == 'horizontal':
            if number_graphs == 1:
                value = 1
            elif number_graphs == 2 or number_graphs == 3 or number_graphs == 4:
                value = 2
            else:
                if d_type == 'desktop':
                    value = msettings.get('COL_HD')
                if d_type == 'tablet':
                    value = msettings.get('COL_HT')
                if d_type == 'mobile':
                    value = msettings.get('COL_HM')
        elif d_ori == 'vertical':
            if d_type == 'desktop':
                value = msettings.get('COL_VD')
            if d_type == 'tablet':
                value = msettings.get('COL_VT')
            if d_type == 'mobile':
                value = msettings.get('COL_VM')
        self.columns = value

    def isContainsGraphWithName(self, _labvar_name):
        for graph in self.GraphArr:
            if graph.s['NAME'] == _labvar_name:
                return True
        return False

    def RefreshAll(self):
        for gr in self.GraphArr:
            gr.ClearGraph()

    def AddGraph(self, _settings=None):
        graphbox = GraphBox(self.kivy_instance, settings=_settings)
        self.GraphArr.append(graphbox)
        self.gcontainer.add_widget(graphbox)
        if not _settings:
            self.ResizeGraphs(self.kivy_instance.main_app.d_ori, self.kivy_instance.main_app.d_type)
            self.UpdateColumns(self.kivy_instance.main_app.d_ori, self.kivy_instance.main_app.d_type)
        Logger.debug(f"GRAPH: Graph [{graphbox.s['NAME']}] with HASH: {graphbox.s['HASH']} is added!")

    def GetGraphByHASH(self, _hash):
        for x in self.GraphArr:
            if x.s['HASH'] == _hash:
                return x
        return None

    def RemoveGraphByHASH(self, _hash):
        animate_graph_removal(self.GetGraphByHASH(_hash), self.RemoveGraph)

    def RemoveGraph(self, anim, graph):
        if len(self.GraphArr) > 0:
            temp = graph
            self.gcontainer.remove_widget(temp)
            self.GraphArr.remove(temp)
            self.ResizeGraphs(self.kivy_instance.main_app.d_ori, self.kivy_instance.main_app.d_type)
            self.UpdateColumns(self.kivy_instance.main_app.d_ori, self.kivy_instance.main_app.d_type)
            Logger.debug(f"GRAPH: Graph [{temp.s['NAME']}] with HASH: {temp.s['HASH']} is removed!")


class Item(OneLineIconListItem):
    left_icon = StringProperty()


class LaboratorClient(MDScreen):
    endpoint = StringProperty()
    number_selected = NumericProperty(0)
    show_menu = BooleanProperty(True)

    def __init__(self, _main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_container = GContainer(self)
        self.main_app = _main_app
        self.isFirst = True
        self.selected = []
        self.show_menu = True

        self.LabVarArr = []

        menu_items = [
            {
                "text": 'Добавить график',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'plus',
                "font_size": sp(12),
                "on_release": self.AddGraph,
            },
            {
                "text": 'Обновить графики',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'refresh',
                "font_size": sp(12),
                "on_release": self.RefreshAll,
            },
            {
                "text": 'Показать лог' if msettings.get('HIDE_LOG_BY_DEFAULT') else 'Скрыть лог',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'math-log',
                "font_size": sp(12),
                "on_release": self.main_app.ToggleLog,
            },
            {
                "text": 'Настройки',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'cog-outline',
                "font_size": sp(12),
                "on_release": self.main_app.open_main_settings,
            },
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.menu_button,
            items=menu_items,
            width_mult=4,
            max_height=0,
        )

    def Prepare(self):
        self.ids.view_port.add_widget(self.main_container)
        self.endpoint = msettings.get('LAST_IP')
        self.animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)

    def GetGraphByHASH(self, _hash):
        return self.main_container.GetGraphByHASH(_hash)

    def AddGraph(self, _settings=None):
        self.main_container.AddGraph(_settings)
        if _settings is None:
            self.menu.dismiss()

    def RefreshAll(self):
        self.main_container.RefreshAll()
        self.menu.dismiss()

    def SwapShowMenu(self):
        self.show_menu = not self.show_menu
        self.main_app.update_orientation()

    @staticmethod
    def animated_hide_widget_only(wid, method):
        animated_hide_widget_only(wid, method)

    @staticmethod
    def animated_show_widget_only(wid, method):
        animated_show_widget_only(wid, method)

    def GetNumberSelected(self):
        return len(self.selected)

    def Selected(self, graph):
        if not self.selected:
            self.animated_show_widget_only(self.ids.selection_controls, self.main_app.show_widget_only_anim)
        self.selected.append(graph)
        self.number_selected += 1

    def Unselected(self, graph):
        self.selected.remove(graph)
        if not self.selected:
            self.animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)
        self.number_selected -= 1

    def UnselectAll(self):
        for graph in self.selected:
            graph.UnChooseIt()
        self.selected = []
        self.number_selected = 0
        self.animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)

    def RemoveSelectedGraphs(self):
        for selected_graph in self.selected:
            self.main_container.RemoveGraph(None, selected_graph)
        self.selected = []
        self.animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)

    def RemoveGraphByHASH(self, _hash):
        self.main_container.RemoveGraphByHASH(_hash)

    def LabVarArrConfigure(self, path):
        Logger.debug("LabVarConf: Getting configuration from server...")
        arr = client.GetVarsFromNode()

        for var in arr:
            for child in client.lab_node.get_children():
                if str(child.get_browse_name()).find(str(var.name)) != -1:
                    var.browse_name = str(child.get_browse_name())
                    var.node_id = str(child)
                    Logger.debug("PARSEVARS: [" + var.name + "], the browse_name is: [" + str(
                        var.browse_name) + "], NodeId: [" + var.node_id + "]")

        self.LabVarArr = arr

    def GetNamesArr(self):
        if self.LabVarArr:
            names = []
            for var in self.LabVarArr:
                names.append(var.name)
            return names
        else:
            return []

    def Reconnection(self, dt):
        if client.GetReconnectNumber() <= msettings.get('MAX_RECONNECTIONS_NUMBER'):
            if client.isReconnecting():
                if not client.isConnected():
                    client._isReconnecting = True
                    client.Disconnect()
                    self.Connect()
                    if not client.isConnected():
                        Clock.schedule_once(self.Reconnection, dt)
                        client.ReconnectNumberInc()
                    else:
                        client.ReconnectNumberZero()
                else:
                    client._isReconnecting = False
                    client.ReconnectNumberZero()
            else:
                client.ReconnectNumberZero()
        else:
            self.Disconnect()

    def ConnectLow(self, dt):
        try:
            client.Connect(self.endpoint)
            self.LabVarArrConfigure(msettings.get('CONFIGURATION_PATH'))
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.endpoint_label.disabled = True
            Logger.debug(f"CONNECT: Connected to {self.endpoint}!")
            self.ids.info_log.text = f"Connected to {self.endpoint}!"
            SnackbarMessage(f"Connected to {self.endpoint}!")
            msettings.set('allSettings', 'LAST_IP', self.endpoint)
        except Exception:
            if not client.isReconnecting():
                self.ids.btn_connect.disabled = False
                self.ids.btn_disconnect.disabled = True
                self.ids.endpoint_label.disabled = False
                self.ids.info_log.text = "Error while connecting... Disconnected!"
                SnackbarMessage("Error while connecting... Disconnected!")
                Logger.error("CONNECT: Error while connecting... Disconnected!")
            else:
                self.ids.info_log.text = f"Connection lost! Error while reconnecting... ({str(client.GetReconnectNumber())})"
                SnackbarMessage(f"Connection lost! Error while reconnecting... ({str(client.GetReconnectNumber())})")
                Logger.error("CONNECT: Connection lost! Error while reconnecting... (" + str(client.GetReconnectNumber()) + ')')

    def Connect(self, *args):
        self.ids.info_log.text = f"Trying connect to {self.endpoint}!"
        self.ids.btn_connect.disabled = True
        Clock.schedule_once(self.ConnectLow, 0)

    def Disconnect(self):
        client._isReconnecting = False
        try:
            client.Disconnect()
            self.ids.btn_disconnect.disabled = True
            self.ids.btn_connect.disabled = False
            self.ids.endpoint_label.disabled = False
            self.ids.info_log.text = f"Disconnected from {self.endpoint}!"
            Logger.debug(f"CONNECT: Disconnected from {self.endpoint}!")
        except Exception:
            self.ids.btn_disconnect.disabled = False
            self.ids.btn_connect.disabled = True
            self.ids.endpoint_label.disabled = True
            self.ids.info_log.text = "Error while disconnecting..."
            Logger.info("CONNECT: Error while disconnecting...")

    def Update(self, dt):
        if client.isConnected():
            try:
                for graph in self.main_container.GraphArr:
                    graph.Update()
            except Exception:
                client._isConnected = False
                client._isReconnecting = True
                self.ids.btn_disconnect.disabled = False
                self.ids.btn_connect.disabled = True
                self.ids.info_log.text = "Connection lost! Trying to reconnect..."
                Logger.debug("UPDATE: Connection lost! Trying to reconnect...")
                self.Reconnection(msettings.get('RECONNECTION_TIME'))

    def GetLabVarByName(self, name):
        for labvar in self.LabVarArr:
            if labvar.name == name:
                return labvar
        return None


class FullLogHandler(logging.Handler):

    def __init__(self, _kivy_instance, _label, level=logging.NOTSET):
        super(FullLogHandler, self).__init__(level=level)
        self.label = _label
        self.kivy_instance = _kivy_instance

    def emit(self, record):
        def f(dt=None):
            self.label.text = "\n".join(list(map(self.format, LoggerHistory.history[::-1])))
            self.label.scroll_y = 0

        Clock.schedule_once(f)


class HoldBehavior(ButtonBehavior):
    __events__ = ['on_hold']
    timeout = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._event = None
        self.timeout = msettings.get('KIVY_DOUBLETAP_TIME')

    def _cancel(self):
        if self._event:
            self._event.cancel()

    def on_press(self):
        self._cancel()
        self._event = Clock.schedule_once(lambda *x: self.dispatch('on_hold'), self.timeout)
        return super().on_press()

    def on_hold(self, *args):
        pass

    def on_release(self):
        self._cancel()


class KivyApp(MDApp):
    d_type = OptionProperty('mobile', options=('desktop', 'tablet', 'mobile'))
    d_ori = OptionProperty('vertical', options=('vertical', 'horizontal'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kivy_instance = None
        self.settings_widget = None
        self.title = "Laborator Client"
        self.dialogEndpoint = None
        self.hiddenWidgets = []
        self.layoutManager = None

        Factory.register('HoldBehavior', cls=HoldBehavior)

    def on_stop(self):
        try:
            client.Disconnect()
            self.layoutManager.SaveLayout()
        except Exception:
            Logger.error("KivyApp: Error while disconnecting on app stop!")

    def on_start(self):
        self.kivy_instance.Prepare()
        if msettings.get('USE_LAYOUT'):
            self.layoutManager.LoadLayout()
        Clock.schedule_once(self.update_orientation, 0)
        Clock.schedule_interval(self.kivy_instance.Update, int(msettings.get('KIVY_UPDATE_FUNCTION_TIME')))

    @staticmethod
    def LoadKV():
        for filename in os.listdir(os.path.join("libs", "kv")):
            Builder.load_file(os.path.join("libs", "kv", filename))

    def update_orientation(self, *args):
        Clock.schedule_once(self.update_orientation_low, 0)

    def update_orientation_low(self, *args):
        width, height = Window.size
        if width < dp(500) or height < dp(500):
            device_type = "mobile"
        elif width < dp(1100) and height < dp(1100):
            device_type = "tablet"
        else:
            device_type = "desktop"

        if width > height:
            device_orientation = 'horizontal'
        else:
            device_orientation = 'vertical'

        self.d_ori = device_orientation
        self.d_type = device_type

        Logger.debug(f'ORIENTATION: Changed orientation to: {self.d_type}:{self.d_ori}')

        self.kivy_instance.main_container.UpdateColumns(self.d_ori, self.d_type)
        self.kivy_instance.main_container.ResizeGraphs(self.d_ori, self.d_type)

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.set_colors("Orange", "300", "50", "800", "Gray", "600", "50", "800")
        self.LoadKV()
        self.kivy_instance = LaboratorClient(self)

        Window.bind(size=self.update_orientation,
                    on_maximize=self.update_orientation,
                    on_restore=self.update_orientation,
                    on_rotate=self.update_orientation,
                    on_minimize=self.update_orientation
                    )

        Logger.addHandler(FullLogHandler(self, self.kivy_instance.ids.log_label, logging.DEBUG))

        if msettings.get("HIDE_LOG_BY_DEFAULT"):
            self.hide_widget(self.kivy_instance.ids.log_box)
        else:
            self.hide_widget(self.kivy_instance.ids.view_port)

        self.dialogEndpoint = DialogEndpoint(self)
        self.layoutManager = LayoutManager(self.kivy_instance)

        return self.kivy_instance

    def build_config(self, config):
        config.setdefaults('allSettings', settings_defaults)
        config.setdefaults('GraphSettings', graph_settings_defaults)
        msettings.instance = self.config

    def build_settings(self, settings):
        self.settings_widget = settings
        settings.add_json_panel('Основные настройки', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        Logger.debug(f'{section}: {key} is {value}')

    def create_settings(self):
        if self.settings_cls is None:
            from libs.settings.settings_mod import SettingsWithNoMenu
            self.settings_cls = SettingsWithNoMenu
        else:
            self.settings_cls = Factory.get(self.settings_cls)
        s = self.settings_cls()
        self.build_settings(s)
        if self.use_kivy_settings:
            s.add_kivy_panel()
        s.bind(on_close=self.close_settings,
               on_config_change=self._on_config_change)
        return s

    def ToggleLog(self):
        wid1 = self.kivy_instance.ids.log_box
        wid2 = self.kivy_instance.ids.view_port
        self.hide_widget(wid1)
        if self.kivy_instance.menu.items[2]['text'] == 'Показать лог':
            self.kivy_instance.ids.hide_menu.disabled = True
            self.kivy_instance.menu.items[2]['text'] = 'Скрыть лог'
        else:
            self.kivy_instance.menu.items[2]['text'] = 'Показать лог'
            self.kivy_instance.ids.hide_menu.disabled = False
        self.kivy_instance.menu.dismiss()

    # Swaps visibility of widgets. Wid1 are hiding permanently.(self.ids.log_box, self.ids.view_port)
    def swap_widgets_visibility(self, wid1, wid2):
        if wid1 not in self.hiddenWidgets and wid2 not in self.hiddenWidgets:
            self.hide_widget(wid1)
        elif wid1 in self.hiddenWidgets and wid2 in self.hiddenWidgets:
            self.hide_widget(wid2)
        else:
            self.hide_widget(wid1)
            self.hide_widget(wid2)

    def show_widget_only_anim(self, anim, wid):
        self.show_widget_only(wid)

    def show_widget_only(self, wid):
        if wid in self.hiddenWidgets:
            self.hiddenWidgets.remove(wid)
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs

    def hide_widget_only_anim(self, anim, wid):
        self.hide_widget_only(wid)

    def hide_widget_only(self, wid):
        if wid not in self.hiddenWidgets:
            self.hiddenWidgets.append(wid)
            wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True

    def hide_widget_anim(self, anim, wid):
        self.hide_widget(wid)

    # Hides or shows widget
    def hide_widget(self, wid):
        if wid not in self.hiddenWidgets:
            self.hiddenWidgets.append(wid)
            wid.saved_attrs = wid.height, wid.size_hint_y, wid.opacity, wid.disabled
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = 0, None, 0, True
        else:
            self.hiddenWidgets.remove(wid)
            wid.height, wid.size_hint_y, wid.opacity, wid.disabled = wid.saved_attrs

    def menu_open(self):
        self.kivy_instance.menu.open()

    def open_main_settings(self):
        self.open_settings()
        self.kivy_instance.menu.dismiss()


KivyApp = KivyApp()

# TODO Научиться делать статистический анализ
# TODO Научиться подключаться к LabView
