from kivy.uix.boxlayout import BoxLayout

from scripts.mod import Mod
from manager import get_paths

class ModList(BoxLayout):
    def __init__(self, manager, *args, **kwargs):
        super(ModList, self).__init__(*args, **kwargs)
        
        #TODO: Move manager to parent 'ModListContainer' object 
        self.manager = manager
        self.manager.populate_mod_paks()
        self.manager.sort_mods_by_load_order()
        #self.populate_original_game_paks()
        #self.manager.make_omnipak()
        
        for i in range( len( manager.mod_paks ) ):
            m = Mod( manager.mod_paks[i].zip_path, i )
            self.add_widget(m)

'''
for mod in os.listdir('mods'):
            print(mod)
'''