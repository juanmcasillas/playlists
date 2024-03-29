# playlists
Manage Playlists from itunes to migrate them to the sandisk jam (m3u8 format)

## Introduction
Currently, create a playlist from directory and migrate itunes playlists to sandisk's jam directory format is implemented. You can check the [web page](https://support-es.wd.com/app/products/product-detailweb/p/8724) for more
details [the manual](https://downloads.sandisk.com/downloads/um/clipsportplus-um-es.pdf) and some support if needed.

* [how to upgrade to 1.01 and BT 202](https://support-en.wd.com/app/answers/detailweb/a_id/49379s) (by default)
* [Stuck on refreshing media?](https://forums.sandisk.com/t/stuck-on-refreshing-your-media/207491)


## deps

```
python3 -m pip install mutagen
python3 -m pip install m3u8
python3 -m pip install PILLOW
```

### Playlist format and details

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