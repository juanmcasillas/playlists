##!/usr/bin/env bash
# -*- coding: utf-8 -*-
# /////////////////////////////////////////////////////////////////////////////
# //
# // gen_playlist.py
# //
# // generates a playlist based on a directory. Jam version
# //
# // 26/03/2024 12:39:20
# // (c) 2024 Juan M. Casillas <juanm.casillas@gmail.com>
# //
# /////////////////////////////////////////////////////////////////////////////

# find D:\\ -iname ".\*" -exec rm -rf "{}" ";"
# https://github.com/globocom/m3u8

import argparse
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3,APIC
import argparse
import sys
import glob
import os
import pathlib
import m3u8
import shutil
import platform
from PIL import Image
from io import BytesIO

class PlayListManager:
    # platform.system()
    platforms = {
        'Windows': None,
        'Darwin': "/Volumes/SPORT PLUS",
        'Linux': None
    }
    MUSIC_DIR = "Music"
    PLAYLIST_DIR = "Playlists"
    MAX_IMG_SZ = (450, 450)
    MAX_IMG_WIDTH, MAX_IMG_HEIGHT = MAX_IMG_SZ
    MAX_DPI = (72,72)

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.extensions = ('.mp3', )
        self.playlist_formatters = {
            'm3u': self.gen_m3u_playlist
        }
        self.jam_root = None

    def check_platform(self, jam_root):
        if jam_root:
            self.jam_root = jam_root
            return jam_root

        system = platform.system()
        if not system in PlayListManager.platforms.keys():
            return None

        self.jam_root = PlayListManager.platforms[system]
        self.music_path = self.jam_music_dir(self.jam_root)
        self.playlist_path = self.jam_playlist_dir(self.jam_root)

        return self.jam_root

    def generate_playlist_entry(self, id3, name):
        "if we have id3 tag, use the id3 title and artist keys, else use the name of the file"
        id3_tags = set([ 'title', 'artist'])
        id3_items = set(id3.keys())

        if id3_tags.issubset(id3_items):
            # keys are contained in id3 keys, so use it.
            ret = "%s - %s" % (id3['artist'][0], id3['title'][0])
        else:
            ret = name
            # remove extensions
            for ex in self.extensions:
                path =  pathlib.Path(ret)
                if path.suffix.lower() == ex.lower():
                    ret = path.stem

        return ret

    def jam_dir(self, base, directory):
        if self.jam_root:
            directory = os.path.join(self.jam_root, base, directory)
        return directory

    def jam_music_dir(self, directory=""):
        return self.jam_dir(self.MUSIC_DIR, directory)

    def jam_playlist_dir(self, directory=""):
        return self.jam_dir(self.PLAYLIST_DIR, directory)

    def jam_music_entry_dir(self, entry):
        # return the entry using the base directory of jam's music
        # use the windows format supported in the player
        p = "..\\%s" % pathlib.Path(entry).relative_to(self.jam_root)
        return p.replace("/","\\")

    def build_playlist_from_directory(self, directory):

        orig_dir = directory
        directory = self.jam_music_dir(directory)
        playlist = []

        for path, dirc, files in os.walk(directory):
            for name in files:
                if name.lower().endswith(self.extensions):
                    # build the relative path in this platform
                    full_fname =  os.path.sep.join([path] + [name])
                    local_fname = pathlib.Path(full_fname).relative_to(directory)
                    try:
                        mt = EasyID3(full_fname)
                        playlist_entry = self.generate_playlist_entry(mt, name)
                        audio = MP3(full_fname)
                    except Exception as e:
                        if self.verbose:
                            print("Invalid file: %s (%s)" % (full_fname,e))

                    playlist.append({
                        'title': playlist_entry,
                        'file': self.jam_music_entry_dir(full_fname),
                        'path': full_fname,
                        'duration': audio.info.length
                    })
                else:
                    if self.verbose:
                        print("Warning: Unknown file extension for %s, skipping" % name)

        return playlist

    def store_playlist(self, playlist, plname, format='m3u'):
        return self.playlist_formatters[format](playlist, plname)

    def gen_m3u_playlist(self, playlist, plname):

        target = self.jam_playlist_dir(plname)
        path =  pathlib.Path(target)
        if path.suffix in ('.m3u8', '.m3u'):
            pass
        else:
            target = "%s.m3u" % target

        if self.verbose:
            print("generating m3u playlist: %s" % target)

        with open(target,"w",encoding='utf-8', newline='') as fd:
            fd.write("#EXTM3U\r\n")
            for item in playlist:
                if self.verbose:
                    print("* adding: %s" % item['file'])
                fd.write("#EXTINF:%d, %s\r\n" % (item['duration'], item['title']))
                fd.write("%s\r\n" % item['file'])

        if self.verbose:
            print("Added %d files" % len(playlist))
        return len(playlist)


    


    def read_playlist(self, playlist_file):

        if not os.path.exists(playlist_file):
            raise ValueError("playlist file %s doesn't exists" % playlist_file)

        playlist = []
        try:
            data = m3u8.load(playlist_file)
        except Exception as e:
            raise(e)

        if data:
            for i in data.segments:
                playlist.append({
                    'title': i.title,
                    'file': i.uri,
                    'path': str(pathlib.Path(i.uri)),
                    'duration': i.duration
                })
        return playlist

    def migrate_playlist(self, playlist_data, playlist_name, from_playlist, create_dir=False):

        new_playlist = []

        # put all the files in the same dir, so we can
        # use playlists to manage the content.
        if create_dir:
            to_dir = self.jam_music_dir(playlist_name)
        else:
            to_dir = self.jam_music_dir()

        if  not os.path.exists(to_dir):
            os.makedirs(to_dir, exist_ok=True)

        from_dir_path = pathlib.Path(from_playlist).parent
        to_dir_path   = pathlib.Path(to_dir  )

        # process the source data in playlist_data. If copy_files false
        # move then to the relative directory, and change the path else
        # move the files. Then write the playlist in the right place
        # with the pointers moved.
        for item in playlist_data:
            # check if the path is absolute.
            # if so, just copy the file (check the intermediate paths)
            # else, build the abs path and do it.
            src_file = pathlib.Path(item['file'])

            if not src_file.is_absolute():
                tgt_file = src_file
                src_file = from_dir_path / src_file
            else:
                tgt_file = to_dir_path / src_file.name

            # create target structure.
            tgt_path = tgt_file.parent
            if  not os.path.exists(tgt_path):
                os.makedirs(tgt_path, exist_ok=True)

            if args.verbose:
                print("copying %s -> %s" % (src_file, tgt_file))

            try:
                if not os.path.exists(tgt_file):
                    shutil.copyfile(src_file, tgt_file)
                    self.check_artwork(tgt_file)
            except shutil.SameFileError:
                pass

            item['file'] = self.jam_music_entry_dir(tgt_file)
            new_playlist.append(item)

        self.gen_m3u_playlist(new_playlist, playlist_name)

    def check_artwork(self, music_file):
        # change image things.
        try:
            mp3file = MP3(music_file, ID3=ID3)
        except Exception as e:
            print("Invalid MP3 file, skipping it: %s %s" % (music_file, e))
            return
        
        tags = mp3file.tags
        if not tags:
            return 
        if args.verbose > 2:
            print("----", music_file)
            print(tags.pprint())

        if 'APIC:' in tags.keys():
            # check if we need to resize it
            
            picturetag = tags['APIC:']
            picturetag.type = 3
            try:
                im = Image.open(BytesIO(picturetag.data))
            except Exception as e:
                print("Invalid APIC entry, removing it: %s" % e)
                mp3file.tags.delall("APIC") # Delete every APIC tag (Cover art)
                mp3file.save()
                return
            
            img_width,img_height = im.size
            if img_width > self.MAX_IMG_WIDTH or img_height > self.MAX_IMG_HEIGHT:
                if args.verbose > 2:
                    print("Resizing from %s to %s" % (im.size, self.MAX_IMG_SZ))
                im.thumbnail(self.MAX_IMG_SZ, Image.LANCZOS)
                im = im.convert('RGB')
                img_bytes = BytesIO()
                im.save(img_bytes, format='JPEG', dpi=self.MAX_DPI,optimize=True, quality=50)
                # rewind it, we need to read it :-D
                img_bytes.seek(0)
                #fname = pathlib.Path(music_file).stem
                #im.save("%s.jpg" % fname, format='JPEG', dpi=self.MAX_DPI, optimize=True, quality=50)

                mp3file.tags.delall("APIC") # Delete every APIC tag (Cover art)
                mp3file.tags["APIC"] = APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3, desc=u'Cover',
                    data=img_bytes.read()
                )
                mp3file.save()        

    def list_dir(self,directory, ext=None):
        items = []

        for path, dirc, files in os.walk(directory):
            for name in files:
                
                if ext and name.lower().endswith(ext):
                    # build the relative path in this platform
                    full_fname =  os.path.sep.join([path] + [name])
                    local_fname = pathlib.Path(full_fname).relative_to(directory)
                    items.append(local_fname)
                if not ext:
                    full_fname =  os.path.sep.join([path] + [name])
                    local_fname = pathlib.Path(full_fname).relative_to(directory)
                    items.append(local_fname)

        return items
    
    def list_songs(self):
        directory = self.jam_music_dir()
        return self.list_dir(directory, self.extensions)

    def list_playlists(self, playlist=None):
        if not playlist:
            directory = self.jam_playlist_dir()
            return self.list_dir(directory)
        
        target = self.jam_playlist_dir(playlist)
        path =  pathlib.Path(target)
        if path.suffix in ('.m3u8', '.m3u'):
            pass
        else:
            target = "%s.m3u" % target
            if not os.path.exists(target):
                target += "8"
                if not os.path.exists(target):
                    raise ValueError("playlist %s doesn't exists: %s" % playlist)
        playlist = self.read_playlist(target)
        items = []
        for i in playlist:
            fname = i['file']
            if fname.find("\\"):
                fname = fname.replace("\\","/")
            items.append(pathlib.Path(fname).name)

        return items
            


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Show data about file and processing", action="count", default=0)
    parser.add_argument("-j", "--jam-root", help="Jam Sport Plus root directory (e.g. /Volumes/SPORT PLUS) or D:\\", default=None)
    subparsers = parser.add_subparsers(dest="subparser_name", help='Command help')

    p_convert = subparsers.add_parser("convert", help="Convert a existing playlist to the new format")
    p_convert.add_argument("playlist", help="Convert from plain dir to hashed one")

    p_process = subparsers.add_parser("process",help="Create the playlist from an existing directory with music (recursive)")
    p_process.add_argument("directory", help="Directory to create the playlist (inside $JAM_ROOT/Music) (use . to create playlist for all the music)")
    p_process.add_argument("playlist", help="Play list name")

    p_migrate = subparsers.add_parser("migrate",help="Migrate a exiting playlist to the jam")
    p_migrate.add_argument("source_playlist", help="Read the playlist from this source")
    p_migrate.add_argument("playlist", help="Store the playlist as <playlist>")



    p_list_songs = subparsers.add_parser("list_songs",help="List available songs in $JAM_ROOT/Music")
    p_list_playlists = subparsers.add_parser("list_playlists",help="List available playlists $JAM_ROOT/Playlists")
    p_list_playlists.add_argument("playlist", help="list also the songs on that playlist", default=None, nargs="?")
    args = parser.parse_args()


    pm = PlayListManager(args.verbose)
    args.jam_root = pm.check_platform(args.jam_root)
    if not args.jam_root or not os.path.exists(args.jam_root):
        raise ValueError("please set a valid --jam-root directory: %s" % args.jam_root)

    print(args)
    if args.subparser_name == "convert":
        print("converting ")
        sys.exit(0)

    if args.subparser_name == "process":
        # create a playlist in the directory pm.jam_root/Music/args.directory`
        playlist_data = pm.build_playlist_from_directory(args.directory)
        pm.store_playlist(playlist_data, args.playlist, format='m3u')
        sys.exit(0)

    if args.subparser_name == "migrate":
        # migrate a current existing playlist to the jam, moving the music, and creating the playlist.
        playlist_data = pm.read_playlist(args.source_playlist)
        pm.migrate_playlist(playlist_data, args.playlist, args.source_playlist)
        sys.exit(0)

    if args.subparser_name == "list_songs":
        # migrate a current existing playlist to the jam, moving the music, and creating the playlist.
        songs = pm.list_songs()
        for s in songs:
            print("%s" % s)
        print("Total: %d songs" % len(songs))
        sys.exit(0)

    if args.subparser_name == "list_playlists":
        # migrate a current existing playlist to the jam, moving the music, and creating the playlist.
        playlists = pm.list_playlists(args.playlist)
        for p in playlists:
            print("%s" % p)
        if not args.playlist:
            print("Total: %d playlists" % len(playlists))
        else:
            print("Total: %d songs in '%s' playlist" % (len(playlists),args.playlist))
        sys.exit(0)


