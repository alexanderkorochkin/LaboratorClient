import json
from kivy.metrics import sp


settings_defaults = {
            'NAMESPACE': "laboratory1",
            'LAST_IP': "opc.tcp://192.168.1.1:4840",
            'MAX_HISTORY_VALUES': 120,
            'MAX_RECONNECTIONS_NUMBER': 10,
            'RECONNECTION_TIME': 5,
            'GET_FROM_SERVER': True,
            'CONFIGURATION_PATH': "databaseconfig.txt",
            'LAYOUT_FILE': "layout.json",
            'KIVY_DOUBLETAP_TIME': 0.3,
            'KIVY_UPDATE_FUNCTION_TIME': 1,
            'USE_LAYOUT': True,
            'HIDE_LOG_BY_DEFAULT': True,
            'COL_HM': 2,
            'COL_HT': 4,
            'COL_HD': 4,
            'COL_VM': 1,
            'COL_VT': 3,
            'COL_VD': 4,
            'ROW_HM': 2,
            'ROW_HT': 4,
            'ROW_HD': 4,
            'ROW_VM': 3,
            'ROW_VT': 4,
            'ROW_VD': 5,
            'DIALOG_MINIMUM_HEIGHT_VERTICAL': sp(400),
            'DIALOG_MAXIMUM_HEIGHT_HORIZONTAL': sp(800),
            }


graph_settings_defaults = {
            'NAME': 'None',
            'MODE': 'NORMAL',

            'MAX_SPECTRAL_BUFFER_SIZE': 128,

            'GRAPH_ADDITIONAL_SPACE_Y': 1.2,
            'GRAPH_BUFFER_AVG_SIZE': 40,
            'GRAPH_ROUND_DIGITS': 1,

            'SHOW_MAIN_VALUE': True,
            'SHOW_AVG_VALUE': True,

            'SHOW_MAIN_GRAPH': True,
            'SHOW_AVG_GRAPH': True,
            'SHOW_INTIME_GRAPH': True,

            'MAIN_GRAPH_COLOR': '#ffb74d',
            'AVG_COLOR': '#FFFFFF',
            'INTIME_GRAPH_COLOR': '#FFFFFF',

            'MAIN_GRAPH_LINE_THICKNESS': 1.2,
            'AVG_GRAPH_LINE_THICKNESS': 1.2,
            'INTIME_GRAPH_LINE_THICKNESS': 1,

            'AVG_GRAPH_OPACITY': 0.8,

            'GRAPH_LABEL_X': False,
            'GRAPH_LABEL_Y': False,

            'HASH': '0',
            'IS_INDIRECT': False,
            'EXPRESSION': 'Empty'
            }

settings_json = json.dumps([

    {'type': 'title',
     'title': 'Настройки клиента'},

    {'type': 'string',
     'title': 'Область имен на сервере',
     'desc': 'NAMESPACE',
     'section': 'allSettings',
     'key': 'NAMESPACE'},

    {'type': 'string',
     'title': 'Последний IP',
     'desc': 'LAST_IP',
     'section': 'allSettings',
     'key': 'LAST_IP',
     'disabled': True},

    {'type': 'numeric',
     'title': 'Максимальное число переподключений',
     'desc': 'MAX_RECONNECTIONS_NUMBER',
     'section': 'allSettings',
     'key': 'MAX_RECONNECTIONS_NUMBER'},

    {'type': 'numeric',
     'title': 'Таймаут переподключения',
     'desc': 'RECONNECTION_TIME',
     'section': 'allSettings',
     'key': 'RECONNECTION_TIME'},

    {'type': 'bool',
     'title': 'Получать конфигурацию с сервера',
     'desc': 'GET_FROM_SERVER',
     'section': 'allSettings',
     'key': 'GET_FROM_SERVER'},

    {'type': 'path',
     'title': 'Путь к файлу конфигурации в локальном режиме',
     'desc': 'CONFIGURATION_PATH',
     'section': 'allSettings',
     'key': 'CONFIGURATION_PATH'},

    {'type': 'title',
     'title': 'Настройки интерфейса'},

    {'type': 'numeric',
     'title': 'Количество точек по оси X на графиках',
     'desc': 'MAX_HISTORY_VALUES',
     'section': 'allSettings',
     'key': 'MAX_HISTORY_VALUES'},

    {'type': 'numeric',
     'title': 'Сжатие графика по оси Y',
     'desc': 'GRAPH_ADDITIONAL_SPACE_Y',
     'section': 'GraphSettings',
     'key': 'GRAPH_ADDITIONAL_SPACE_Y'},

    {'type': 'numeric',
     'title': 'Количество значений для подсчета среднего',
     'desc': 'GRAPH_BUFFER_AVG_SIZE',
     'section': 'GraphSettings',
     'key': 'GRAPH_BUFFER_AVG_SIZE'},

    {'type': 'options',
     'title': 'Округление до N знаков после запятой',
     'desc': 'GRAPH_ROUND_DIGITS',
     'section': 'GraphSettings',
     'key': 'GRAPH_ROUND_DIGITS',
     'options': ['1', '2', '3']},

    {'type': 'numeric',
     'title': 'Толщина линии графика',
     'desc': 'MAIN_GRAPH_LINE_THICKNESS',
     'section': 'GraphSettings',
     'key': 'MAIN_GRAPH_LINE_THICKNESS'},

    {'type': 'bool',
     'title': 'Запоминать открытые графики',
     'desc': 'USE_LAYOUT',
     'section': 'allSettings',
     'key': 'USE_LAYOUT'},

    {'type': 'bool',
     'title': 'Скрывать лог при открытии',
     'desc': 'HIDE_LOG_BY_DEFAULT',
     'section': 'allSettings',
     'key': 'HIDE_LOG_BY_DEFAULT'},

    {'type': 'title',
     'title': 'Настройки сетки графиков'},

    {'type': 'options',
     'title': 'COLS for Horizontal:Mobile',
     'desc': 'COL_HM',
     'section': 'allSettings',
     'key': 'COL_HM',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Horizontal:Tablet',
     'desc': 'COL_HT',
     'section': 'allSettings',
     'key': 'COL_HT',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Horizontal:Desktop',
     'desc': 'COL_HD',
     'section': 'allSettings',
     'key': 'COL_HD',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Vertical:Mobile',
     'desc': 'COL_VM',
     'section': 'allSettings',
     'key': 'COL_VM',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Vertical:Tablet',
     'desc': 'COL_VT',
     'section': 'allSettings',
     'key': 'COL_VT',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'COLS for Vertical:Desktop',
     'desc': 'COL_VD',
     'section': 'allSettings',
     'key': 'COL_VD',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Horizontal:Mobile',
     'desc': 'ROW_HM',
     'section': 'allSettings',
     'key': 'ROW_HM',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Horizontal:Tablet',
     'desc': 'ROW_HT',
     'section': 'allSettings',
     'key': 'ROW_HT',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Horizontal:Desktop',
     'desc': 'ROW_HD',
     'section': 'allSettings',
     'key': 'ROW_HD',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Vertical:Mobile',
     'desc': 'ROW_VM',
     'section': 'allSettings',
     'key': 'ROW_VM',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Vertical:Tablet',
     'desc': 'ROW_VT',
     'section': 'allSettings',
     'key': 'ROW_VT',
     'options': ['1', '2', '3', '4', '5']},

    {'type': 'options',
     'title': 'ROWS for Vertical:Desktop',
     'desc': 'ROW_VD',
     'section': 'allSettings',
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

    def get(self, key, section='allSettings'):
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


ALL_SETTINGS = 'allSettings'
PADDING = sp(5)

msettings = MConf()
