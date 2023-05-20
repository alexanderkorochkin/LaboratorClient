import logging
import os
import threading

from kivy.core.clipboard import Clipboard

from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, OptionProperty, BooleanProperty, \
    ListProperty, partial
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineIconListItem
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivy.logger import Logger, LOG_LEVELS, LoggerHistory
from kivy.lang import Builder
from kivy.factory import Factory
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.textfield import MDTextField

from libs.android_permissions import AndroidPermissions
from libs.controls import ControlButton
from libs.settings.settings_mod import SettingsWithNoMenu
from libs.utils import *
from libs.settings.settingsJSON import *
from libs.opcua.opcuaclient import client
from libs.graph import GraphBox
from libs.dialogs import LDialogEnterString, LDialogGraphSettings, LDialogList, LDialogMenu
from libs.layoutManager import LayoutManager

Logger.setLevel(LOG_LEVELS["debug"])


class GContainer(MDBoxLayout):
    gcontainer = ObjectProperty(None)
    scrollview = ObjectProperty(None)
    columns = NumericProperty(1)
    spacing_value = NumericProperty(dp(5))

    def __init__(self, _kivy_instance, **kwargs):
        super().__init__(**kwargs)
        self.kivy_instance = _kivy_instance
        self.GraphArr = []
        self.columns = 1
        self.target_height = 0
        self.bind(height=self.ResizeGraphs)

    def ResizeGraphsLow(self):
        d_ori = self.kivy_instance.main_app.d_ori
        d_type = self.kivy_instance.main_app.d_type

        number_graphs = len(self.kivy_instance.main_container.GraphArr)
        if d_ori == 'horizontal':
            if number_graphs == 1:
                self.target_height = self.height
            elif number_graphs == 2 or number_graphs == 3 or number_graphs == 4:
                if d_type == 'tablet':
                    self.target_height = (1 / msettings.get('ROW_HT')) * (
                            self.height - (msettings.get('ROW_HT') - 1) * PADDING)
                else:
                    self.target_height = (1 / 2) * (self.height - 1 * PADDING)
            else:
                if d_type == 'desktop':
                    self.target_height = (1 / msettings.get('ROW_HD')) * (
                            self.height - (msettings.get('ROW_HD') - 1) * PADDING)
                elif d_type == 'tablet':
                    self.target_height = (1 / msettings.get('ROW_HT')) * (
                            self.height - (msettings.get('ROW_HT') - 1) * PADDING)
                elif d_type == 'mobile':
                    self.target_height = (1 / msettings.get('ROW_HM')) * (
                            self.height - (msettings.get('ROW_HM') - 1) * PADDING)
        elif d_ori == 'vertical':
            if d_type == 'desktop':
                self.target_height = (1 / msettings.get('ROW_VD')) * (
                        self.height - (msettings.get('ROW_VD') - 1) * PADDING)
            elif d_type == 'tablet':
                self.target_height = (1 / msettings.get('ROW_VT')) * (
                        self.height - (msettings.get('ROW_VT') - 1) * PADDING)
            elif d_type == 'mobile':
                self.target_height = (1 / msettings.get('ROW_VM')) * (
                        self.height - (msettings.get('ROW_VM') - 1) * PADDING)

        for graph in self.GraphArr:
            graph.Resize(self.target_height)

    def ResizeGraphs(self, *args):
        threading.Thread(target=self.ResizeGraphsLow).start()

    def UpdateColumns(self, *args):
        d_ori = self.kivy_instance.main_app.d_ori
        d_type = self.kivy_instance.main_app.d_type
        value = 1
        number_graphs = len(self.GraphArr)
        if d_ori == 'horizontal':
            if number_graphs == 1:
                value = 1
            elif number_graphs == 2 or number_graphs == 3 or number_graphs == 4:
                value = 2
            else:
                if d_type == 'desktop':
                    value = msettings.get('COL_HD')
                elif d_type == 'tablet':
                    value = msettings.get('COL_HT')
                elif d_type == 'mobile':
                    value = msettings.get('COL_HM')
        else:
            if d_type == 'desktop':
                value = msettings.get('COL_VD')
            elif d_type == 'tablet':
                value = msettings.get('COL_VT')
            elif d_type == 'mobile':
                value = msettings.get('COL_VM')

        self.columns = value

    def isContainsGraphWithName(self, _labvar_name):
        for graph in self.GraphArr:
            if graph.s['NAME'] == _labvar_name:
                return True
        return False

    def UpdateThreads(self):
        for graph in self.GraphArr:
            graph.UpdateThread()

    def UpdateGraphs(self):
        for graph in self.GraphArr:
            graph.UpdateGraph()

    def RefreshAll(self):
        for gr in self.GraphArr:
            gr.ClearGraph()

    def AddGraph(self, settings=None, *args):
        graphbox = GraphBox(self.kivy_instance, settings=settings)

        self.GraphArr.append(graphbox)
        self.gcontainer.add_widget(graphbox)
        Logger.debug(f"GRAPH: Graph [{graphbox.s['NAME']}] with HASH: {graphbox.s['HASH']} is added!")

    def GetGraphByHASH(self, _hash):
        for x in self.GraphArr:
            if x.s['HASH'] == _hash:
                return x
        return None

    def RemoveAll(self):
        for graph in self.GraphArr:
            self.RemoveGraphLow(anim=None, graph=graph, do_remove_graph=False)
        self.GraphArr.clear()
        self.ResizeGraphs()

    def RemoveGraph(self, graph):
        animate_graph_removal(graph, self.RemoveGraphLow)

    def RemoveGraphLow(self, anim, graph, do_remove_graph=True):
        self.gcontainer.remove_widget(graph)
        if do_remove_graph:
            self.GraphArr.remove(graph)
            self.ResizeGraphs()
        self.UpdateColumns()
        Logger.debug(f"GRAPH: Graph [{graph.s['NAME']}] with HASH: {graph.s['HASH']} is removed!")
        self.kivy_instance.main_app.layoutManager.SaveLayout()


class LaboratorClient(MDScreen):
    endpoint = StringProperty()
    number_selected = NumericProperty(0)
    selected_badge_icon = StringProperty('numeric-0')
    show_menu = BooleanProperty(True)
    show_controls_menu = BooleanProperty(False)
    server_connected = BooleanProperty(False)
    controlsArray = []

    def __init__(self, _main_app, **kwargs):
        super().__init__(**kwargs)
        self.addThread = None
        self.main_container = GContainer(self)
        self.main_app = _main_app
        self.isFirst = True
        self.canceled = False
        self.selected = []
        self.show_menu = True
        self.dialog = None

        self.controlsArray = []

    def open_main_settings(self):
        self.main_app.open_main_settings()

    def Prepare(self):
        self.ids.view_port.add_widget(self.main_container)
        self.endpoint = msettings.get('LAST_IP')

        animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)

    def GetGraphByHASH(self, _hash):
        return self.main_container.GetGraphByHASH(_hash)

    def AddGraphManual(self, *args):
        schedule(partial(self.main_container.AddGraph, None), 1)
        schedule(self.main_container.UpdateColumns, 2)
        schedule(self.main_container.ResizeGraphs, 3)
        self.ScrollToLastGraph()

    def AddGraph(self, settings=None):
        self.main_container.AddGraph(settings)

    def ScrollToLastGraph(self):
        app = self.main_app
        if len(self.main_container.GraphArr) > msettings.get(
                'COL_' + str.capitalize(app.d_ori[0]) + str.capitalize(app.d_type[0])) * msettings.get(
            'ROW_' + str.capitalize(app.d_ori[0]) + str.capitalize(app.d_type[0])):
            self.main_container.ids.scroll_view.scroll_to(self.main_container.GraphArr[-1])

    def AddGraphsCallbackLow(self, count, *args):
        if count > 0:
            for i in range(count):
                schedule(self.AddGraphManual, 2 * i)

    def AddGraphsCallback(self, count):
        Clock.schedule_once(partial(self.AddGraphsCallbackLow, int(count)), 0.2)

    def AddGraphs(self, *args):
        self.main_app.dialogTextInput.Open('int', 'Создать графики', 'CREATE', 'CANCEL', self.AddGraphsCallback, '1', 'Одновременно можно создать не более 100 шт.')

    def AddControl(self, settings=None, *args):
        control = ControlButton(self.main_app, settings)
        self.controlsArray.append(control)
        self.ids.controls_view_port.add_widget(control)
        if settings is None:
            self.show_controls_menu = True
            msettings.set('MainSettings', 'SHOW_CONTROLS_BY_DEFAULT', True)
            Clock.schedule_once(self.main_app.layoutManager.SaveLayout, 0.5)
        else:
            self.show_controls_menu = bool(msettings.get('SHOW_CONTROLS_BY_DEFAULT'))

    def RefreshAll(self):
        self.main_container.RefreshAll()

    def SwapShowMenu(self):
        self.show_menu = not self.show_menu

    def isControls(self):
        if self.controlsArray:
            return True
        else:
            return False

    def SwapShowControlsMenu(self):
        if self.controlsArray:
            self.show_controls_menu = not self.show_controls_menu
            msettings.set('MainSettings', 'SHOW_CONTROLS_BY_DEFAULT', int(self.show_controls_menu))

    def GetNumberSelected(self):
        return len(self.selected)

    def Selected(self, graph):
        if not self.selected:
            animated_show_widget_only(self.ids.selection_controls, self.main_app.show_widget_only_anim)
        self.selected.append(graph)
        self.number_selected += 1

    def Unselected(self, graph):
        self.selected.remove(graph)
        if not self.selected:
            animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)
        self.number_selected -= 1

    def UnselectAll(self, excepted=None):
        if self.selected and self.number_selected > 0:
            for graph in self.selected:
                if graph is not excepted:
                    graph.UnChooseIt()
            self.selected = []
            self.number_selected = 0
            animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)

    def RemoveSelectedGraphs(self):
        for selected_graph in self.selected:
            self.main_container.RemoveGraph(selected_graph)
        self.selected = []
        self.number_selected = 0
        animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)

    def RemoveAll(self):
        self.main_container.RemoveAll()
        for cButton in self.controlsArray:
            self.ids.controls_view_port.remove_widget(cButton)
        self.controlsArray.clear()

    def CheckConnection(self):
        return client.isParsed() and client.isConnected() and not client.isReconnecting()

    def GoodConnection(self):
        msettings.set('MainSettings', 'LAST_IP', self.endpoint)
        Logger.debug(f"CONNECT: Connected to {self.endpoint}!")

    def ConnectionFail(self, out, reconnecting=False):
        if reconnecting:
            self.SetServerState('reconnecting')
            Logger.debug(out)
        else:
            self.SetServerState('disconnected')
            Logger.debug(out)

    def Connect(self):
        client._isAbort = False
        client._isReconnecting = False
        Logger.debug(f"CONNECT: Trying to connect to {self.endpoint}...")
        self.SetServerState('blocked')
        client.Connect(self.endpoint)

    def Disconnect(self):
        self.SetServerState('blocked')
        client.Disconnect(force=True)

    def SetServerState(self, state):
        if state == 'blocked':
            self.ids.endpoint_label.disabled = True
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = True
            self.ids.indicator.color = 'white'
        elif state == 'connected':
            self.ids.endpoint_label.disabled = True
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.indicator.color = 'green'
        elif state == 'disconnected':
            self.ids.endpoint_label.disabled = False
            self.ids.btn_connect.disabled = False
            self.ids.btn_disconnect.disabled = True
            self.ids.indicator.color = 'red'
            Logger.debug(f"CONNECT: Disconnected from {self.endpoint}!")
        elif state == 'reconnecting':
            self.ids.endpoint_label.disabled = True
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.indicator.color = 'orange'

    def UpdateControls(self):
        for control in self.controlsArray:
            control.Update()

    def Update(self):
        if self.CheckConnection():

            if not self.server_connected:
                self.server_connected = True
                self.main_app.dialogList.Rebase()
                self.SetServerState('connected')

            threading.Thread(target=client.UpdateValues).start()
            threading.Thread(target=self.main_container.UpdateThreads).start()
            self.main_container.UpdateGraphs()
            self.UpdateControls()
        else:
            if self.server_connected:
                self.server_connected = False


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


class KivyApp(MDApp):
    d_type = OptionProperty('mobile', options=('desktop', 'tablet', 'mobile'))
    d_ori = OptionProperty('vertical', options=('vertical', 'horizontal'))
    d_iori = OptionProperty('horizontal', options=('vertical', 'horizontal'))
    main_radius = NumericProperty(dp(10))
    main_spacing = NumericProperty(dp(5))
    main_padding = NumericProperty(dp(5))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ori_time_good = True
        self.dont_gc = None
        self.kivy_instance = None
        self.settings_widget = None
        self.layoutManager = None
        self.title = "Laborator Client"
        self.hiddenWidgets = []

        self.dialogTextInput = None
        self.dialogGraphSettings = None
        self.dialogList = None
        self.dialogMenu = None

        t = Clock.create_trigger(self.d_changed)

        self.bind(d_ori=t, d_type=t)

    def d_changed(self, *args):
        self.kivy_instance.main_container.UpdateColumns()

    def on_stop(self):
        try:
            client.Disconnect()
            self.layoutManager.SaveLayout()
        except Exception:
            Logger.error("KivyApp: Error while disconnecting on app stop!")

    def Update(self, *args):
        self.kivy_instance.Update()

    def on_start(self):
        self.kivy_instance.Prepare()
        self.dont_gc = AndroidPermissions(self.start_app)

        if platform == "android":
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            ActivityInfo = autoclass("android.content.pm.ActivityInfo")
            activity = PythonActivity.mActivity
            # set orientation according to user's preference
            activity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER)

        if msettings.get('USE_LAYOUT'):
            self.layoutManager.LoadLayout()

        Logger.debug('LayoutManager: Pre-caching...')
        Clock.schedule_once(self.PreCache, 0)

        Clock.schedule_interval(self.Update, int(msettings.get('KIVY_UPDATE_FUNCTION_TIME')))

    def start_app(self):
        self.dont_gc = None

    @staticmethod
    def LoadKV():
        for filename in os.listdir(os.path.join("libs", "kv")):
            Builder.load_file(os.path.join("libs", "kv", filename))

    def update_ori_is_good(self, *args):
        self.ori_time_good = True

    def update_orientation(self, *args):
        if self.ori_time_good:
            self.ori_time_good = False
            Clock.schedule_once(self.update_orientation_low)
            Clock.schedule_once(self.update_ori_is_good, 0.2)

    def update_orientation_low(self, *args):
        if len(args) > 1:
            width, height = args[1]
        else:
            width, height = self.root_window.size
        if width < dp(500) or height < dp(500):
            device_type = "mobile"
        elif width < dp(1100) and height < dp(1100):
            device_type = "tablet"
        else:
            if platform != 'android' and platform != 'ios':
                device_type = "desktop"
            else:
                device_type = 'mobile'

        if width > height:
            device_orientation = 'horizontal'
            inverted_device_orientation = 'vertical'
        else:
            device_orientation = 'vertical'
            inverted_device_orientation = 'horizontal'

        self.d_ori = device_orientation
        self.d_type = device_type
        self.d_iori = inverted_device_orientation

    def build(self):

        Factory.register('OpacityScrollEffectSmooth', module='libs.effects.opacityscrollsmooth')

        self.theme_cls.theme_style = msettings.get("THEME")
        if msettings.get("THEME") == 'Light':
            self.theme_cls.set_colors("Purple", "300", "50", "800", "Gray", "600", "50", "800")
        else:
            self.theme_cls.set_colors("Orange", "300", "50", "800", "Gray", "600", "50", "800")
        self.LoadKV()
        self.kivy_instance = LaboratorClient(self)
        client.kivy_instance = self.kivy_instance

        Window.bind(size=self.update_orientation,
                    # on_maximize=self.update_orientation,
                    # on_restore=self.update_orientation,
                    on_rotate=self.update_orientation,
                    # on_minimize=self.update_orientation
                    )

        Logger.addHandler(FullLogHandler(self, self.kivy_instance.ids.log_label, logging.DEBUG))

        self.hide_widget(self.kivy_instance.ids.log_box)

        self.dialogTextInput = LDialogEnterString(self)
        self.dialogGraphSettings = LDialogGraphSettings(self)
        self.dialogList = LDialogList(self)
        self.dialogMenu = LDialogMenu(self)
        self.layoutManager = LayoutManager(self.kivy_instance)

        if self._app_settings is None:
            self._app_settings = self.create_settings()

        return self.kivy_instance

    def build_config(self, config):
        config.setdefaults('MainSettings', settings_defaults)
        config.setdefaults('GraphSettings', graph_settings_defaults)
        msettings.instance = self.config

    def on_config_change(self, config, section, key, value):
        Logger.debug(f'{section}: {key} is {value}')

    def toggle_log(self):
        self.hide_widget(self.kivy_instance.ids.log_box)

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

    def build_settings(self, settings):
        self.settings_widget = settings
        settings.add_json_panel('Основные настройки', self.config, data=settings_json)

    def create_settings(self):
        if self.settings_cls is None:
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

    def open_settings(self, *largs):
        displayed = self.display_settings(self._app_settings)
        if displayed:
            return True
        return False

    def close_settings(self, *largs):
        win = self._app_window
        settings = self._app_settings
        if win is None or settings is None:
            return
        if settings in win.children:
            win.remove_widget(settings)
            return True
        return False

    def display_settings(self, settings):
        win = self._app_window
        if not win:
            raise Exception('No windows are set on the application, you cannot'
                            ' open settings yet.')
        if settings not in win.children:
            win.add_widget(settings)
            return True
        return False

    def menu_open(self, instance):
        self.dialogMenu.Open()

    def setEndpoint(self, string):
        self.kivy_instance.endpoint = string

    def copy(self, _str: str):
        Clipboard.copy(_str)

    def PreCache(self, *args):
        self.dialogTextInput.PreCache()
        self.dialogGraphSettings.PreCache()
        self.dialogList.PreCache()
        self.dialogMenu.PreCache()


KivyApp = KivyApp()

# TODO Вывести статистику в каждом графике
# TODO Реализовать кнопки для управления стендом
# TODO Написать справку по программе
# TODO Реализовать экранирование скобок для вывода в виджетах (kivy.label documentation )
