import os
import sys

from kivy.resources import resource_add_path
from kivy.utils import platform

import kivymd.effects.stiffscroll

from libs.kivyapp import KivyApp

if __name__ == "__main__":
    if hasattr(sys, '_MEIPASS') and platform != 'android':
        resource_add_path(os.path.join(sys._MEIPASS))
    KivyApp.run()
