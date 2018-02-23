import zipfile
import os
import struct

class PakFile(zipfile.ZipFile):
    def open(self, name, mode="r", pwd=None):
        """Return file-like object for 'name'."""
        if mode not in ("r", "U", "rU"):
            raise RuntimeError('open() requires mode "r", "U", or "rU"')
        if 'U' in mode:
            import warnings
            warnings.warn("'U' mode is deprecated",
                          DeprecationWarning, 2)
        if pwd and not isinstance(pwd, bytes):
            raise TypeError("pwd: expected bytes, got %s" % type(pwd))
        if not self.fp:
            raise RuntimeError(
                "Attempt to read ZIP archive that was already closed")

        # Make sure we have an info object
        if isinstance(name, zipfile.ZipInfo):
            # 'name' is already an info object
            zinfo = name
        else:
            # Get info object for name
            zinfo = self.getinfo(name)

        self._fileRefCnt += 1
        zef_file = zipfile._SharedFile(self.fp, zinfo.header_offset, self._fpclose, self._lock)
        try:
            # Skip the file header:
            fheader = zef_file.read(zipfile.sizeFileHeader)
            if len(fheader) != zipfile.sizeFileHeader:
                raise zipfile.BadZipFile("Truncated file header")
            fheader = struct.unpack(zipfile.structFileHeader, fheader)
            if fheader[zipfile._FH_SIGNATURE] != zipfile.stringFileHeader:
                raise zipfile.BadZipFile("Bad magic number for file header")

            fname = zef_file.read(fheader[zipfile._FH_FILENAME_LENGTH])
            if fheader[zipfile._FH_EXTRA_FIELD_LENGTH]:
                zef_file.read(fheader[zipfile._FH_EXTRA_FIELD_LENGTH])

            if zinfo.flag_bits & 0x20:
                # Zip 2.7: compressed patched data
                raise NotImplementedError("compressed patched data (flag bit 5)")

            if zinfo.flag_bits & 0x40:
                # strong encryption
                raise NotImplementedError("strong encryption (flag bit 6)")

            if zinfo.flag_bits & 0x800:
                # UTF-8 filename
                fname_str = fname.decode("utf-8")
            else:
                fname_str = fname.decode("cp437")

            fname_str = '/'.join(fname_str.split('\\'))
                
            if fname_str != zinfo.orig_filename:
                raise zipfile.BadZipFile(
                    'File name in directory %r and header %r differ.'
                    % (zinfo.orig_filename, fname_str))

            # check for encrypted flag & handle password
            is_encrypted = zinfo.flag_bits & 0x1
            zd = None
            if is_encrypted:
                if not pwd:
                    pwd = self.pwd
                if not pwd:
                    raise RuntimeError("File %s is encrypted, password "
                                       "required for extraction" % name)

                zd = zipfile._ZipDecrypter(pwd)
                # The first 12 bytes in the cypher stream is an encryption header
                #  used to strengthen the algorithm. The first 11 bytes are
                #  completely random, while the 12th contains the MSB of the CRC,
                #  or the MSB of the file time depending on the header type
                #  and is used to check the correctness of the password.
                header = zef_file.read(12)
                h = list(map(zd, header[0:12]))
                if zinfo.flag_bits & 0x8:
                    # compare against the file type from extended local headers
                    check_byte = (zinfo._raw_time >> 8) & 0xff
                else:
                    # compare against the CRC otherwise
                    check_byte = (zinfo.CRC >> 24) & 0xff
                if h[11] != check_byte:
                    raise RuntimeError("Bad password for file", name)

            return zipfile.ZipExtFile(zef_file, mode, zinfo, zd, True)
        except:
            zef_file.close()
            raise

class File(object):
    def __init__(self, filepath, contents):
        self.filepath = filepath
        self.contents = contents

    def __repr__(self):
        return 'filepath = {0}, contents = {1}'.format( self.filepath, self.contents )

class Pak(object):
    def __init__(self, zip_path):
        self._zip_path = zip_path
        self._zip = PakFile( self.zip_path )
        self._files = []

        for member in self.zip.infolist():
            if '.' in member.filename:
                fname = member.filename.split('/')
                #fname = '\\'.join(fname).encode()
                fname = '/'.join(fname)
                self.files.append( File( member.filename, self.zip.open( fname, 'r' ).read().splitlines() ) )

        self.zip.close()

    @property
    def zip_path(self):
        return self._zip_path

    @zip_path.setter
    def zip_path(self, value):
        self._zip_path = value

    @property
    def zip(self):
        return self._zip

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, value):
        self._files = value

    def __repr__(self):
        str_list = []

        str_list.append( '---' + self.zip_path )

        for file in self.files:
            str_list.append( '    ' + str(file) )

        str_list.append('---')

        return '\n'.join(str_list)

    def write(self, filename = None):
        if filename == None:
            filename = self.zip_path

        new_zip = PakFile(self.zip_path, 'w')

        for file in self.files:
            new_zip.writestr(file.filepath, b'\n'.join( file.contents ))

        new_zip.close()

class Manager(object):
    def __init__(self, mod_files_filepath, game_files_filepath):
        self.mod_files_filepath = mod_files_filepath
        self.mod_files_filepath = mod_files_filepath
        if self.mod_files_filepath[-1] != os.sep:
            self.mod_files_filepath += os.sep

        if not os.path.exists(self.mod_files_filepath):
            os.makedirs(self.mod_files_filepath)

        self.game_files_filepath = game_files_filepath
        if self.game_files_filepath[-1] != os.sep:
            self.game_files_filepath += os.sep

        self.new_file_name = 'zzz_simple_mod_loader.pak'
        self.new_file_path = self.game_files_filepath + 'zzz_simple_mod_loader.pak'

        self.mod_paks = []

        self.original_game_paks = []

    def populate_paks(self, sort = True):
        self._populate_mod_paks()
        self._populate_original_game_paks()
        if sort:
            self._sort_mods_by_load_order()

    def _populate_mod_paks(self):
        for filename in os.listdir( self.mod_files_filepath ):
            self.mod_paks.append( Pak( self.mod_files_filepath + filename ) )

    def _populate_original_game_paks(self):
        def get_all_game_paks( fp = None ):
            if fp == None:
                fp = self.game_files_filepath

            if fp[-1] != os.sep:
                fp += os.sep

            folder = os.listdir( fp )
            paks = []

            for pak in folder:
                if os.path.isdir( fp + pak ):
                    for gotten_pak in get_all_game_paks( fp + pak ):
                        paks.append( gotten_pak )
                elif '.pak' in pak:
                    paks.append( fp + pak )

            return paks

        paks = get_all_game_paks()

        needed_files = []
        for mod_pak in self.mod_paks:
            for file in mod_pak.files:
                if file.filepath not in needed_files:
                    needed_files.append( file.filepath )

        for pak in paks:
            if pak != self.game_files_filepath + self.new_file_name:
                z = PakFile( pak )
                for member in z.infolist():
                    need_file = False
                    if member.filename in needed_files:
                        need_file = True
                        self.original_game_paks.append( Pak( pak ) )
                z.close()

    def make_omnipak(self):
        mod_paks = self.mod_paks[:]
        new_pak = mod_paks.pop(0)
        new_pak.zip_path = self.new_file_path

        for mod_pak in mod_paks:
            for mod_file in mod_pak.files:
                in_new_pak_files = False

                for new_pak_file_index in range( len( new_pak.files ) ):
                    if  new_pak.files[new_pak_file_index].filepath == mod_file.filepath:
                        in_new_pak_files = True

                        for original_game_pak in self.original_game_paks:
                            for original_game_file in original_game_pak.files:
                                if original_game_file.filepath == new_pak.files[new_pak_file_index].filepath:
                                    new_pak.files[new_pak_file_index] = self._merge_files(original_game_file, new_pak.files[new_pak_file_index], mod_file)

                if not in_new_pak_files:
                    new_pak.files.append(mod_file)

        new_pak.write()

    def _merge_files(self, original_game_file, new_pak_file, mod_file):
        new_file = new_pak_file

        for i in range( len( mod_file.contents ) ):
            if mod_file.contents[i] != original_game_file.contents[i]:
                new_file.contents[i] = mod_file.contents[i]

        return new_file
        
    def _sort_mods_by_load_order(self):
        mod_paks = self.mod_paks
        sorted_list = []

        if not os.path.isfile('load_order'):
            if len( os.listdir( self.mod_files_filepath ) ) > 1:
                with open('load_order', 'w') as file:
                    file.write( '\n'.join( os.listdir( self.mod_files_filepath ) ) )

        load_order = open('load_order').read().splitlines()

        for load_order_list_element in load_order:
            for mod in self.mod_paks:
                found_mod = False

                if mod.zip_path == self.mod_files_filepath + load_order_list_element:
                    found_mod = True
                    sorted_list.append( mod_paks.pop( self.mod_paks.index(mod) ) )
                
                if not found_mod:
                    print("Warning! Mod in load order file but not in mods folder.")
                
        if mod_paks:
            print("Warning! Mod in folder but not in load order file.")
            for mod_index in range( self.mod_paks ):
                sorted_list.insert(0, mod_paks.pop( mod_index ) )
                
        self.mod_paks = sorted_list

def _get_paths(exe):
    path_list = exe.split(os.sep)
    path_list.pop()

    path_list.append( 'user.cfg' )
    usercfg = os.sep.join(path_list)

    for i in range(3):
        path_list.pop()

    path_list.append('Data')
    data_path = os.sep.join(path_list)

    path_list.pop()

    path_list.append('Localization')
    localization_path = os.sep.join(path_list)

    mods_path = os.path.dirname( os.path.realpath(__file__) ) + os.sep + 'mods' + os.sep
    
    return usercfg, data_path, localization_path, mods_path

if __name__ == '__main__':
    exe = 'C:\Program Files (x86)\Kingdom Come - Deliverance\Bin\Win64\KingdomCome.exe'
    
    usercfg, data_path, localization_path, mods_path = _get_paths(exe)
    
    manager = Manager(mods_path, data_path)
    manager.populate_paks()
    manager.make_omnipak()
    '''
    for pak in manager.original_game_paks:
        print(pak)

    for pak in manager.mod_paks:
        print(pak)
    '''