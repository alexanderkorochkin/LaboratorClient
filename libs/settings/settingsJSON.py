import json
import os
from kivy.metrics import sp


settings_defaults = {
            'NAMESPACE': "laboratory1",
            'LAST_IP': "opc.tcp://192.168.1.1:4840",
            'MAX_HISTORY_VALUES': 120,
            'MAX_RECONNECTIONS_NUMBER': 10,
            'RECONNECTION_TIME': 5,
            'GET_FROM_SERVER': True,
            'CONFIGURATION_PATH': os.path.join("settings", "databaseconfig.txt"),
            'KIVY_DOUBLETAP_TIME': 0.3,
            'KIVY_UPDATE_FUNCTION_TIME': 1,
            'GRAPH_ADDITIONAL_SPACE_Y': 1.5,
            'GRAPH_BUFFER_AVG_SIZE': 20,
            'GRAPH_ROUND_DIGITS': '1',
            'GRAPH_LINE_THICKNESS': 1.3,
            'USE_LAYOUT': True
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
     'title': 'Скорость двойного нажатия',
     'desc': 'KIVY_DOUBLETAP_TIME',
     'section': 'allSettings',
     'key': 'KIVY_DOUBLETAP_TIME'},

    {'type': 'numeric',
     'title': 'Количество точек по оси X на графиках (зависит от частоты обновления)',
     'desc': 'MAX_HISTORY_VALUES',
     'section': 'allSettings',
     'key': 'MAX_HISTORY_VALUES'},

    {'type': 'numeric',
     'title': 'Скорость обновления графики',
     'desc': 'KIVY_UPDATE_FUNCTION_TIME',
     'section': 'allSettings',
     'key': 'KIVY_UPDATE_FUNCTION_TIME'},

    {'type': 'numeric',
     'title': 'Сжатие графика по оси Y',
     'desc': 'GRAPH_ADDITIONAL_SPACE_Y',
     'section': 'allSettings',
     'key': 'GRAPH_ADDITIONAL_SPACE_Y'},

    {'type': 'numeric',
     'title': 'Количество значений для подсчета среднего',
     'desc': 'GRAPH_BUFFER_AVG_SIZE',
     'section': 'allSettings',
     'key': 'GRAPH_BUFFER_AVG_SIZE'},

    {'type': 'options',
     'title': 'Количество символов после запятой',
     'desc': 'GRAPH_ROUND_DIGITS',
     'section': 'allSettings',
     'key': 'GRAPH_ROUND_DIGITS',
     'options': ['1', '2', '3']},

    {'type': 'numeric',
     'title': 'Толщина линии графика',
     'desc': 'GRAPH_LINE_THICKNESS',
     'section': 'allSettings',
     'key': 'GRAPH_LINE_THICKNESS'},

    {'type': 'bool',
     'title': 'Запоминать открытые графики',
     'desc': 'USE_LAYOUT',
     'section': 'allSettings',
     'key': 'USE_LAYOUT'},

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
PADDING = sp(15)

msettings = MConf()
