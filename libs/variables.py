import cmath
import math

import numpy as np
from numpy.fft import rfftfreq
from scipy.fft import rfft

from libs.utils import *
from libs.settings.settingsJSON import msettings

from timeit import default_timer as timer

class DirectVariable:
    def __init__(self, _client, _kivy, _max_history_size, _name, _id=0):
        self.id = _id
        self.name = _name
        self.kivy_instance = _kivy
        self.value = 0
        self.values_history = []
        self.spectral_values = []
        self.max_history_size = _max_history_size
        self.client = _client

    def GetValue(self, no_history=False):

        out = self.client.GetValueFromName(self.name) # 4ms

        if 'ERROR' in out:
            return out

        out = str_to_variable(out)
        self.value = float(out)
        if not no_history:

            self.WriteHistory(float(out)) # 0,002ms

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

    def GetSpectral(self, top):
        return FFTGraph(self.max_history_size, self.values_history, top)

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

        out = GetValueExpr(self.client, expression) # 0,00354ms

        if 'ERROR' in out:
            return out
        out = str_to_variable(out)
        self.value = float(out)

        self.WriteHistory(float(out)) # 2ms

        return self.value

    def WriteHistory(self, _value: float):
        if len(self.values_history) < self.max_history_size:
            self.values_history.append([len(self.values_history), _value])
        else:
            for i in range(len(self.values_history)):
                if i < (len(self.values_history) - 1):
                    self.values_history[i][1] = self.values_history[i + 1][1]
                    self.values_history[i][0] += 1
                else:
                    self.values_history[i][1] = _value
                    self.values_history[i][0] += 1

    def GetHistory(self):
        return self.values_history[-msettings.get('MAX_HISTORY_VALUES'):]

    def GetSpectral(self, top):
        return FFTGraph(self.max_history_size, self.values_history, top)

    def ClearHistory(self):
        self.values_history = []
        self.spectral_values = []

def FFTGraph(samplerate: int, values: list, top: int):

    SAMPLE_RATE = samplerate
    N = SAMPLE_RATE
    TIME_STEP = 1 / SAMPLE_RATE

    sig = []
    if values:
        if hasattr(values[0], '__iter__') and len(values[0]) == 2:
            for i in range(len(values)):
                sig.append(values[i][1])
        else:
            sig = values

    avg = sum(sig) / len(sig)
    signal = [y - avg for y in sig]

    yf = 2 * np.abs(rfft(signal, N)) / len(sig)
    xf = rfftfreq(N, d=TIME_STEP) / N

    out = []
    i = 0
    for x in xf:
        out.append((xf[i], yf[i]))
        i += 1

    extremes = []
    for i in range(1, len(out) - 1):
        if out[i - 1][1] < out[i][1] > out[i + 1][1]:
            extremes.append(out[i])

    maxes = [(0., 0.) for i in range(top)]
    for extreme in extremes:
        num = 0
        for i in range(len(maxes)):
            if extreme[1] > maxes[i][1]:
                num += 1
        for j in range(top):
            if num == len(maxes) - j:
                maxes.insert(j, extreme)
                maxes = maxes[:top]
                break

    disp = 0

    for i in range(len(sig)):
        disp += ((sig[i] - avg) ** 2) / len(sig)

    sigma = np.sqrt(disp)

    return [out, maxes, avg, sigma]