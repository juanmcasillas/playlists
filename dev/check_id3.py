##!/usr/bin/env bash
# -*- coding: utf-8 -*-

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


def check_artwork(music_file):
    # change image things.
    mp3file = MP3(music_file, ID3=ID3)
    tags = mp3file.tags
    print("----", music_file)
    print(tags.pprint())

    if 'APIC:' in tags.keys():
        # check if we need to resize it
        
        picturetag = tags['APIC:']
        im = Image.open(BytesIO(picturetag.data))
        print(im.size)
    

if __name__ == "__main__":
    check_artwork(sys.argv[1])