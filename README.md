# playlists

Manage Playlists from itunes to migrate them to the sandisk jam (m3u8 format)

## Introduction

Currently, create a playlist from directory and migrate itunes playlists to sandisk's jam directory format is implemented. You can check the [web page](https://support-es.wd.com/app/products/product-detailweb/p/8724) for more
details [the manual](https://downloads.sandisk.com/downloads/um/clipsportplus-um-es.pdf) and some support if needed.

* [how to upgrade to 1.01 and BT 202](https://support-en.wd.com/app/answers/detailweb/a_id/49379s) (by default)
* [Stuck on refreshing media?](https://forums.sandisk.com/t/stuck-on-refreshing-your-media/207491)


## Python dependencies

```
python3 -m pip install mutagen
python3 -m pip install m3u8
python3 -m pip install PILLOW
```

## Playlist format and details

* Ended with `\r\n` (`\0xD\0xA`) if not, it doesn't work. 
* The standard format for sources doesn't work also.
* Playlists are stored in the jam `SPORT PLUS\Playlists` folder
* Music are stored in the jam `SPORT PLUS\Music` folder
* Folders are allowed inside the `Music` folder.
  

For a playlist stored in `SPORT PLUS\Playlists` the file paths are:
```
#EXTM3U
..\Music\01 - Michael McEachern - Easier As Us.mp3
..\Music\Tunguska_Electronic_Music_Society_-_Aquascape_-_Sunrise.mp3
```

## Usage

### General options 

```
% python3.9 gen_playlist_jam.py -v --jam-root dev/CLIP_SPORT --help
usage: gen_playlist_jam.py [-h] [-v] [-j JAM_ROOT] {convert,process,migrate,list_songs,list_playlists} ...

positional arguments:
  {convert,process,migrate,list_songs,list_playlists}
                        Command help
    convert             Convert a existing playlist to the new format
    process             Create the playlist from an existing directory with music (recursive)
    migrate             Migrate a exiting playlist to the jam
    list_songs          List available songs in $JAM_ROOT/Music
    list_playlists      List available playlists $JAM_ROOT/Playlists

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Show data about file and processing
  -j JAM_ROOT, --jam-root JAM_ROOT
                        Jam Sport Plus root directory (e.g. /Volumes/SPORT PLUS) or D:\
```

### Convert

Converts and existing playlist to a hashed one

```
% gen_playlist_jam.py -v --jam-root dev/CLIP_SPORT convert --help
usage: gen_playlist_jam.py convert [-h] playlist

positional arguments:
  playlist    Convert from plain dir to hashed one

optional arguments:
  -h, --help  show this help message and exit
```

### Process

Get a directory, and build a playlist with all the files (recursive) inside

```
% gen_playlist_jam.py -v --jam-root dev/CLIP_SPORT process --help
usage: gen_playlist_jam.py process [-h] directory playlist

positional arguments:
  directory   Directory to create the playlist (inside $JAM_ROOT/Music) (use . to create playlist for all the music)
  playlist    Play list name

optional arguments:
  -h, --help  show this help message and exit
```

### Migrate

Read a playlist from somewhere, copy the files into the device and build the playlist. Now it does hashed

```
% gen_playlist_jam.py -v --jam-root dev/CLIP_SPORT migrate --help
usage: gen_playlist_jam.py migrate [-h] source_playlist playlist

positional arguments:
  source_playlist  Read the playlist from this source
  playlist         Store the playlist as <playlist>

optional arguments:
  -h, --help       show this help message and exit

 python3.9 gen_playlist_jam.py -vvv migrate dev/itunes-mac/list-01.m3u8 list-01
```

### List songs

List all songs in the device

```
% gen_playlist_jam.py -v --jam-root dev/CLIP_SPORT list_songs --help
usage: gen_playlist_jam.py list_songs [-h]

optional arguments:
  -h, --help  show this help message and exit
```

### List playlists

List all playlists in the device. If you specified one, list the songs in that playlist

```
% gen_playlist_jam.py -v --jam-root dev/CLIP_SPORT list_playlists --help
usage: gen_playlist_jam.py list_playlists [-h] [playlist]

positional arguments:
  playlist    list also the songs on that playlist

optional arguments:
  -h, --help  show this help message and exit
```

### How to run (deprecated)
* on mac: `python3.9 gen_playlist_jam.py -vvv  -m dev/itunes-mac/nano.m3u8 nano`
* on windows: `C:\Python312\python.exe gen_playlist_jam.py -vvv -j "E:\\" -m "dev\\itunes-pc\\remix.m3u" remix`

### Warnings

Not support funky dots on paths. So fix it in code.

