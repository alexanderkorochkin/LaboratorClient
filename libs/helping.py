# [ref=https://vk.com/im][color=548cb9]ВК[/color][/ref]

main_help_text = 'Привет'
add_multiple_graphs_text = ''
menu_text = ''
endpoint_text = ''
graph_settings_text = """
Плитки графиков (далее - плитки) являются независимыми виджетами, обладающими индивидуальными настройками.

Плитки обладают [b]двумя[/b] режимами работы. В режиме [b][color=d49a44]NORMAL[/color][/b] плитка показывает график от времени, в режиме [b][color=d49a44]SPECTRAL[/color][/b] - спектр плотности мощности выбранной переменной.

Помимо этого, плитка может обрабатывать один из двух типов переменных - [b][color=d49a44]серверные[/color][/b] и [b][color=d49a44]пользовательские[/color][/b]. Если первые получают свое значение напрямую с сервера и не могут быть переименованы, то вторые получают значение согласно заданному [i][b]выражению[/b][/i], и могут быть переименованы.

Далее описано назначение всех пунктов меню настроек:

[color=549f70]* Переменная[/color] - позволяет выбрать из списка серверную переменную (только при наличии соединения с сервером) или создать пользовательскую переменную с выражением. Справа от этой кнопки расположена иконка, по нажатии которой можно скопировать название серверной переменной или переименовать пользовательскую.

[color=549f70]* Выражение[/color] - позволяет задать выражение для пользовательской переменной согласно принятому синтаксису (см. справку в окне ввода выражения). [color=706e60]Стоит заметить, что при некорректном вводе плитка будет показывать[/color] [color=ff1313]ERROR[/color] [color=706e60]вместо числового значения, то же будет происходить при наличии аргументов, выходящих за пределы области определения использующихся функций (в том числе библиотеки IAPWS).[/color]

[color=549f70]* Текущий режим[/color] - переключатель режима работы плитки (NORMAL/SPECTRAL).

[color=549f70]* Показывать значение среднего[/color] - когда активно, отображает в углу плитки среднее значение за последние N отсчетов.

[color=549f70]* График среднего значения[/color] - когда активно, отображает график среднего значения переменной (белый).

[color=549f70]* Основной график[/color] - когда активно, отображает основной график переменной (оранжевый).

[color=549f70]* Линия текущего значения[/color] - когда активно, отображает горизонтальную линию текущего значения переменной (серый).

[color=549f70]* Целевое значение[/color] - когда активно, позволяет выбрать целевое значение. При наличии целевого значения строится соответствующая статичная горизонтальная линия на графике (зеленым), а текущее значение в углу плитки сравнивается с целевым.

[color=549f70]* Отсчетов для среднего[/color] - позволяет задать количество отсчетов, которые будут браться для расчета среднего и построения графика среднего значения.

[color=549f70]* Знаков после запятой[/color] - параметр, задающий число знаков после запятой для чисел, отображаемых на графике.

[color=549f70]* Размер спектрального буфера[/color] - параметр, задающий число отсчетов для вычисления [i]Быстрого Преобразования Фурье[/i] (рекомендуется указывать число кратное степени двойки).

[color=549f70]* Вкл./Откл. ось X/Y[/color] - показывает/скрывает ось X/Y у графика.

[color=549f70]* Очистить график[/color] - очищает все буферы и обновляет график так, что он начинает заполняться с начала. При изменении некоторых настроек это происходит автоматически.

[color=549f70]* Удалить плитку[/color] - удаляет плитку из видового экрана (при этом пользовательская переменная плитки не сохраняется).

Все изменения в настройках плиток сохраняются автоматически через несколько секунд после внесения изменений и хранятся в файле [color=d49a44][graphs_layout.json][/color].

"""
graph_new_indirect_variable_naming_text = ''
graph_variable_choosing_text = ''
graph_rename_variable_text = ''
graph_expression_text = """
[i][color=d49a44]Выражения[/color][/i] позволяют в режиме реального времени производить вычисления, опираясь на текущие значения переменных. Присутствует поддержка базовых математических операций и других операций, поддерживаемых модулями math, random, time для Python.

[size=16sp][b][color=d49a44]1. Серверные переменные:[/color][/b][/size]
Серверная переменная - это переменная [i]Laborator Client[/i], которая получает свое значение напрямую из аналогичной по названию переменной на сервере.
Для использования серверной переменной в выражении необходимо заключить её название в квадратных скобках, например: [color=549f70][txc][/color]. При расчете выражения будет подставлено численное значение этой переменной.

[size=16sp][b][color=d49a44]2. Константы:[/color][/b][/size]
Выражения поддерживают следующие константы:
[color=d49a44]K = 273.15[/color] [color=706e60]- kelvin = °С + K[/color]
[color=d49a44]c = 299792458.0[/color] [color=706e60]- скорость света, м/с[/color]
[color=d49a44]G = 299792458.0[/color] [color=706e60]- гравитационная постоянная, м^3/кг*с^2[/color]
[color=d49a44]Patm = 0.101325[/color] [color=706e60]- атмосферное давление при н.у., МПа[/color]
Константы указываются без скобок, как есть, например: [txc] + [color=549f70]K[/color].

[size=16sp][b][color=d49a44]3. Возможности модуля IAPWS в выражениях:[/color][/b][/size]
В программу встроена [i]библиотека IAPWS[/i], которая позволяет производить расчет параметров пара и воды в режиме реального времени.
Далее приведены допустимые параметры, рассчитываемые модулем:

* P: [i]Pressure[/i], [MPa]
* T: [i]Temperature[/i], [K]
* g: [i]Specific Gibbs free energy[/i], [kJ/kg]
* a: [i]Specific Helmholtz free energy[/i], [kJ/kg]
* v: [i]Specific volume[/i], [m³/kg]
* rho: [i]Density[/i], [kg/m³]
* h: [i]Specific enthalpy[/i], [kJ/kg]
* u: [i]Specific internal energy[/i], [kJ/kg]
* s: [i]Specific entropy[/i], [kJ/kg·K]
* cp: [i]Specific isobaric heat capacity[/i], [kJ/kg·K]
* cv: [i]Specific isochoric heat capacity[/i], [kJ/kg·K]
* Z: [i]Compression factor[/i], [-]
* fi: [i]Fugacity coefficient[/i], [-]
* f: [i]Fugacity[/i], [MPa]

* gamma: [i]Isoentropic exponent[/i], [-]
* alfav: [i]Isobaric cubic expansion coefficient[/i], [1/K]
* xkappa: [i]Isothermal compressibility[/i], [1/MPa]
* kappas: [i]Adiabatic compresibility[/i], [1/MPa]
* alfap: [i]Relative pressure coefficient[/i], [1/K]
* betap: [i]Isothermal stress coefficient[/i], [kg/m³]
* joule: [i]Joule-Thomson coefficient[/i], [K/MPa]
* deltat: [i]Isothermal throttling coefficient[/i], [kJ/kg·MPa]
* region: [i]Region[/i]

* v0: [i]Ideal specific volume[/i], [m³/kg]
* u0: [i]Ideal specific internal energy[/i], [kJ/kg]
* h0: [i]Ideal specific enthalpy[/i], [kJ/kg]
* s0: [i]Ideal specific entropy[/i], [kJ/kg·K]
* a0: [i]Ideal specific Helmholtz free energy[/i], [kJ/kg]
* g0: [i]Ideal specific Gibbs free energy[/i], [kJ/kg]
* cp0: [i]Ideal specific isobaric heat capacity[/i], [kJ/kg·K]
* cv0: [i]Ideal specific isochoric heat capacity[/i], [kJ/kg·K]
* w0: [i]Ideal speed of sound[/i], [m/s]
* gamma0: [i]Ideal isoentropic exponent[/i], [-]

* w: [i]Speed of sound[/i], [m/s]
* mu: [i]Dynamic viscosity[/i], [Pa·s]
* nu: [i]Kinematic viscosity[/i], [m²/s]
* k: [i]Thermal conductivity[/i], [W/m·K]
* alfa: [i]Thermal diffusivity[/i], [m²/s]
* sigma: [i]Surface tension[/i], [N/m]
* epsilon: [i]Dielectric constant[/i], [-]
* n: [i]Refractive index[/i], [-]
* Prandt: [i]Prandtl number[/i], [-]
* Pr: [i]Reduced Pressure[/i], [-]
* Tr: [i]Reduced Temperature[/i], [-]
* Hvap: [i]Vaporization heat[/i], [kJ/kg]
* Svap: [i]Vaporization entropy[/i], [kJ/kg·K]

Для получения требуемого параметра необходимо в фигурных скобках указать его первым, а далее через запятую привести значения параметров-аргументов. При этом допускается использовать константы или серверные переменные, см. примеры ниже.
Подробнее см. [ref=https://iapws.readthedocs.io/en/latest/modules.html#documentation][color=548cb9]документацию библиотеки IAPWS97 для Python[/color][/ref].

[color=d49a44]Примеры[/color]
[color=549f70]{h, T = [txc] + K, P = 0.0006112127}[/color]

[color=549f70]{cp, T = 170 + K, x = 0.5, phase = ‘Liquid’}[/color] [i]# Output: 4.3695[/i]
[color=549f70]{cp, T = 170 + K, x = 0.5, phase = ‘Vapor’}[/color] [i]# Output: 2.5985[/i]
[color=549f70]{w, T = 170 + K, x = 0.5, phase = ‘Liquid’}[/color] [i]# Output: 1418.3[/i]
[color=549f70]{w, T = 170 + K, x = 0.5, phase = ‘Vapor’}[/color] [i]# Output: 498.78[/i]

[color=549f70]{P, T = 325 + K, x = 0.5}[/color] # Output: 12.0505
[color=549f70]{v, T = 325 + K, x = 0.5, phase = ‘Liquid’}[/color] [i]# Output: 0.00152830[/i]
[color=549f70]{v, T = 325 + K, x = 0.5, phase = ‘Vapor’}[/color] [i]# Output: 0.0141887[/i]
[color=549f70]{h, T = 325 + K, x = 0.5, phase = ‘Liquid’}[/color] [i]# Output: 1493.37[/i]
[color=549f70]{h, T = 325 + K, x = 0.5, phase = ‘Vapor’}[/color] [i]# Output: 2684.48[/i]

[color=549f70]{cp0, T = 50 + K, P = 0.0006112127}[/color] [i]# Output: 1.8714[/i]
[color=549f70]{cv0, T = 50 + K, P = 0.0006112127}[/color] [i]# Output: 1.4098[/i]
[color=549f70]{h0, T = 50 + K, P = 0.0006112127}[/color] [i]# Output: 2594.66[/i]
[color=549f70]{s0, T = 50 + K, P = 0.0006112127}[/color] [i]# Output: 9.471[/i]
[color=549f70]{w0, T = 50 + K, P = 0.0006112127}[/color] [i]# Output: 444.93[/i]
"""
graph_spectral_buffer_size_text = ''
graph_avg_buffer_size_text = ''
graph_target_value_text = ''
graph_precision_text = ''
control_settings_text = ''
control_name_text = ''
control_variable_choosing_text = ''
control_icon_on_text = ''
control_icon_off_text = ''

tips = [
    ['add_multiple_graphs', '', add_multiple_graphs_text],
    ['main_help', '', main_help_text],
    ['menu', 'Меню', menu_text],
    ['endpoint', 'URL сервера', endpoint_text],
    ['graph_settings', 'Настройки графика', graph_settings_text],
    ['graph_new_indirect_variable_naming', '', graph_new_indirect_variable_naming_text],
    ['graph_variable_choosing', '', graph_variable_choosing_text],
    ['graph_rename_variable', '', graph_rename_variable_text],
    ['graph_expression', 'Выражения', graph_expression_text],
    ['graph_spectral_buffer_size', '', graph_spectral_buffer_size_text],
    ['graph_avg_buffer_size', '', graph_avg_buffer_size_text],
    ['graph_target_value', '', graph_target_value_text],
    ['graph_precision', '', graph_precision_text],
    ['control_settings', '', control_settings_text],
    ['control_name', '', control_name_text],
    ['control_variable_choosing', '', control_variable_choosing_text],
    ['control_icon_on', '', control_icon_on_text],
    ['control_icon_off', '', control_icon_off_text]
]

helping = {}

for tip in tips:
    helping[tip[0]] = {'disabled': False if tip[2] else True, 'title': tip[1], 'text': tip[2]}