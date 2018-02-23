""" This module holds the main menu screen.
"""

#pylint: disable=locally-disabled, too-many-ancestors

import os

from screens.main_menu.buttons.exit_button import ExitButton
from scripts.screen import Screen


class MainMenu(Screen):
    """ This is the main menu Screen which holds the main menu.

        #TODO: doctest here.
    """
    def __init__(self, *args, **kwargs):
        """ Method gets called when class in instantiated.
        """

        super(MainMenu, self).__init__(*args, **kwargs)

        #TODO: Move these out to a BoxLayout. So they can be centered
        #       Easier.

        for mod in os.listdir('mods'):
            print(mod)
        
        #Creates the Exit Button and sets it as a child of self.
        self._exit_button = ExitButton()
        self._exit_button.text = "Exit"
        self.add_widget(self._exit_button)
