__all__ = ('OpacityScrollEffectSmooth', )


from kivy.effects.dampedscroll import DampedScrollEffect
import math


class OpacityScrollEffectSmooth(DampedScrollEffect):

    friction = 0.1
    min_overscroll = 0
    min_velocity = 0.1

    def on_overscroll(self, *args):
        if self.target_widget and self.target_widget.height != 0:
            alpha = (1.0 -
                     math.sqrt(abs(self.overscroll / float(self.target_widget.height)))/5)
            self.target_widget.opacity = min(1., max(0.2, alpha))
        self.trigger_velocity_update()
