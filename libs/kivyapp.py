import logging
import os

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
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, OptionProperty, BooleanProperty, ListProperty
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
from libs.dialogs import DialogEndpoint, SnackbarMessage, SnackbarMessageAction, MDDialogFix
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

    def ResizeGraphs(self, d_ori, d_type):
        for graph in self.GraphArr:
            graph.Resize(d_ori, d_type, self.height)

    def UpdateColumns(self, d_ori, d_type):
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
        if self.columns != value:
            self.columns = value

    def isContainsGraphWithName(self, _labvar_name):
        for graph in self.GraphArr:
            if graph.s['NAME'] == _labvar_name:
                return True
        return False

    def UpdateGraphs(self, plots_only=False):
        for graph in self.GraphArr:
            graph.Update(plots_only)

    def RefreshAll(self):
        for gr in self.GraphArr:
            gr.ClearGraph()

    def AddGraph(self, _settings=None):
        graphbox = GraphBox(self.kivy_instance, settings=_settings)
        app = self.kivy_instance.main_app
        self.GraphArr.append(graphbox)
        self.gcontainer.add_widget(graphbox)
        if not _settings:
            self.ResizeGraphs(app.d_ori, app.d_type)
            self.UpdateColumns(app.d_ori, app.d_type)
        Logger.debug(f"GRAPH: Graph [{graphbox.s['NAME']}] with HASH: {graphbox.s['HASH']} is added!")
        if not _settings:
            if len(self.GraphArr) > msettings.get(
                    'COL_' + str.capitalize(app.d_ori[0]) + str.capitalize(app.d_type[0])) * msettings.get(
                    'ROW_' + str.capitalize(app.d_ori[0]) + str.capitalize(app.d_type[0])):
                self.ids.scroll_view.scroll_to(graphbox)

    def GetGraphByHASH(self, _hash):
        for x in self.GraphArr:
            if x.s['HASH'] == _hash:
                return x
        return None

    def RemoveAll(self):
        for graph in self.GraphArr:
            self.RemoveGraph(anim=None, graph=graph, do_remove_graph=False)
        self.GraphArr.clear()

    def RemoveGraphByHASH(self, _hash):
        graph = self.GetGraphByHASH(_hash)
        animate_graph_removal(graph, 'vertical' if (
                    self.kivy_instance.main_app.d_type == 'mobile' and self.kivy_instance.main_app.d_ori == 'vertical') else 'horizontal',
                              self.RemoveGraph)

    def RemoveGraph(self, anim, graph, do_remove_graph=True):
        if len(self.GraphArr) > 0:
            temp = graph
            self.gcontainer.remove_widget(temp)
            if do_remove_graph:
                self.GraphArr.remove(temp)
            self.ResizeGraphs(self.kivy_instance.main_app.d_ori, self.kivy_instance.main_app.d_type)
            self.UpdateColumns(self.kivy_instance.main_app.d_ori, self.kivy_instance.main_app.d_type)
            Logger.debug(f"GRAPH: Graph [{temp.s['NAME']}] with HASH: {temp.s['HASH']} is removed!")


class Item(OneLineIconListItem):
    left_icon = StringProperty()


class CircularButton(ButtonBehavior, MDLabel):
    pass


class LaboratorClient(MDScreen):
    endpoint = StringProperty()
    number_selected = NumericProperty(0)
    selected_badge_icon = StringProperty('numeric-0')
    show_menu = BooleanProperty(True)
    show_controls_menu = BooleanProperty(False)
    controlsArray = []

    def __init__(self, _main_app, **kwargs):
        super().__init__(**kwargs)
        self.main_container = GContainer(self)
        self.main_app = _main_app
        self.isFirst = True
        self.selected = []
        self.show_menu = True
        self.dialog = None

        self.controlsArray = []

        self.menu_items = [
            {
                "text": 'Добавить график',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'plus-box',
                "font_style": 'Body1',
                "on_release": self.AddGraph,
            },
            {
                "text": 'Добавить несколько графиков',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'plus-box-multiple',
                "font_style": 'Body1',
                "on_release": self.AddGraphs,
            },
            {
                "text": 'Добавить кнопку',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'card-plus',
                "font_style": 'Body1',
                "on_release": self.AddControls,
            },
            {
                "text": 'Обновить графики',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'refresh',
                "font_style": 'Body1',
                "on_release": self.RefreshAll,
            },
            {
                "text": 'Показать лог' if msettings.get('HIDE_LOG_BY_DEFAULT') else 'Скрыть лог',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'math-log',
                "font_style": 'Body1',
                "on_release": self.main_app.toggle_log,
            },
            {
                "text": 'Показывать кнопки',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'ticket',
                "font_style": 'Body1',
                "on_release": self.SwapShowControlsMenu,
            },
            {
                "text": 'Настройки',
                "viewclass": "Item",
                "height": dp(48),
                "left_icon": 'cog-outline',
                "font_style": 'Body1',
                "on_release": self.open_main_settings,
            }
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.menu_button,
            items=self.menu_items,
            # elevation=3,
            width_mult=5,
        )

    def open_main_settings(self):
        self.main_app.open_main_settings()

    def Prepare(self):
        self.ids.view_port.add_widget(self.main_container)
        self.endpoint = msettings.get('LAST_IP')

        animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)

    def GetGraphByHASH(self, _hash):
        return self.main_container.GetGraphByHASH(_hash)

    def AddGraph(self, settings=None):
        self.main_container.AddGraph(settings)
        if settings is None:
            self.menu.dismiss()

    def AddGraphs(self):
        self.ActionAfterEnterStringDialog('ITERATIVE|DECIMAL', self.AddGraph, 'Введите число графиков',
                                          'Введите целое число графиков')
        self.menu.dismiss()

    def AddControls(self, settings=None):
        control = ControlButton(self.main_app, settings)
        self.controlsArray.append(control)
        self.ids.controls_view_port.add_widget(control)
        if settings is None:
            self.show_controls_menu = True
            msettings.set('MainSettings', 'SHOW_CONTROLS_BY_DEFAULT', True)

            i = 0
            good_id = 0
            name = 'кнопки'
            for item in self.menu.items:
                if name in item['text']:
                    good_id = i
                i += 1
            self.menu.items[good_id]['text'] = 'Скрывать ' + name

            self.menu.dismiss()
            self.main_app.update_orientation()
            self.main_app.layoutManager.SaveLayout()
        else:
            self.show_controls_menu = bool(msettings.get('SHOW_CONTROLS_BY_DEFAULT'))

            i = 0
            good_id = 0
            name = 'кнопки'
            for item in self.menu.items:
                if name in item['text']:
                    good_id = i
                i += 1
            if self.show_controls_menu:
                self.menu.items[good_id]['text'] = 'Скрывать ' + name
            else:
                self.menu.items[good_id]['text'] = 'Показывать ' + name

    def ActionAfterEnterStringDialog(self, mode, action, title, hint_text):

        def Cancel(*args):
            self.dialog.dismiss(force=True)
            self.dialog = None

        def Enter(*args):
            if 'ITERATIVE' in mode:
                if 'DECIMAL' in mode:
                    if self.dialog.content_cls.text.isdecimal():
                        for i in range(int(self.dialog.content_cls.text)):
                            action()
                        self.dialog.dismiss(force=True)
                        self.dialog = None
                    else:
                        SnackbarMessage('Некорректный ввод!')

        self.dialog = MDDialog(
            title=title,
            # elevation=0,
            auto_dismiss=False,
            type="custom",
            content_cls=MDTextField(hint_text=hint_text),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=self.main_app.theme_cls.primary_color,
                    on_release=Cancel,
                ),
                MDFlatButton(
                    text="ENTER",
                    theme_text_color="Custom",
                    text_color=self.main_app.theme_cls.primary_color,
                    on_release=Enter,
                )
            ]
        )
        self.dialog.open()

    def RefreshAll(self):
        self.main_container.RefreshAll()
        self.menu.dismiss()

    def SwapShowMenu(self):
        self.show_menu = not self.show_menu
        self.main_app.update_orientation()

    def isControls(self):
        if self.controlsArray:
            return True
        else:
            return False

    def SwapShowControlsMenu(self):
        if self.controlsArray:
            self.show_controls_menu = not self.show_controls_menu
            msettings.set('MainSettings', 'SHOW_CONTROLS_BY_DEFAULT', int(self.show_controls_menu))
            self.main_app.update_orientation()

            i = 0
            good_id = 0
            name = 'кнопки'
            for item in self.menu.items:
                if name in item['text']:
                    good_id = i
                i += 1
            if self.menu.items[good_id]['text'] == 'Показывать ' + name:
                self.menu.items[good_id]['text'] = 'Скрывать ' + name
            else:
                self.menu.items[good_id]['text'] = 'Показывать ' + name

        self.menu.dismiss()

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
            self.main_container.RemoveGraph(None, selected_graph)
        self.selected = []
        self.number_selected = 0
        SnackbarMessageAction('Отменить удаление', 'UNDO', cancel_button_text='SAVE',
                              accept_action=self.main_app.layoutManager.ReloadLayout,
                              cancel_action=self.main_app.layoutManager.SaveLayout)
        animated_hide_widget_only(self.ids.selection_controls, self.main_app.hide_widget_only_anim)

    def RemoveAll(self):
        self.main_container.RemoveAll()
        for cButton in self.controlsArray:
            self.ids.controls_view_port.remove_widget(cButton)
        self.controlsArray.clear()

    def RemoveGraphByHASH(self, _hash):
        self.main_container.RemoveGraphByHASH(_hash)
        self.main_app.layoutManager.SaveLayout()

    def Reconnection(self, dt):
        if client.GetReconnectNumber() <= msettings.get('MAX_RECONNECTIONS_NUMBER'):
            if client.isReconnecting():
                if not client.isConnected():
                    client._isReconnecting = True
                    client.Disconnect()
                    self.ConnectLow(0)
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
            Logger.debug("LabVarConf: Getting configuration from server...")
            client.Connect(self.endpoint)
            self.ids.btn_connect.disabled = True
            self.ids.btn_disconnect.disabled = False
            self.ids.endpoint_label.disabled = True
            Logger.debug(f"CONNECT: Connected to {self.endpoint}!")
            SnackbarMessage(f"Connected to {self.endpoint}!")
            msettings.set('MainSettings', 'LAST_IP', self.endpoint)
            client.ReconnectNumberZero()
        except Exception:
            if not client.isReconnecting():
                self.ids.btn_connect.disabled = False
                self.ids.btn_disconnect.disabled = True
                self.ids.endpoint_label.disabled = False
                SnackbarMessage("Error while connecting... Disconnected!")
                Logger.error("CONNECT: Error while connecting... Disconnected!")
            else:
                SnackbarMessage(f"Connection lost! Error while reconnecting... ({str(client.GetReconnectNumber())})")
                Logger.error(
                    "CONNECT: Connection lost! Error while reconnecting... (" + str(client.GetReconnectNumber()) + ')')

    def Connect(self, *args):
        self.ids.btn_connect.disabled = True
        self.ConnectLow(0)

    def Disconnect(self):
        client._isReconnecting = False
        try:
            client.Disconnect()
            self.ids.btn_disconnect.disabled = True
            self.ids.btn_connect.disabled = False
            self.ids.endpoint_label.disabled = False
            SnackbarMessage(f"Disconnected from {self.endpoint}!")
            Logger.debug(f"CONNECT: Disconnected from {self.endpoint}!")
        except Exception:
            self.ids.btn_disconnect.disabled = False
            self.ids.btn_connect.disabled = True
            self.ids.endpoint_label.disabled = True
            SnackbarMessage("Error while disconnecting...")
            Logger.info("CONNECT: Error while disconnecting...")

    def UpdateControls(self):
        for control in self.controlsArray:
            control.Update()

    def Update(self):
        if client.isConnected():
            try:
                client.UpdateValues()
            except Exception:
                client._isConnected = False
                client._isReconnecting = True
                self.ids.btn_disconnect.disabled = False
                self.ids.btn_connect.disabled = True
                SnackbarMessage("Connection lost! Trying to reconnect...")
                Logger.debug("UPDATE: Connection lost! Trying to reconnect...")
                self.Reconnection(msettings.get('RECONNECTION_TIME'))
            self.main_container.UpdateGraphs()
            self.UpdateControls()

    def PreCacheAll(self):
        for graph in self.main_container.GraphArr:
            graph.PreCache()


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
    main_radius = NumericProperty(dp(10))
    main_spacing = NumericProperty(dp(5))
    main_padding = NumericProperty(dp(5))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dont_gc = None
        self.kivy_instance = None
        self.settings_widget = None
        self.dialogEndpoint = None
        self.layoutManager = None
        self.title = "Laborator Client"
        self.hiddenWidgets = []
        self._close_button = None

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
        Logger.debug('LayoutManager: Pre-caching...')
        if msettings.get('USE_LAYOUT'):
            self.layoutManager.LoadLayout()
        Clock.schedule_once(self.update_orientation, 0)
        Clock.schedule_interval(self.Update, int(msettings.get('KIVY_UPDATE_FUNCTION_TIME')))

        self.dont_gc = AndroidPermissions(self.start_app)


    def start_app(self):
        self.dont_gc = None

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

        # Logger.debug(f'ORIENTATION: Changed orientation to: {self.d_type}:{self.d_ori}')

        self.kivy_instance.main_container.UpdateColumns(self.d_ori, self.d_type)
        self.kivy_instance.main_container.ResizeGraphs(self.d_ori, self.d_type)
        if client.isConnected():
            self.kivy_instance.main_container.UpdateGraphs(plots_only=True)

        win = self._app_window
        if self._close_button in win.children:
            self._close_button.pos = [dp(5), win.height - dp(53)]

    def build(self):
        self.theme_cls.theme_style = msettings.get("THEME")
        if msettings.get("THEME") == 'Light':
            self.theme_cls.set_colors("Purple", "300", "50", "800", "Gray", "600", "50", "800")
        else:
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

        if self._app_settings is None:
            self._app_settings = self.create_settings()

        return self.kivy_instance

    def build_config(self, config):
        config.setdefaults('MainSettings', settings_defaults)
        config.setdefaults('GraphSettings', graph_settings_defaults)
        msettings.instance = self.config

    def on_config_change(self, config, section, key, value):
        Logger.debug(f'{section}: {key} is {value}')

        if key == 'THEME':
            SnackbarMessage('Тема изменится после перезагрузки приложения')

    def toggle_log(self):
        self.hide_widget(self.kivy_instance.ids.log_box)
        i = 0
        log_id = 0
        for item in self.kivy_instance.menu.items:
            if 'лог' in item['text']:
                log_id = i
            i += 1
        if self.kivy_instance.menu.items[log_id]['text'] == 'Показать лог':
            self.kivy_instance.menu.items[log_id]['text'] = 'Скрыть лог'
            self.kivy_instance.ids.log_scroll.scroll_y = 0
        else:
            self.kivy_instance.menu.items[log_id]['text'] = 'Показать лог'
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
            win.remove_widget(self._close_button)
            return True
        return False

    def display_settings(self, settings):
        win = self._app_window
        self._close_button = MDIconButton(pos=[dp(5), win.height - dp(53)], md_bg_color=self.theme_cls.accent_color, icon='arrow-left', on_release=self.close_settings)
        if not win:
            raise Exception('No windows are set on the application, you cannot'
                            ' open settings yet.')
        if settings not in win.children:
            win.add_widget(settings)
            win.add_widget(self._close_button)
            return True
        return False

    def menu_open(self, instance):
        self.kivy_instance.menu.caller = instance
        self.kivy_instance.menu.open()

    def open_main_settings(self):
        self.kivy_instance.menu.dismiss()
        self.open_settings()

    def copy(self, _str: str):
        Clipboard.copy(_str)


KivyApp = KivyApp()

# TODO Вывести статистику в каждом графике
# TODO Реализовать кнопки для управления стендом
# TODO Написать справку по программе
# TODO Реализовать экранирование скобок для вывода в виджетах (kivy.label documentation )
