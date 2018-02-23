#Should be made up two labels, and two buttons.
#Label 1 should be the position of the mod in mod_list and 
#Label 2 should be the name of the mod.
#button one should move the element up in the mod_list
#button two should move the element down in the mod_list

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class Mod(BoxLayout):
    def __init__(self, mod_name, position):
    
        self._position = position
    
        self._position_label = Label()
        self._position_label.text = self.position
        self.add_widget(self._position_label)
        
        self._mod_name_label = Label()
        self._position_label.text = mod_name
        
        self._up_button = Button()
        self._up_button.text = 'up'
        self.add_widget(self._up_button)
        
        self._dn_button = Button()
        self._dn_button.text = 'dn'
        self.add_widget(self._dn_button)
        
    @property
    def position(self)
        return self._position
        
    @position.setter
    def position(self, value):
        #TODO: make it change the position of this object in the parent object
        self._position = value
        self._position_label.text = self._position