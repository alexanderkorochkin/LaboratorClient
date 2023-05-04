import json
from kivy.metrics import sp, dp

settings_defaults = {
            'LAST_IP': "opc.tcp://192.168.1.1:4840",
            'MAX_HISTORY_VALUES': 120,
            'MAX_RECONNECTIONS_NUMBER': 10,
            'RECONNECTION_TIME': 5,
            'GRAPHS_LAYOUT_FILE': "graphs_layout.json",
            'CONTROLS_LAYOUT_FILE': "controls_layout.json",
            'KIVY_HOLD_TIME': 0.2,
            'KIVY_UPDATE_FUNCTION_TIME': 1,
            'SAVE_TIMEOUT_TIME': 5,
            'USE_LAYOUT': True,
            'HIDE_LOG_BY_DEFAULT': True,
            'SHOW_CONTROLS_BY_DEFAULT': True,
            'THEME': 'Light',
            'COL_HM': 2,
            'COL_HT': 2,
            'COL_HD': 4,
            'COL_VM': 1,
            'COL_VT': 2,
            'COL_VD': 4,
            'ROW_HM': 2,
            'ROW_HT': 4,
            'ROW_HD': 4,
            'ROW_VM': 3,
            'ROW_VT': 4,
            'ROW_VD': 5,
            'DIALOG_MINIMUM_HEIGHT_VERTICAL': dp(400),
            'DIALOG_MAXIMUM_HEIGHT_HORIZONTAL': dp(800),
            }


controls_settings_defaults = {
            'VARIABLE': 'None',
            'NAME': 'None',
            'MODE': 'TOGGLE',           # SWITCH (on_release action True/False) or HOLD (on_press - True, on_release - False)
            'DEFAULT_STATE': False,
            'ICON_ON': 'electric-switch-closed',
            'ICON_OFF': 'electric-switch',
            'HASH': '0',
}


graph_settings_defaults = {
            'NAME': 'None',
            'MODE': 'NORMAL',

            'MAX_SPECTRAL_BUFFER_SIZE': 128,

            'GRAPH_ADDITIONAL_SPACE_Y': 1.2,
            'GRAPH_BUFFER_AVG_SIZE': 40,
            'GRAPH_ROUND_DIGITS': 3,

            'SHOW_MAIN_VALUE': True,
            'SHOW_AVG_VALUE': True,

            'SHOW_MAIN_GRAPH': True,
            'SHOW_AVG_GRAPH': True,
            'SHOW_INTIME_GRAPH': True,

            'MAIN_GRAPH_COLOR': '#ffb74d',
            'AVG_COLOR': '#FFFFFF',
            'INTIME_GRAPH_COLOR': '#FFFFFF',

            'MAIN_GRAPH_LINE_THICKNESS': dp(1),
            'AVG_GRAPH_LINE_THICKNESS': dp(1),
            'INTIME_GRAPH_LINE_THICKNESS': dp(1),

            'AVG_GRAPH_OPACITY': 0.8,

            'GRAPH_LABEL_X': False,
            'GRAPH_LABEL_Y': True,

            'HASH': '0',
            'IS_INDIRECT': False,
            'EXPRESSION': 'Empty'
            }

settings_json = json.dumps([

    {'type': 'title',
     'title': 'Настройки клиента'},

    {'type': 'string',
     'title': 'Последний IP',
     'desc': 'LAST_IP',
     'section': 'MainSettings',
     'key': 'LAST_IP',
     'disabled': True},

    {'type': 'numeric',
     'title': 'Максимальное число переподключений',
     'desc': 'MAX_RECONNECTIONS_NUMBER',
     'section': 'MainSettings',
     'key': 'MAX_RECONNECTIONS_NUMBER'},

    {'type': 'numeric',
     'title': 'Таймаут переподключения',
     'desc': 'RECONNECTION_TIME',
     'section': 'MainSettings',
     'key': 'RECONNECTION_TIME'},

    {'type': 'title',
     'title': 'Настройки интерфейса'},

    {'type': 'options',
     'title': 'Тема клиента',
     'desc': 'Выберите между светлой или темной',
     'section': 'MainSettings',
     'key': 'THEME',
     'options': ['Dark', 'Light']},

    {'type': 'numeric',
     'title': 'Количество точек по оси X на графиках (+ число точек для подсчета среднего)',
     'desc': 'MAX_HISTORY_VALUES',
     'section': 'MainSettings',
     'key': 'MAX_HISTORY_VALUES'},

    {'type': 'numeric',
     'title': 'Количество значений для подсчета среднего',
     'desc': 'GRAPH_BUFFER_AVG_SIZE',
     'section': 'GraphSettings',
     'key': 'GRAPH_BUFFER_AVG_SIZE'},

    {'type': 'numeric',
     'title': 'Толщина линии графика',
     'desc': 'MAIN_GRAPH_LINE_THICKNESS',
     'section': 'GraphSettings',
     'key': 'MAIN_GRAPH_LINE_THICKNESS'},

    {'type': 'bool',
     'title': 'Запоминать открытые графики и кнопки',
     'desc': 'USE_LAYOUT',
     'section': 'MainSettings',
     'key': 'USE_LAYOUT'},

    {'type': 'bool',
     'title': 'Скрывать лог при открытии',
     'desc': 'HIDE_LOG_BY_DEFAULT',
     'section': 'MainSettings',
     'key': 'HIDE_LOG_BY_DEFAULT'},

    {'type': 'title',
     'title': 'Настройки сетки графиков'},

    {'type': 'options',
     'title': 'COLS for Horizontal:Mobile',
     'desc': 'COL_HM',
     'section': 'MainSettings',
     'key': 'COL_HM',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Horizontal:Tablet',
     'desc': 'COL_HT',
     'section': 'MainSettings',
     'key': 'COL_HT',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Horizontal:Desktop',
     'desc': 'COL_HD',
     'section': 'MainSettings',
     'key': 'COL_HD',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Vertical:Mobile',
     'desc': 'COL_VM',
     'section': 'MainSettings',
     'key': 'COL_VM',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Vertical:Tablet',
     'desc': 'COL_VT',
     'section': 'MainSettings',
     'key': 'COL_VT',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Vertical:Desktop',
     'desc': 'COL_VD',
     'section': 'MainSettings',
     'key': 'COL_VD',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Horizontal:Mobile',
     'desc': 'ROW_HM',
     'section': 'MainSettings',
     'key': 'ROW_HM',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Horizontal:Tablet',
     'desc': 'ROW_HT',
     'section': 'MainSettings',
     'key': 'ROW_HT',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Horizontal:Desktop',
     'desc': 'ROW_HD',
     'section': 'MainSettings',
     'key': 'ROW_HD',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Vertical:Mobile',
     'desc': 'ROW_VM',
     'section': 'MainSettings',
     'key': 'ROW_VM',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Vertical:Tablet',
     'desc': 'ROW_VT',
     'section': 'MainSettings',
     'key': 'ROW_VT',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Vertical:Desktop',
     'desc': 'ROW_VD',
     'section': 'MainSettings',
     'key': 'ROW_VD',
     'options': ['1', '2', '3', '4', '5']},

])


class MConf:
    instance = None

    @staticmethod
    def isFloatOrNumber(num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    def get(self, key, section='MainSettings'):
        if self.isFloatOrNumber(self.instance.get(section, key)):
            if self.instance.get(section, key).find('.') != -1:
                return float(self.instance.get(section, key))
            else:
                return int(self.instance.get(section, key))
        else:
            return self.instance.get(section, key)

    def set(self, section, key, value):
        self.instance.set(section, key, value)
        self.instance.write()


PADDING = dp(5)

msettings = MConf()
