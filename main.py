""" This is the main module; where everything begins.
"""
import sys
sys.dont_write_bytecode = True

import os
from pathlib import Path
import random

from kivy.app import App
from kivy.core.window import Window
from kivy.config import Config
from kivy.utils import platform as PLATFORM

from scripts.screen_manager import ScreenManager


class GameApp(App):
    """The GameApp class which contains the game.

        #TODO: doctest here
    """
    def build(self):
        """ Method gets called by Python start, run() and before on_start()
                see https://kivy.org/docs/guide/basic.html

            #TODO: doctest here
        """

        #FIXME: Window.size gets set to a random size for debugging but
        #   before release the window should have a default size and
        #   should also save it's size on_resize() to a file and then
        #   load in those settings.
        _x, _y = random.randint(500, 1000), random.randint(500, 1000)
        Window.size = (random.randint(500, 1000), random.randint(500, 1000))
        #Window.size = (300, 500)

        #Sets the title of the application window.
        self.title = 'Simple Mod Loader'

        #Declares a dictionary to hold icon file path objects.
        icons = {
            '16': Path('images/icons/icon-16.png'),
            '24': Path('images/icons/icon-24.png'),
            '32': Path('images/icons/icon-32.png'),
            '48': Path('images/icons/icon-48.png'),
            '64': Path('images/icons/icon-64.png'),
            '128': Path('images/icons/icon-128.png'),
            '256': Path('images/icons/icon-256.png'),
            '512': Path('images/icons/icon-256.png'),
        }

        #Trys to determine the size an icon should be based on the os.
        if  icons['256'].is_file() and PLATFORM == 'linux' or\
                                       PLATFORM == 'macosx':
            #Sets the icon for the window to the 256x256 version.
            self.icon = str(icons['256'])
        elif icons['32'].is_file():
            #Sets the icon for the window to the 32x32 version.
            self.icon = str(icons['32'])
        else:
            #Sets the icon for the window to the first available version.
            for icon in icons.items():
                if icon.is_file():
                    self.icon = str(icon)

        #Creates a ScreenManager that will hold all our screens
        #   i.e. MainMenu(), TwitchPlaysSession(), etc..etc..
        _r = ScreenManager()

        #Returns the ScreenManager mentioned earlier.
        return _r

if __name__ == "__main__":
    #TODO: Move these out to a config file.
    Config.set('kivy', 'log_name', 'log_%y-%m-%d_%_.txt')
    LOG_DIR = os.path.dirname(os.path.abspath(__file__)) + '\\logs'
    Config.set('kivy', 'log_dir', LOG_DIR)

    CURRENT_WORKING_DIRECTORY = os.getcwd()

    #Sets kivy's home to the current worlding directory.
    os.environ['KIVY_HOME'] = CURRENT_WORKING_DIRECTORY

    #Creates a GameApp object defined above.
    GAMEAPP = GameApp()

    #Calls GAMEAPP's run method which calls GAMEAPP.build().
    GAMEAPP.run()

    #Gracefully exits python.
    quit()
