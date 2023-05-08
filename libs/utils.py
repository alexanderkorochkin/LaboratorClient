import re
from re import split

import random   # Для поддержки рандомизации в выражениях
import math     # Для поддержки математических функций в выражениях

from kivy import Logger
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.properties import NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.utils import escape_markup
from iapws import IAPWS97

from libs.settings.settingsJSON import msettings


class DictCallback(dict):

    def __init__(self, d: dict, cls=None, callback=None, log=False):
        super(DictCallback, self).__init__(d)
        self.cls = cls
        self.callback = callback
        self.log = log

    def __setitem__(self, item, value):
        old_name = self['NAME']
        old_value = self[item]
        super(DictCallback, self).__setitem__(item, value)
        if self.cls and self.log:
            if old_value != value:
                Logger.debug(f'{self.cls.__class__.__name__}Dict: [{old_name}]: [{item}] changed to [{value}]')
            else:
                Logger.debug(f'{self.cls.__class__.__name__}Dict: [{old_name}]: [{item}] is still [{value}]')
        if self.callback:
            self.callback(item, value)


class HoldBehavior(ButtonBehavior):
    __events__ = ['on_hold']
    timeout = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._event = None
        self.always_release = True
        self.timeout = msettings.get('KIVY_HOLD_TIME')

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


Factory.register('HoldBehavior', cls=HoldBehavior)

K = 273.15                # Kelvin = °С + K
c = 299792458.0           # Скорость света, м/с
G = 299792458.0           # Гравитационная постоянная, м^3/кг*с^2
Patm = 101325.0           # Атмосферное давление при н.у., Па

IAPWS97_PARAMS = ['T', 'P', 'g', 'a', 'v', 'rho', 'h', 'u', 's', 'cp', 'cv', 'Z', 'fi', 'f', 'gamma', 'alfav', 'xkappa',
         'kappas', 'alfap', 'betap', 'joule', 'deltat', 'v0', 'u0', 'h0', 's0', 'a0', 'g0', 'cp0', 'cv0', 'w0',
         'gamma0', 'w', 'mu', 'nu', 'k', 'alfa', 'sigma', 'epsilon', 'n', 'Prandt', 'Pr', 'Tr', 'Hvap', 'Svap']


def GetValueExprRecursive(client, expression: str):
    # Находим все функции IAPWS в expression и заменяем их рекурсивно
    if (expression.count('{') == expression.count('}')) and expression.count('{') > 0:
        functions = []
        function = ''
        isOpened = False
        isFirst = True
        count = 0
        for ch in expression:
            if ch == '{':
                isOpened = True
                count += 1
            if ch == '}':
                count -= 1
                if count == 0:
                    isOpened = False
                    functions.append(function)
                    function = ''
                    isFirst = True
            if isOpened:
                if isFirst:
                    isFirst = False
                else:
                    function += ch

        for function in functions:
            expression = expression.replace('{' + f'{function}' + '}', GetValueExprRecursive(client, function), 1)

    # После замены всех вложенных IAPWS-функций получаем чистую IAPWS-функцию с числовыми параметрами, вычисляем
    if expression.split(',')[0] in IAPWS97_PARAMS:
        params = expression.split(',')
        f = params[0]
        params = params[1:]

        kwargs = {"T": 0.0,
                  "P": 0.0,
                  "x": None,
                  "h": None,
                  "s": None,
                  "v": 0.0,
                  "l": 0.5893}
        for param in params:
            param_name, param_value = param.split('=')
            param_value = float(eval(param_value))
            if param_name in list(kwargs.keys()):
                kwargs[param_name] = param_value

        substance = IAPWS97()
        substance.kwargs = IAPWS97.kwargs.copy()
        substance.kwargs.update(kwargs)
        if substance.calculable:
            substance.status = 1
            try:
                substance.calculo()
                substance.msg = "Solved"
                expression = str(getattr(substance, str(f)))
            except Exception:
                return f'ERROR: Unable to evaluate the expression: {expression} with IAPWS97!'

    # Пытаемся вычислить численное выражение
    try:
        return str(eval(expression))
    except Exception:
        return f'ERROR: Cannot evaluate expression: {expression}!'


def GetValueExpr(client, expression):
    expression = expression.replace('  ', ' ')
    expression = expression.replace(' ', '')
    if expression.count('[') == expression.count(']'):
        if expression.count('[') >= 0 and len(expression) != 0:
            isWork = True
            isFirst = True
            while isWork:
                result = re.search(r'\[([^\]]*)\]', expression)
                if result:
                    name = str(result.group(0))[1:-1]
                    value = client.GetValueFromName(name)
                    if 'ERROR' in value:
                        return value
                    expression = expression.replace(f'[{name}]', str(value))
                    isFirst = False
                else:
                    isWork = False
                    if isFirst:
                        try:
                            return str(eval(expression))
                        except Exception:
                            pass
        else:
            return f'ERROR: Expression {expression} is empty!'
    else:
        return f"ERROR: Expression '{expression}' contains a different number of opening and closing []-brackets!"

    return GetValueExprRecursive(client, expression)


def round_to(num, digits=2):
    if num == 0: return 0
    scale = int(-math.floor(math.log10(abs(num - int(num))))) + digits - 1
    if scale < digits: scale = digits
    return round(num, scale)


def color2hex(color):
    return '#' + ''.join(['{0:02x}'.format(int(x * 255)) for x in color])


def hex2color(s, opacity=-1.0):

    if s.startswith('#'):
        return hex2color(s[1:], opacity)

    value = [int(x, 16) / 255.
             for x in split('([0-9a-f]{2})', s.lower()) if x != '']
    if opacity > 0:
        if len(value) == 3:
            value.append(opacity)
        if len(value) == 4:
            value[3] = opacity
    else:
        if len(value) == 3:
            value.append(1.0)
    return value


def str_to_variable(_str: str):
    if _str in ['True', 'False', 'true', 'false']:
        try:
            return _str.lower() == 'true'
        except Exception:
            Logger.debug(f'Utils.str_to_value: Can\'t covert string: {_str} to boolean as excepted!')
    elif '.' in _str:
        try:
            return float(_str)
        except Exception:
            Logger.debug(f'Utils.str_to_value: Can\'t covert string: {_str} to float as excepted!')
    else:
        try:
            return int(_str)
        except Exception:
            Logger.debug(f'Utils: str_to_value: Can\'t covert string: {_str} to int as excepted!')
    Logger.debug(f'Utils.str_to_value: Can\'t detect string: {_str} as int, float or bool!')
    return 0


def truncate_string(string, N, screen_brackets=False):
    out = string
    if len(string) > N:
        substring = string[0: N]
        last_alpha = 0
        for i in range(N - 1, 0, -1):
            if string[i - 1].isalpha() and not string[i].isalpha():
                last_alpha = i
                break
        out = substring[0: last_alpha] + "…"

    if screen_brackets:
        out = out.replace('[', escape_markup('['))
        out = out.replace(']', escape_markup(']'))

    return out


def animated_hide_widget_only(wid, method):
    anim = Animation(opacity=0, duration=0.2, t='in_quart')
    anim.bind(on_complete=method)
    anim.start(wid)


def animated_show_widget_only(wid, method):
    anim = Animation(opacity=1,  duration=0.2, t='out_quart')
    anim.bind(on_start=method)
    anim.start(wid)


def animate_graph_removal(wid, side, method):
    # animate shrinking widget width
    if side == 'vertical':
        wid.size_hint = wid.size_hint[0], None
        anim = Animation(opacity=0, size=(wid.size[0], 0), duration=0.5, t='out_expo')
    elif side == 'horizontal':
        anim = Animation(opacity=0, duration=0.5, t='out_expo')
    anim.bind(on_complete=method)
    t = wid.gardenGraph._trigger
    ts = wid.gardenGraph._trigger_size
    wid.gardenGraph.unbind(center=ts, padding=ts, x_precision=ts, y_precision=ts, plots=ts, x_grid=ts,
                           y_grid=ts, draw_border=ts)
    wid.gardenGraph.unbind(xmin=t, xmax=t, xlog=t, x_ticks_major=t, x_ticks_minor=t,
                           xlabel=t, x_grid_label=t, ymin=t, ymax=t, ylog=t,
                           y_ticks_major=t, y_ticks_minor=t, ylabel=t, y_grid_label=t,
                           font_size=t, label_options=t, x_ticks_angle=t)
    anim.start(wid)
