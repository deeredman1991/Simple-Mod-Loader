from kivy.uix.boxlayout import BoxLayout

from scripts.mod_list import ModList
from manager import get_paths, Manager

class ModListContainer(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(ModListContainer, self).__init__(*args, **kwargs)
        
        usercfg, data_path, localization_path, mods_path = get_paths()
        
        self.manager = Manager(mods_path, data_path)
        
        self.mod_list = ModList(self.manager)
        self.add_widget(self.mod_list)
        
        #TODO: Move these two lines out to buttons.
        #self.manager.populate_original_game_paks()
        #self.manager.make_omnipak()
        