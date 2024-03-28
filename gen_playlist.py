##!/usr/bin/env bash
# -*- coding: utf-8 -*-
# /////////////////////////////////////////////////////////////////////////////
# //
# // gen_playlist.py 
# //
# // generates a playlist based on a directory
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
import argparse
import sys
import glob
import os 
import pathlib
import m3u8
import shutil

class PlayListManager:
    def __init__(self, verbose=False):
        self.verbose = verbose

        self.extensions = ('.mp3', )
        self.playlist_formatters = {
            'm3u8': self.gen_m3u8_playlist
        }

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


    def build_playlist_from_directory(self, directory):
        
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
                        'file': local_fname,
                        'path': full_fname,
                        'duration': audio.info.length
                    })
                else:
                    if self.verbose:
                        print("Warning: Unknown file extension for %s, skipping" % name)
        
        return playlist

    def store_playlist(self, playlist, directory, plname, format='m3u8'):
        return self.playlist_formatters[format](playlist, directory, plname)

    def gen_m3u8_playlist(self, playlist, directory, plname):
        
        target = os.path.sep.join([directory, plname])
        path =  pathlib.Path(target)
        if path.suffix in ('.m3u8', '.m3u'):
            pass
        else:
            target = "%s.m3u8" % target
        
        if self.verbose:
            print("generating m3u8 playlist: %s" % target)
        
        with open(target,"w",encoding='utf-8') as fd:
            for item in playlist:
                fd.write("#EXTINF:%d, %s\n" % (item['duration'], item['title']))
                fd.write("%s\n\n" % item['file'])

        return len(playlist)

    def read_playlist(self, directory, playlist_file):
        
        if not os.path.exists(playlist_file):
            raise ValueError("playlist file %s doesn't exists" % playlist_file)
        
        playlist = []
        dir_path = pathlib.Path(directory)
        try:
            data = m3u8.load(playlist_file)
        except Exception as e:
            raise(e)
        
        if data:
            for i in data.segments:
                playlist.append({
                    'title': i.title,
                    'file': i.uri,
                    'path': str(dir_path / pathlib.Path(i.uri)),
                    'duration': i.duration
                })
           
        return playlist

    def migrate_playlist(self, playlist_data, playlist, from_dir=None, to_dir=None):
        if not from_dir or not to_dir or \
            not os.path.exists(from_dir) or \
            not os.path.isdir(from_dir):
                raise ValueError("from_dir & to_dir must be valid directories")
        
        new_playlist = []

        if  not os.path.exists(to_dir):
            os.makedirs(to_dir, exist_ok=True)

        from_dir_path = pathlib.Path(from_dir)
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
                shutil.copyfile(src_file, tgt_file)
            except shutil.SameFileError:
                pass

            item['file'] = str(tgt_file)
            new_playlist.append(item)

        self.gen_m3u8_playlist(new_playlist, to_dir, pathlib.Path(playlist).name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Show data about file and processing", action="count", default=0)
    parser.add_argument("-d", "--directory", help="Directory to read")
    parser.add_argument("-m", "--migrate", help="Directory to migrate (target directory is directory)")
    parser.add_argument("playlist", help="Play list name")
    args = parser.parse_args()

    pm = PlayListManager(args.verbose)

    
    if args.directory and not args.migrate:
        playlist_data = pm.build_playlist_from_directory(args.directory)
        pm.store_playlist(playlist_data, args.directory, args.playlist)

    if args.migrate and args.directory:
        playlist_data = pm.read_playlist(args.migrate, args.playlist)
        pm.migrate_playlist(playlist_data, args.playlist, from_dir=args.migrate, to_dir=args.directory)