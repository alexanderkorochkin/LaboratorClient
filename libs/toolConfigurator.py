from libs.settings.settingsJSON import msettings
from kivy.logger import Logger, LOG_LEVELS, LoggerHistory
import numexpr as ne
import re


class LabVar:
    def __init__(self, name, browse_name='', node_id=''):
        self.name = name
        self.browse_name = browse_name
        self.node_id = node_id

    def GetName(self):
        return self.name


class ServerVariable:
    def __init__(self, _client, _kivy, _name, _id=0):
        self.id = _id
        self.name = _name
        self.kivy_instance = _kivy
        self.value = 0
        self.values_history = []
        self.client = _client

    def SetName(self, _name):
        self.name = _name
        self.ClearHistory()
        self.value = 0

    def GetValue(self, no_history=False):
        self.value = self.client.get_node(self.kivy_instance.GetLabVarByName(self.name).node_id).get_value()
        if not no_history:
            self.WriteHistory(self.value)
        return self.value

    def WriteHistory(self, _value):
        if len(self.values_history) < msettings.get('MAX_HISTORY_VALUES'):
            self.values_history.append([len(self.values_history), _value])
        else:
            for i in range(len(self.values_history)):
                if i < (len(self.values_history) - 1):
                    self.values_history[i][1] = self.values_history[i + 1][1]
                    self.values_history[i][0] += 1
                else:
                    self.values_history[i][1] = float(_value)
                    self.values_history[i][0] += 1

    def GetHistory(self):
        return self.values_history

    def ClearHistory(self):
        self.values_history = []


class IndirectVariable:
    def __init__(self, _client, _kivy):
        self.value = 0
        self.values_history = []
        self.client = _client
        self.kivy_instance = _kivy

    def GetValue(self, expr):
        number1 = expr.count('[')
        number2 = expr.count(']')
        expression = expr
        number = -1
        mode = "NormalMode"

        if number1 == number2:
            number = number1
            if number == 0 and len(expression) != 0:
                try:
                    self.value = float(ne.evaluate(expression))
                    self.WriteHistory(self.value)
                except Exception:
                    Logger.debug(f"GetValue: Expression: '{expression}' are invalid!")
            if number > 0 and len(expression) != 0:
                isWork = True
                isError = False
                while isWork:
                    result = re.search(r'\[([^\]]*)\]', expression)
                    if result:
                        name = str(result.group(0))[1:-1]
                        labvar = self.kivy_instance.GetLabVarByName(name)
                        if labvar is not None:
                            expression = expression.replace(f'[{name}]', str(self.client.get_node(labvar.node_id).get_value()))
                        else:
                            return name
                    else:
                        isWork = False
                try:
                    self.value = float(ne.evaluate(expression))
                    self.WriteHistory(self.value)
                except Exception:
                    Logger.debug(f"GetValue: Expression: '{expression}' are invalid!")

        return self.value

    def WriteHistory(self, _value):
        if len(self.values_history) < msettings.get('MAX_HISTORY_VALUES'):
            self.values_history.append([len(self.values_history), _value])
        else:
            for i in range(len(self.values_history)):
                if i < (len(self.values_history) - 1):
                    self.values_history[i][1] = self.values_history[i + 1][1]
                    self.values_history[i][0] += 1
                else:
                    self.values_history[i][1] = float(_value)
                    self.values_history[i][0] += 1

    def GetHistory(self):
        return self.values_history

    def ClearHistory(self):
        self.values_history = []
