import zipfile
import os
import sys
import struct
import difflib
import math
import time
import threading
import xml.etree.ElementTree as etree
import logging
import datetime
import traceback


def init_plog( log_folder_path, filename = None, format=None, datefmt = None, keep_logs=10 ):
    logger = logging.getLogger()
    if not os.path.isdir( log_folder_path ):
        os.makedirs(log_folder_path)

    datefmt = datefmt or '%Y-%m-%d ~ %H-%M-%S-%p'
        
    log_folder = File( log_folder_path, [] )
    log_file_path = filename or datetime.datetime.now().strftime( log_folder.filepath + '%Y-%m-%d ~ %H-%M-%S-%f' + '.log' )

    while len( log_folder.contents ) >= keep_logs:
        os.remove( log_folder.filepath + log_folder.contents.pop(0) )

    format = format or '[%(asctime)-22s] : %(message)s'
    
    logging.basicConfig( filename = os.sep.join( log_file_path.split(os.sep)[-2:] ), filemode = 'w', format = format, datefmt=datefmt, level=logging.DEBUG )
    logging.captureWarnings(True)

#Debug Print
def dprint( msg, *args, end='\n' ):
    ''' Usage: 
        >>>dprint( 'blah `3 be `3 dee `2 `1 sa `0.', 'ni', 'hi', 'bi', 'fly' ) 
        >>>blah <class 'str'>(fly) be <class 'str'>(fly) dee <class 'str'>(bi) <class 'str'>(hi) sa <class 'str'>(ni).
    '''
    if args:
        list = []
        for arg in args:
            list.append( arg )

        msg = msg.split( '`' )

        for i in range( len( msg ) ):
            list_index = ''

            char_list = [ char for char in msg[ i ] ]
            
            for j in range( len( char_list ) ):
                char = char_list[ j ]
                if char.isdigit():
                    list_index += char_list.pop( j )
                else:
                    break
                    
            msg[ i ] = ''.join( char_list )

            if list_index:
                list_index = int( list_index )
                msg[ i-1 ] = str( msg[ i-1 ] ) + str( type( list[ list_index ] ) ) + '( ' + str( list[ list_index ] ) + ' )'

        msg = ''.join( msg )

        plog( msg, end=end )
    else:
        plog( '{0}({1})'.format( type(msg), msg ) )

def plog( msg, level=logging.INFO, end='\n', *args, **kwargs ):
    if msg == '':
        msg = ' '*100
    logger = logging.getLogger()
    logger.log( level, msg, *args, **kwargs )

    if level >= logging.INFO :
        print( '{0}{1}'.format( msg, ' '*100 ) , end = end )

def reindentXmlString( xmlToFix ):
    xml = etree.fromstringlist( xmlToFix )
    return etree.tostring(xml, encoding='utf-8', method='xml').decode()
    
def pop_str( str, index ):
        try:
            index = index % len(str)+1
        except ZeroDivisionError:
            index = 0
        return str[:index-1] + str[index:]
        
def insert_str( str, index, value ):
        try:
            index = index % len(str)+1
        except ZeroDivisionError:
            index = 0
        return str[:index-1] + value + str[index:]

class DiffCombiner( object ):
    def __init__( self, diff_report_folder, original_game_file, mod_file, omni_mod_file, mod_pak_name, log_folder_path, accuracy, area_size ):
        if diff_report_folder[-1] != os.sep:
            diff_report_folder += os.sep
        self.diff_report_folder = diff_report_folder
        
        self.log_folder_path = log_folder_path
        if self.log_folder_path[-1] != os.sep:
            self.log_folder_path += os.sep
            
        self.reindent = False
        
        self.accuracy = accuracy
        self.area_size = area_size
        
        if self.area_size % 2 != 1:
            self.area_size += 1
        
        self.mod_pak_name = mod_pak_name.split(os.sep)[-1]
        
        self.mod_file = mod_file
        self.mod_file_path = self.mod_file.filepath
        
        '''
        #Makes sure every indentation is 4 spaces (as opposed to 1 space or 2 spaces)
        if self.mod_file_path[-4:] == '.xml':
            self.mod_file = reindentXmlString( self.mod_file ).splitlines( keepends=True )
        '''
        self.original_file = original_game_file.contents
        
        '''
        #Makes sure every indentation is 4 spaces (as opposed to 1 space or 2 spaces)
        if self.mod_file_path[-4:] == '.xml':
            self.original_file = reindentXmlString( self.original_file ).splitlines( keepends=True )
        '''
        self.omni_mod_file = omni_mod_file.contents
        
    def diffs_to_folder( self ):
        d =  [ x for x in difflib.ndiff( self.original_file.split('\n') , self.mod_file.contents.split('\n') ) ]

        if not os.path.exists(self.diff_report_folder):
            os.makedirs(self.diff_report_folder)

        if d:
            with open( '{0}diff_report{1}.txt'.format( self.diff_report_folder, len( os.listdir( self.diff_report_folder ) ) ), 'w' ) as diffile:
                diffile.write( ''.join( d ) )

        return '\n'.join( d )

    def similarity(self, str1, str2):
        ''' returns how similar two strings are as a percentage '''
        sequence = difflib.SequenceMatcher(isjunk=None, a=str1, b=str2)
        difference = sequence.ratio()*100
        difference = round( difference, 1 )
        return difference
        
    def most_similar_to(self, str, list):
        ''' returns the index of the element in a list that is most similar to string '''
        how_similar_most_similar_line_is = -1
        most_similar_line_index = -1

        for i in range( len( list ) ):
            similarity = self.similarity( str, list[i] )
            if similarity > how_similar_most_similar_line_is:
                how_similar_most_similar_line_is = similarity
                most_similar_line_index = i

        if most_similar_line_index < 0:
            plog( 'Something went terribly wrong in; DiffCombiner.most_similar_to(str, list).'\
                     'Please remove \'{0}\' from mods folder and file a bug report on nexus mods.'\
                     'Please remember to include your \'logs\' folder located in {1}.'.format( self.mod_pak_name, self.log_folder_path ) )
            plog( 'most_similar_line_index = {0}.\nstr = {1}\nfile = {2}'.format( most_similar_line_index, 
                                                                                                                str, 
                                                                                                                self.mod_file.filepath ), level=logging.DEBUG )
            input('Press Enter/Return to close...')
            assert False
        
        return most_similar_line_index
        
    def find_top_matching_lines( self, line, file ):
        similarities = [ {
            'how_similar': -1,
            'index': None
            } ]

        for i in range( len( file ) ):
            similarity = self.similarity( line, file[ i ] )
            
            if similarity >= similarities[ 0 ][ 'how_similar' ]:
                similarities.insert( 0 , 
                    { 
                        'how_similar': similarity,
                        'index': i
                    } )
                if len( similarities ) > self.accuracy:
                    similarities.pop( -1 )
        return similarities
        
    def compare_areas( self, area1, area2 ):
        if len(area1) != len(area2):
            assert False, 'len( area1 ) and len( area2 ) must be of same size.'
        
        similarities_list = [ ]
        for i in range( len( area1 ) ):
            similarities_list.append( self.similarity( area1[ i ], area2[ i ] ) )
            
        return sum( similarities_list )
        
    def most_similar_area( self, area, file ):
        area_size = len( area )
        
        if area_size % 2 != 1:
            assert False, 'len( area ) MUST be odd.'
            
        line = area[ math.floor( area_size/2 ) ]
        
        top_matches = self.find_top_matching_lines( line, file )
        
        best_area = {
            'how_similar': -1,
            'index': -1
        }

        for i in range( len( top_matches ) ):
            match = top_matches[ i ]
            match_line_number = match[ 'index' ]
            if match_line_number is not None:
            
                match_area = self.get_area( len( area ), file, match[ 'index' ] )
                
                comp = self.compare_areas( area, match_area )
                
                if comp >= best_area[ 'how_similar' ]:
                    best_area[ 'how_similar' ] = comp
                    best_area[ 'index' ] = match_line_number

        return best_area[ 'index' ]
        
        ''' Takes an even length list of lines as area and another list of lines as file returns the middle point'''
        '''
        how_similar_most_similar_area_is = -1
        most_similar_area_center_line_index = -1
        
        if len(area) % 2 == 0:
            plog( 'Something went terribly wrong in; DiffCombiner.most_similar_area(area, file), len(area) is even? what?'
                     'Please remove \'{0}\' from mods folder and file a bug report on nexus mods including:'\
                     'Please remember to include your \'logs\' folder located in {1}.'.format( self.mod_pak_name, self.log_folder_path ) )
            plog( 'area = {0}.\file = {1}'.format( area, self.mod_file.filepath ), level=logging.DEBUG )
            input('Press Enter/Return to close...')
            assert False
            
        for _ in range( math.floor( len(area)/2 ) ):
            file.insert(0, ' ')

        for _ in range( math.floor( len(area)/2 ) ):
            file.append(' ')

        for i in range(math.floor( len(area)/2 )+1, len(file) ):
            diff_perc = [ -1 for _ in range( len( area ) ) ]

            for line in file:
                for j in range( len( area ) ):
                    aline = area[ j ]
                    diff_perc[ j ] = self.similarity(aline, line)

            for j in range( 1, len( diff_perc ) ):
                diff_perc[0] += diff_perc[ j ]

            if diff_perc[0] > how_similar_most_similar_area_is:
                how_similar_most_similar_area_is = diff_perc[0]
                most_similar_area_center_line_index = i - math.floor( len(area)/2 )

        return most_similar_area_center_line_index
        '''
        
    def get_area( self, area_size, file, line_number ):
        file = file[:]
        
        if area_size % 2 != 1:
            assert False, 'area_size MUST be odd'
    
        for _ in range( math.floor( area_size/2 )+1 ):
                file.insert(0, ' ')
                line_number += 1
        for _ in range( math.floor( area_size/2 )+1 ):
            file.append(' ')
            
        area = []
        
        for i in range( line_number - math.floor( area_size/2 ), line_number + math.floor( area_size/2 )+1 ):
            area.append( file[ i ] )
            
        return area
        
    def combine(self):
        diff_file = self.diffs_to_folder()

        if self.omni_mod_file:
            new_file = self.omni_mod_file
        else:
            new_file = self.original_file
        
        diff = diff_file.split( '\n' )
        new = new_file.split( '\n' )
        omni = self.omni_mod_file.split( '\n' )
        orig = self.original_file.split( '\n' )
        mod = self.mod_file.contents.split( '\n' )

        diff_blocks = [ ]
        for i in range( len( diff ) ):
            line = diff[ i ]
            try:
                next_line = diff[ i+1 ]
            except IndexError:
                next_line = ' '
                
            if line and ( line[ 0 ] == '-' or line[ 0 ] == '+' ):
                
                line = [ char for char in line ]
                instruction = line[ 0 ]
                for i in range(2):
                    line.pop( 0 )
                line = ''.join( line )
                
                diff_blocks.append( 
                    { 'line_number': i, 'line': line, 'instruction': instruction, 'details': None }
                )
                if next_line and next_line[ 0 ] == '?':
                    for i in range(2):
                        next_line = pop_str( next_line, 0 )
                    diff_blocks[ -1 ][ 'details' ] = next_line
                    
        for i in range( len( diff_blocks ) ):
            block = diff_blocks[ i ]
            bline = block[ 'line' ]
            bline_number = block[ 'line_number' ]
            instruction = block[ 'instruction' ]
            details = block[ 'details' ]

            if instruction == '-':
                orig_area = self.get_area( self.area_size, orig, orig.index( bline ) )
                olinei = self.most_similar_area( orig_area, new )
                new.pop( olinei )

            elif instruction == '+':
                mod_area = self.get_area( self.area_size, mod, mod.index( bline ) )
                mlinei = self.most_similar_area( mod_area, new )
                new.insert( mlinei, bline )
        
        return '\n'.join( new )

class PakFile( zipfile.ZipFile ):
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

class FileContentsElement( object ):
    def __init__( self, value ):
        self.value = value

    def __repr__( self ):
        return str( self.value )
            
class FileContents( list ):
    def __init__( self, items ):
        for item in self.items:
            self.append( item )
            
    def append(self, value):
        list.append( self, FileContentsElement( value ) )
            
    def __setitem__(self, index, value):
        list.__setitem__( self, index, FileContentsElement( value ) )
            
class File( object ):
    def __init__(self, filepath, contents, zip_path = None):
        self.filepath = filepath
        self.ext = self.filepath.split( '.' )[-1]
        
        if os.path.isdir(self.filepath):
            if self.filepath[-1] != os.sep:
                self.filepath += os.sep
            self.contents = sorted( os.listdir( self.filepath ) )
        else:
            self.contents = contents if self.ext != 'tbl' else ''

        self.zip_path = zip_path

    @property
    def contents(self):
        return self._contents
        
    @contents.setter
    def contents(self, value):
        self._contents = value
        
    def __repr__(self):
        return 'FileObject: {0}'.format( self.filepath )

class Pak( object ):
    def __init__(self, zip_path):
        self.zip_path = zip_path
        
        if not os.path.isfile( self.zip_path ):
            ezip = b'PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            with open(self.zip_path, 'wb') as zip:
                zip.write(ezip)

        self.zip = PakFile( self.zip_path )

        self.files = []

        for member in self.zip.infolist():
            if '.' in member.filename:
                if member.filename[-4:] != '.tbl':
                    file_contents = self.zip.open( member.filename, 'r' )
                    file_contents = file_contents.readlines()
                    try:
                        if type( file_contents[0] ) == type( b'' ):
                            file_contents = b''.join( file_contents ).decode('latin-1')
                        else:
                            file_contents = ''.join( file_contents )
                    except IndexError:
                        file_contents = ''
                else:
                    file_contents = ''
                self.files.append( File( member.filename,  file_contents, self.zip_path ) )
        self.zip.close()

    def __repr__(self):
        str_list = []

        str_list.append( '                             ')
        str_list.append(self.zip_path)
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
            file_contents = file.contents
            try:
                if type( file_contents[0] ) == type( b'' ):
                    file_contents = b''.join( file_contents ).decode('latin-1')
                else:
                    file_contents = ''.join( file_contents )
            except IndexError:
                file_contents = ''
            new_zip.writestr( file.filepath, file_contents )

        new_zip.close()

class QuickPak( object ):
    def __init__(self, zip_path):
        self.zip_path = zip_path

        if not os.path.isfile( self.zip_path ):
            ezip = b'PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            with open(self.zip_path, 'wb') as zip:
                zip.write(ezip)

        self.zip = PakFile( self.zip_path )

        self.quick_folders = []
        
        self.quick_folder_level = 3

        for member in self.zip.infolist():
            if '.' in member.filename:
                quick_folder = member.filename.split('/')[ 0:self.quick_folder_level ]
                
                for i in range( -1, len( quick_folder ), -1 ):
                    if '.' in quick_folder[i]:
                        quick_folder.pop( i )
                        
                quick_folder = '/'.join( quick_folder )

                if quick_folder and quick_folder not in self.quick_folders:
                    self.quick_folders.append( quick_folder )

class Manager( object ):
    def __init__(self, game_files_filepath, mod_files_filepath, diff_report_folder, log_folder_path, load_order_path):
        self.mod_files_filepath = mod_files_filepath
        if self.mod_files_filepath[-1] != os.sep:
            self.mod_files_filepath += os.sep

        if not os.path.exists(self.mod_files_filepath):
            os.makedirs(self.mod_files_filepath)

        self.game_files_filepath = game_files_filepath
        if self.game_files_filepath[-1] != os.sep:
            self.game_files_filepath += os.sep
            
        self.diff_report_folder = diff_report_folder
        if self.diff_report_folder[-1] != os.sep:
            self.diff_report_folder += os.sep
            
        self.log_folder_path = log_folder_path
        if self.log_folder_path[-1] != os.sep:
            self.log_folder_path += os.sep
            
        self.load_order_path = load_order_path

        self.omni_mod_name = 'zzz_simple_mod_loader.pak'
        self.omni_mod_path = self.game_files_filepath + self.omni_mod_name
        
        self.lightning_search_dict = {
                                                'Libs/Tables/rpg': [self.game_files_filepath + 'Tables.pak'],
                                                'Libs/UI/UIActions': [self.game_files_filepath + 'GameData.pak']
                                            }
        self.quick_search_dict ={}
        
        self.non_mergeable_types = [ 'tbl', 'dds' ]

        self.mod_pak_paths = []

        self.original_game_pak_paths = []

    def populate_paks(self, sort = True):
        self._populate_mod_pak_paths()
        self._populate_original_game_pak_paths()
        self._populate_quick_search()
        if sort:
            self._sort_mods_by_load_order()

    def _file_to_pak(self, filepath, make_quick_pak = False):
        pak = None

        if( filepath[-4:] == '.pak' ):
            if make_quick_pak:
                pak = QuickPak( filepath )
            else:
                pak = Pak( filepath )
        elif( filepath[-4:] == '.zip' ):
            #TODO: if user.cfg is in the zip file; append contents to user.cfg
            #TODO: if bin in zip file; go looking for user.cfg in bin/Win64
            #TODO: if Localization is in .zip file; do localization stuff...
            #TODO: if Data is in .zip file; recursively call '_populate_mod_paks' on the new "Data" folder.
            #TODO: if Engine is in .zip file; recursively call '_populate_mod_paks' on Engine folder.
            #TODO: if .pak is in .zip file; load in the .pak file.
            pass

        return pak
            
    def _populate_mod_pak_paths(self):
        plog('Getting mod paks.')
        for filename in os.listdir( self.mod_files_filepath ):
            if filename[-4:] == '.pak' or filename[-4:] == '.zip':
                self.mod_pak_paths.append( self.mod_files_filepath + filename )
                
    def _populate_original_game_pak_paths(self):
        plog('Getting necessary game files.')
        def get_all_game_pak_paths( fp = None ):
            if fp == None:
                fp = self.game_files_filepath

            if fp[-1] != os.sep:
                fp += os.sep

            paks = []
            for pak in os.listdir( fp ):
                if os.path.isdir( fp + pak ):
                    #Recursively get all .pak files in the game files.
                    for gotten_pak in get_all_game_pak_paths( fp + pak ):
                        paks.append( gotten_pak )
                elif '.pak' in pak and pak[0].lower() != 'z':
                    paks.append( fp + pak )

            return paks

        pak_paths = get_all_game_pak_paths()

        needed_files = []
        for filename in os.listdir( self.mod_files_filepath ):
            if filename[-4:] == '.pak' or filename[-4:] == '.zip':
                mod_pak = self._file_to_pak( self.mod_files_filepath + filename )
                for file in mod_pak.files:
                    if file.filepath not in needed_files:
                        needed_files.append( file.filepath.lower() )

        for pak_path in pak_paths:
            if pak_path != self.omni_mod_path:
                pak = PakFile( pak_path )
                for member in pak.infolist():
                    if member.filename.lower() in needed_files:
                        self.original_game_pak_paths.append( pak_path )
                pak.close()

    def _populate_quick_search(self):
        plog('Initializing Quick Search')
        
        for original_game_pak_filepath in self.original_game_pak_paths:
            original_game_pak = self._file_to_pak( original_game_pak_filepath, make_quick_pak = True )
            for folder in original_game_pak.quick_folders:
                if folder not in self.quick_search_dict.items():
                    self.quick_search_dict[ folder ] = [ ]
                self.quick_search_dict[ folder ].append( original_game_pak.zip_path )

    def search( self, filepath, search_dict ):
        quick_folder = '/'.join( filepath.split('/')[ 0:3 ] )
        
        for path, paks in search_dict.items():
            if path == quick_folder:
                return paks
                
        return None
            
    def lightning_search(self, filepath):
        plog( '    Performing Lightning Search for Pak Containing File: {0}'.format( filepath ) )
        result = self.search( filepath, self.lightning_search_dict )
        if result:
            plog( '        Lightning Search Found Pak File.' )
            plog( '        Looking for {0} in Pak File.'.format( filepath ) )
        else:
            plog( '        Lightning Search Failed.' ) 
            
        return result
        
    def quick_search(self, filepath):
        plog( '    Performing Quick Search for Pak Containing File: {0}'.format( filepath ) )
        result = self.search( filepath, self.quick_search_dict )
        if result:
            plog( '        Quick Search Found Pak File.' )
            plog( '        Looking for {0} in Pak File.'.format( filepath ) )
        else:
            plog( '        Quick Search Failed.' ) 
        return result

    def make_omnipak(self):
        plog('')
        plog( '~=Building omni-mod=~' )
        plog( 'This may take awhile. Go get a snack and make some coffee.' )
        
        #Cleanup old omni-mod and create new one.
        if os.path.exists(self.omni_mod_path):
            os.remove(self.omni_mod_path)
        omni_mod = Pak( self.omni_mod_path )
        
        #Cleanup report diffs folder.
        for file in os.listdir(self.diff_report_folder):
            os.remove(self.diff_report_folder + file)
        
        #Iterate over all mods in the mods folder.
        for mod_pak_filepath in self.mod_pak_paths:
            plog('')
            plog( 'Loading New Mod: {0}'.format( mod_pak_filepath ) )
            
            mod_pak = self._file_to_pak( mod_pak_filepath )
            for mod_pak_file_index in range( len( mod_pak.files ) ):
                mod_file = mod_pak.files[ mod_pak_file_index ]
                
                if mod_file.ext not in self.non_mergeable_types:
                    original_game_pak_paths = self.lightning_search( mod_file.filepath ) or self.quick_search( mod_file.filepath )

                    mod_file_in_omni_mod = False
                    
                    for original_game_pak_filepath in original_game_pak_paths:
                        original_game_pak = self._file_to_pak( original_game_pak_filepath )
                        plog( '        Searching in Game Pak: {0}'.format( original_game_pak.zip_path ) )

                        for original_game_file in original_game_pak.files:
                            if mod_file.filepath.lower() == original_game_file.filepath.lower():
                                plog( '            Found Game File.' )
                                plog('')

                                
                                
                                plog( '        Searching Omni-Mod for: {0}'.format( mod_file.filepath ) )
                                for omni_mod_file_index in range( len( omni_mod.files ) ):
                                    omni_mod_file = omni_mod.files[ omni_mod_file_index ]
         
                                    if ( mod_file.filepath.lower() == omni_mod_file.filepath.lower() ):
                                        plog( '            Found Duplicate.' )
                                        plog('')
                                        mod_file_in_omni_mod = True
                                        omni_mod.files[ omni_mod_file_index ] = self._merge_files( original_game_file, omni_mod_file, mod_file, mod_pak.zip_path )
                                        break
                                if mod_file_in_omni_mod:
                                    break
                            if mod_file_in_omni_mod:
                                break
                        if mod_file_in_omni_mod:
                            break
                                        
                    if not mod_file_in_omni_mod:
                        plog( '            Creating New File in Omni-Mod: {0}'.format( mod_file.filepath ) )
                        
                        new_file = mod_file
                        new_file.filepath = new_file.filepath.lower()

                        omni_mod.files.append( new_file )
                else:
                    plog( '    Handling non-mergeable filetype: {0}'.format( mod_file.filepath ) )
                    mod_file_in_omni_mod = False
                    for omni_mod_file_index in range( len( omni_mod.files ) ):
                        omni_mod_file = omni_mod.files[ omni_mod_file_index ]
                        if mod_file.filepath.lower() == omni_mod_file.filepath.lower():
                            plog( '        File already exists in Omni-Mod. Replacing file.' )
                            plog('')

                            mod_file_in_omni_mod = True

                            new_file = mod_file
                            new_file.filepath = new_file.filepath.lower()

                            omni_mod.files[ omni_mod_file_index ] = new_file

                            break

                    if not mod_file_in_omni_mod:
                        plog( '        Creating New File in Omni-Mod: {0}'.format( mod_file.filepath ) )
                        plog('')
                        
                        new_file = mod_file
                        new_file.filepath = new_file.filepath.lower()

                        omni_mod.files.append( new_file )

        omni_mod.write()

    def _merge_files(self, original_game_file, omni_mod_file, mod_file, mod_pak_name):
        new_file = File( original_game_file.filepath, omni_mod_file.contents )

        plog( '            Merging in Mod File: {0}'.format( mod_file.filepath ) )

        #TODO: Move accuracy and area out to a config file;
        accuracy = 10
        area_size = 5

        new_file.contents = DiffCombiner( self.diff_report_folder, 
                                                              original_game_file, 
                                                              mod_file, 
                                                              omni_mod_file, 
                                                              mod_pak_name,
                                                              self.log_folder_path,
                                                              accuracy,
                                                              area_size ).combine()

        return new_file

    def _sort_mods_by_load_order(self):
        plog('Sorting mods by load order')
        mod_pak_paths = self.mod_pak_paths[:]
        sorted_list = []
            
        try:
            with open(self.load_order_path, 'r') as load_order:
                load_order = load_order.read().splitlines()
        except FileNotFoundError:
            with open(self.load_order_path, 'w') as load_order:
                file = os.listdir( self.mod_files_filepath )
                file_map = []
                for filename in file[:]:
                    if filename[-4:] == '.pak' or filename[-4:] == '.zip':
                        file_map.append(filename)
                load_order.write( '\n'.join( file_map ) )
                
            with open(self.load_order_path, 'r') as load_order:
                load_order = load_order.read().splitlines()

        for load_order_list_element in load_order:
            found_mod = False

            for mod_pak_path in mod_pak_paths[:]:
                if mod_pak_path == self.mod_files_filepath + load_order_list_element:
                    found_mod = True
                    sorted_list.append( mod_pak_paths.pop( mod_pak_paths.index(mod_pak_path) ) )
                    break

            if not found_mod:
                plog("Warning! Mod in load_order file but not in mods folder. Please delete load_order file after adding or removing mods.")

        if mod_pak_paths:
            plog("Warning! Mods in mods folder but not in load order file. Please delete load_order file after adding or removing mods.")
            for _ in range( len( mod_pak_paths[:] ) ):
                sorted_list.insert(0, mod_pak_paths.pop( 0 ) )

        self.mod_pak_paths = sorted_list

def _get_paths( exe ):
    log_folder_path = os.path.dirname( os.path.abspath('__file__') ) + os.sep + 'logs' + os.sep
    init_plog( log_folder_path )
    plog( 'exe_path = {0}'.format(exe), level=logging.DEBUG )

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

    mods_path = os.path.dirname( os.path.realpath('__file__') ) + os.sep + 'mods' + os.sep

    plog( 'included mods:', level=logging.DEBUG )
    
    if not os.path.exists(mods_path):
        os.makedirs(mods_path)
    
    for mod in os.listdir( mods_path ):
        plog( '    {0}'.format(mod), level=logging.DEBUG )
        
    diff_report_folder_path = os.path.dirname( os.path.realpath('__file__') ) + os.sep + 'diff_reports' + os.sep
    
    if not os.path.exists(diff_report_folder_path):
        os.makedirs(diff_report_folder_path)
    
    load_order_path = os.path.dirname( os.path.realpath('__file__') ) + os.sep + 'load_order.txt'
    
    plog('load order:', level=logging.DEBUG)
    if os.path.isfile(load_order_path):
        with open(load_order_path, 'r') as load_order:
            for line in load_order.read().splitlines():
                plog('    {0}'.format( line ), level=logging.DEBUG)
    else:
        plog('    No load order file', level=logging.DEBUG)
    
    return usercfg, data_path, localization_path, mods_path, diff_report_folder_path, log_folder_path, load_order_path

def play_loading_anim( started ):
    global PLAYANIM
    
    anim = [ '\\', '|', '/', '-'  ]
    PLAYANIM = True
    while PLAYANIM:
        for x in range( len(anim) ):
            print ( 'Loading{0} Elapsed Time - {1} - Please allow up to 5 minutes for each mod.\r'.format( anim[ x ], datetime.datetime.now()-started, ), end='' )
            time.sleep(0.3)
    print(' '*100)
    
if __name__ == '__main__':
    started = datetime.datetime.now()
    
    with open('config', 'r') as file:
        file = file.read().split('\n')
        for line in file:
            line = line.split('=')
            if line[0] == 'exe_path':
                exe = line[1]

    #TODO: Make a server and ask the user if it's ok to send us data with 'add data is anonymous blah blah blah', if yes; on exception; send logfiles to server.
    sys.excepthook = lambda *exc_info : plog( 'Exception raised:\n{0}'.format( ''.join(traceback.format_exception(*exc_info) ) ), level=logging.ERROR )

    usercfg, data_path, localization_path, mods_path, diff_report_folder_path, log_folder_path, load_order_path = _get_paths(exe)

    loading_anim_thread = threading.Thread( target=play_loading_anim, args = ( started, )  )
    
    if not os.path.isfile( os.path.dirname( os.path.abspath('__file__') ) + os.sep + '.gitignore' ):
        loading_anim_thread.start()

    manager = Manager( data_path, mods_path, diff_report_folder_path, log_folder_path, load_order_path )
    manager.populate_paks()
    manager.make_omnipak()

    PLAYANIM = False

    try:
        loading_anim_thread.join()
    except RuntimeError:
        pass

    plog( 'Elapsed Time - {0}'.format( datetime.datetime.now() - started ) )
    plog( 'Successfully Loaded All Mods' )
    input( 'Press Enter/Return to close...' )