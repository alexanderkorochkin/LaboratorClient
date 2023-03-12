from re import split

from kivy.animation import Animation
from kivy.metrics import sp


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


def truncate_string(string, N):
    if len(string) > N:
        substring = string[0: N]
        last_alpha = 0
        for i in range(N - 1, 0, -1):
            if string[i - 1].isalpha() and not string[i].isalpha():
                last_alpha = i
                break
        return substring[0: last_alpha] + "…"
    else:
        return string


def animated_hide_widget_only(wid, method):
    anim = Animation(pos=(wid.pos[0], sp(10) - sp(200)), opacity=0, duration=0.2, t='in_quart')
    anim.bind(on_complete=method)
    anim.start(wid)


def animated_show_widget_only(wid, method):
    anim = Animation(pos=(wid.pos[0], sp(10)), opacity=1,  duration=0.2, t='out_quart')
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
