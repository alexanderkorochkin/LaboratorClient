import math

from scipy.fft import rfft, rfftfreq

from libs.settings.settingsJSON import msettings
from kivy.logger import Logger
import numexpr as ne
import re

import numpy as np


class LabVar:
    def __init__(self, name, browse_name='', node_id=''):
        self.name = name
        self.browse_name = browse_name
        self.node_id = node_id

    def GetName(self):
        return self.name


class DirectVariable:
    def __init__(self, _client, _kivy, _max_history_size, _name, _id=0):
        self.id = _id
        self.name = _name
        self.kivy_instance = _kivy
        self.value = 0
        self.values_history = []
        self.spectral_values = []
        self.max_history_size = _max_history_size
        self.N = 2 ** math.ceil(math.log2(self.max_history_size))
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
        if len(self.values_history) < self.max_history_size:
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
        return self.values_history[-msettings.get('MAX_HISTORY_VALUES'):]

    def GetSpectral(self):

        SAMPLE_RATE = self.max_history_size                         # Количество точек в сэмпле, Гц
        DURATION = 1                                                # Длительность сэмпла, сек
        N = SAMPLE_RATE * DURATION                                  # Количество сэмплов всего
        TIME_STEP = 1 / SAMPLE_RATE

        sig = []
        for i in range(len(self.values_history)):
            sig.append(self.values_history[i][1])

        avg = sum(sig) / len(sig)                                   # Среднее значение
        sig = [y - avg for y in sig]                                # Выравнивание по оси Y

        signal = np.array(sig, dtype=float)

        yf = rfft(sig, N)
        xf = rfftfreq(N, d=TIME_STEP) / N

        out = []
        i = 0
        for x in xf:
            out.append((xf[i], np.abs(yf[i])))
            i += 1

        print(xf[np.argmax(np.abs(yf))], np.max(np.abs(yf)))

        return out

    def ClearHistory(self):
        self.values_history = []
        self.spectral_values = []


class IndirectVariable:
    def __init__(self, _client, _kivy, _max_history_size):
        self.value = 0
        self.values_history = []
        self.spectral_values = []
        self.max_history_size = _max_history_size
        self.client = _client
        self.kivy_instance = _kivy

    def GetValue(self, expression):
        if expression.count('[') == expression.count(']'):
            if expression.count('[') == 0 and len(expression) != 0:
                try:
                    self.value = float(ne.evaluate(expression))
                    self.WriteHistory(self.value)
                    return self.value
                except Exception:
                    Logger.debug(f"GetValue: Cannot evaluate expression without args: {expression}!")
                    return expression
            elif expression.count('[') > 0 and len(expression) != 0:

                isWork = True
                while isWork:
                    result = re.search(r'\[([^\]]*)\]', expression)
                    if result:
                        name = str(result.group(0))[1:-1]
                        labvar = self.kivy_instance.GetLabVarByName(name)
                        if labvar is not None:
                            expression = expression.replace(f'[{name}]',
                                                            str(self.client.get_node(labvar.node_id).get_value()))
                        else:
                            return name
                    else:
                        isWork = False

                try:
                    self.value = float(ne.evaluate(expression))
                    self.WriteHistory(self.value)
                    return self.value
                except Exception:
                    Logger.debug(f"GetValue: Cannot evaluate expression with args: {expression}!")
                    return expression
            else:
                Logger.debug(f"GetValue: Expression is empty!")
                return expression
        else:
            Logger.debug(
                f"GetValue: Expression '{expression}' contains a different number of opening and closing brackets!")
            return expression

    def WriteHistory(self, _value):
        if len(self.values_history) < self.max_history_size:
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
        return self.values_history[-msettings.get('MAX_HISTORY_VALUES'):]

    def GetSpectral(self):

        SAMPLE_RATE = self.max_history_size                         # Количество точек в сэмпле, Гц
        DURATION = 1                                                # Длительность сэмпла, сек
        N = SAMPLE_RATE * DURATION                                  # Количество сэмплов всего
        TIME_STEP = 1 / SAMPLE_RATE

        sig = []
        for i in range(len(self.values_history)):
            sig.append(self.values_history[i][1])

        avg = sum(sig) / len(sig)                                   # Среднее значение
        sig = [y - avg for y in sig]                                # Выравнивание по оси Y

        signal = np.array(sig, dtype=float)

        yf = rfft(sig, N)
        xf = rfftfreq(N, d=TIME_STEP) / N

        out = []
        i = 0
        for x in xf:
            out.append((xf[i], np.abs(yf[i])))
            i += 1

        print(xf[np.argmax(np.abs(yf))], np.max(np.abs(yf)))

        return out

    def ClearHistory(self):
        self.values_history = []
        self.spectral_values = []
