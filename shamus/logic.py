import os
from io import BytesIO
from django.conf import settings
from django.core.files import File
from .utils import (store_uploaded_file, get_md5_hexdigest,
                    construct_album_folder_name, create_zip_arch, is_mp3_ext)
from .models import Track, Artist, Album


def construct_artist_folder_path(title: str) -> str:
    return os.path.join(settings.MEDIA_ROOT, title[0], title)


def prepare_artist_folder(title: str) -> str:
    path = construct_artist_folder_path(title)
    if not os.path.isdir(path):
        os.makedirs(path)

    return path


def prepare_album_folder(artists: list[str], album_title: str,
                         album_year: int) -> str:
    catalogue_folder = os.path.join(
            settings.MEDIA_ROOT, artists[0][0], artists[0],
            construct_album_folder_name(artists, album_title, album_year))

    if not os.path.exists(catalogue_folder):
        os.makedirs(catalogue_folder)

    for artist in artists[1:]:
        symfolder = os.path.join(
                settings.MEDIA_ROOT, artist[0], artist,
                construct_album_folder_name([artist], album_title, album_year))
        if not os.path.exists(symfolder):
            os.symlink(catalogue_folder, symfolder, target_is_directory=True) 

    return catalogue_folder


def get_catalogue_contents():
    ret = {
        'catalogue_symbols': [chr(n) for n in range(ord('А'), ord('Я') + 1)] +
                             [chr(n) for n in range(ord('A'), ord('Z') + 1)] +
                             [str(n) for n in range(0, 9 + 1)] + ['!#@'],
        'default_artists': Artist.used.filter(id__in=(1, 2)),
        }

    ret['catalogue_symbols'].insert(6, chr(ord('Ё')))

    return ret


def store_track(file_object, mode_mdl):
    if mode_mdl.__class__.__name__ == 'Artist':
        dst_folder = prepare_artist_folder(mode_mdl.title)
        track_artist = mode_mdl.__class__.used.filter(id=mode_mdl.id)
    elif mode_mdl.__class__.__name__ == 'Album':
        dst_folder = prepare_album_folder(
            mode_mdl.artist.all().values_list('title', flat=True),
            mode_mdl.title,
            mode_mdl.year) 
        track_artist = mode_mdl.artist.all()
    else:
        raise NotImplementedError
    
    file_hash = get_md5_hexdigest(file_object.file.file)

    track_by_hash = Track.used.filter(file_hash=file_hash)
    if track_by_hash.count():
        return track_by_hash.first()

    if store_uploaded_file(file_object, dst_folder):
        track = Track(
                title='',
                file_hash=file_hash,
                path=os.path.join(
                    dst_folder.replace(str(settings.MEDIA_ROOT),
                                       settings.MEDIA_URL[1:-1]),
                    file_object._name))
        track.save()
        track.artist.set(track_artist)

        if mode_mdl.__class__.__name__ == 'Album':
            mode_mdl.track.add(track)

        return True

    return False


def create_album_zip(album: Album) -> BytesIO:
    return create_zip_arch(album.get_full_path())


def folder_to_shamus(path: str):
    if not os.path.isdir(path):
        raise ValueError(f'Path {path} is not folder!')

    mp3_files = []
    for fname in os.listdir(path):
        if is_mp3_ext(fname):
            mp3_files.append(fname)
    mp3_files.sort()
    print('Founded tracks:')
    for mp3f in mp3_files:
        print(f'\t{mp3f}')

    artist_user = input('Print Artist name: ')
    try:
        artist = Artist.used.get(title=artist_user)
    except Artist.DoesNotExist:
        print(f'Artist {artist_user} not created yet. Create it before!')
        return

    album_user = input('Print Album name: ')
    try:
        album = Album.used.get(title=album_user)
        if album.track.all().count() < -1:
            print(f'Album {album_user} already created!')
            return
    except Album.DoesNotExist:
        album_year_user = input('Print Album year: ')
        try:
            album_year = int(album_year_user.strip())
        except ValueError:
            print(f'Enter a year in YYYY format!')
            return
        
        album = Album(title=album_user, year=album_year)
        album.save()
        album.artist.add(artist)

    for mp3f in mp3_files:
        with open(os.path.join(path, mp3f), 'rb') as mp3fo:
            # simulate uploading file from django
            mp3djf = File(mp3fo, name=mp3f)
            setattr(mp3djf, '_name', mp3djf.name)
            setattr(mp3djf.file, 'file', mp3djf)
            store_res = store_track(mp3djf, album)
            print(f'{"+" if store_res else "-"}{mp3f}')
