import cmath
import math

from libs.utils import *
from libs.settings.settingsJSON import msettings


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
        out = self.client.GetValueFromName(self.name)
        if out != 'ERROR' and 'nf' not in out:
            out = str_to_variable(out)
            self.value = float(out)
            if not no_history:
                self.WriteHistory(float(out))
        else:
            self.value = 'ERROR'
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
        return FFTGraph(self.max_history_size, self.values_history)

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
        out = GetValueExpr(self.client, expression)
        if out != 'ERROR':
            out = str_to_variable(out)
            self.value = float(out)
            self.WriteHistory(float(out))
        return out

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

    sig = []
    if values:
        if hasattr(values[0], '__iter__') and len(values[0]) == 2:
            for i in range(len(values)):
                sig.append(values[i][1])
        else:
            sig = values

    avg = sum(sig) / len(sig)
    signal = [y - avg for y in sig]

    # amplitude = max(signal) - min(signal)

    length = len(signal)
    if len(signal) < SAMPLE_RATE:
        for i in range(SAMPLE_RATE - length):
            signal.append(0)

    FFT = transform(signal, False)
    FFT_abs = [abs(x) for x in FFT]
    _max = max(FFT_abs) or 1

    out = []
    for i in range(int(len(FFT) / 2) + 1):
        out.append((i/SAMPLE_RATE, 2 * FFT_abs[i] / SAMPLE_RATE))

    extremes = []
    for i in range(1, len(out) - 1):
        if out[i - 1][1] < out[i][1] > out[i + 1][1]:
            extremes.append(out[i])

    maxes = [(0., 0.) for i in range(top)]
    for extremum in extremes:
        num = 0
        for i in range(len(maxes)):
            if extremum[1] > maxes[i][1]:
                num += 1
        for j in range(top):
            if num == len(maxes) - j:
                maxes.insert(j, extremum)
                maxes = maxes[:top]
                break

    disp = 0

    for i in range(len(sig)):
        disp += ((sig[i] - avg)**2)/len(sig)

    sigma = math.sqrt(disp)

    return [out, maxes, avg, sigma]


#
# Computes the discrete Fourier transform (DFT) of the given complex vector, returning the result as a new vector.
# Set 'inverse' to True if computing the inverse transform. This DFT does not perform scaling, so the inverse is not a true inverse.
# The vector can have any length. This is a wrapper function.
#
def transform(vector, inverse=False):
    n = len(vector)
    if n > 0 and n & (n - 1) == 0:  # Is power of 2
        return transform_radix2(vector, inverse)
    else:  # More complicated algorithm for aribtrary sizes
        return transform_bluestein(vector, inverse)


#
# Computes the discrete Fourier transform (DFT) of the given complex vector, returning the result as a new vector.
# The vector's length must be a power of 2. Uses the Cooley-Tukey decimation-in-time radix-2 algorithm.
#
def transform_radix2(vector, inverse):
    # Initialization
    n = len(vector)
    levels = _log2(n)
    exptable = [cmath.exp((2j if inverse else -2j) * cmath.pi * i / n) for i in range(int(n / 2))]
    vector = [vector[_reverse(i, levels)] for i in range(n)]  # Copy with bit-reversed permutation

    # Radix-2 decimation-in-time FFT
    size = 2
    while size <= n:
        halfsize = int(size / 2)
        tablestep = int(n / size)
        for i in range(0, n, size):
            k = 0
            for j in range(i, i + halfsize):
                temp = vector[int(j + halfsize)] * exptable[k]
                vector[int(j + halfsize)] = vector[j] - temp
                vector[j] += temp
                k += tablestep
        size *= 2
    return vector


#
# Computes the discrete Fourier transform (DFT) of the given complex vector, returning the result as a new vector.
# The vector can have any length. This requires the convolution function, which in turn requires the radix-2 FFT function.
# Uses Bluestein's chirp z-transform algorithm.
#
def transform_bluestein(vector, inverse):
    # Find a power-of-2 convolution length m such that m >= n * 2 + 1
    n = len(vector)
    m = 1
    while m < n * 2 + 1:
        m *= 2

    exptable = [cmath.exp((1j if inverse else -1j) * cmath.pi * (i * i % (n * 2)) / n) for i in
                range(n)]  # Trigonometric table
    a = [x * y for (x, y) in zip(vector, exptable)] + [0] * (m - n)  # Temporary vectors and preprocessing
    b = [(exptable[min(i, m - i)].conjugate() if (i < n or m - i < n) else 0) for i in range(m)]
    c = convolve(a, b, False)[:n]  # Convolution
    for i in range(n):  # Postprocessing
        c[i] *= exptable[i]
    return c


#
# Computes the circular convolution of the given real or complex vectors, returning the result as a new vector. Each vector's length must be the same.
# realoutput=True: Extract the real part of the convolution, so that the output is a list of floats. This is useful if both inputs are real.
# realoutput=False: The output is always a list of complex numbers (even if both inputs are real).
#
def convolve(x, y, realoutput=True):
    assert len(x) == len(y)
    n = len(x)
    x = transform(x)
    y = transform(y)
    for i in range(n):
        x[i] *= y[i]
    x = transform(x, inverse=True)

    # Scaling (because this FFT implementation omits it) and postprocessing
    if realoutput:
        for i in range(n):
            x[i] = x[i].real / n
    else:
        for i in range(n):
            x[i] /= n
    return x


# Returns the integer whose value is the reverse of the lowest 'bits' bits of the integer 'x'.
def _reverse(x, bits):
    y = 0
    for i in range(bits):
        y = (y << 1) | (x & 1)
        x >>= 1
    return y


# Returns the integer y such that 2^y == x, or raises an exception if x is not a power of 2.
def _log2(x):
    i = 0
    while True:
        if 1 << i == x:
            return i
        elif 1 << i > x:
            raise ValueError("Not a power of 2")
        else:
            i += 1
