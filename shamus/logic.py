from io import BytesIO
import os
import re
import random
import shutil
from django.conf import settings
from django.core.files import File
from django.db.models.query import QuerySet
from .utils import (store_uploaded_file, get_md5_hexdigest,
                    escape_path, create_zip_arch, is_mp3_ext)
from .models import Track, Artist, Album, Genre


def construct_artist_folder_path(artist: Artist) -> str:
    """
    Возвращает полный путь для папки Артиста с учётом логики каталога:
    MEDIA_ROOT -> <первый символ наименования> или '_s' -> <наименование>_<id>,
    где "первый символ наименования" всегда в верхнем регистре;
    "наименование" из имени Артиста в каталоге;
    "id" - Artist.id для уникальности имени в случае зачистки всех символов.
    Все символы в "наименование" очищаются через escape_path,
    поэтому остаются только латиница, кириллица, цифры, дефис, скобки и пробел.
    Итоговый размер имени отсекается до MAX_ARTISTPATH_TITLE_LENGTH с учётом
    количества символов под использование "_id".
    """
    folder_name = escape_path(artist.title)
    first_symbol = '_s' if not folder_name else folder_name[0].upper()

    str_id = str(artist.id)
    folder_name = folder_name[:settings.MAX_ARTISTPATH_TITLE_LENGTH-len(str_id)]

    folder_name = f'{folder_name}_{str_id}'

    return os.path.join(settings.MEDIA_ROOT, first_symbol, folder_name)


def prepare_artist_folder(artist: Artist) -> tuple[str, int]:
    """
    Создаёт, если ещё не создана, папку для Артиста на диске,
    возвращает путь до папки и результат ret_code.
    Коды возврата: -1 - ошибка; 0 - создано; 1- существовало.
    """
    ret_code = -1

    path = construct_artist_folder_path(artist)
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
            ret_code = 0
        except OSError as e:
            print(e)
    else:
        ret_code = 1

    return path, ret_code


def construct_album_folder_path(album: Album) -> str:
    """
    Возвращает полный путь для папки Альбома с учётом логики каталога:
    MEDIA_ROOT -> <первый символ наименования Артиста> или '_s' ->
    <наименование Артиста>_<id> -> <наименование Альбома_<id>,
    где вся часть до последнего элемента формируется в
    construct_artist_folder_path по имени первого Артиста из аргументов;
    "id" - Album.id для уникальности имени в случае зачистки всех символов.
    Все символы в "наименование Альбома" очищаются через escape_path,
    поэтому остаются только латиница, кириллица, цифры, дефис, скобки и пробел.
    Итоговый размер имени отсекается до MAX_ALBUMPATH_TITLE_LENGTH с учётом
    количества символов под использование "_id".
    """
    artist_path = construct_artist_folder_path(album.artist.all()[0])

    str_id = str(album.id)
    folder_name = escape_path(str(album))[
                  :settings.MAX_ALBUMPATH_TITLE_LENGTH-len(str_id)]

    folder_name = f'{folder_name}_{str_id}'

    return os.path.join(artist_path, folder_name)


def prepare_album_folder(album: Album) -> tuple[tuple[str], int]:
    """
    Создаёт, если ещё не создана, папку для Альбома на диске, после чего создаёт
    на неё симлинки, если Артистов больше одного.
    Возвращает список со списками, в которых содержатся пути и ret_code.
    Коды возврата: -1 - ошибка; 0 - создано; 1 - существует; 2 - ошибка ссылок.
    """
    catalogue_folder = construct_album_folder_path(album)
    ret = (catalogue_folder, )
    ret_code = -1

    if not os.path.exists(catalogue_folder):
        try:
            os.makedirs(catalogue_folder)
        except OSError as e:
            ret_code = -1
            print(e)

        try:
            artists = album.artist.all()[1:]
            for artist in artists:
                album.artist = artist
                symfolder = construct_album_folder_path(album)
                ret += (symfolder, )

                if not os.path.exists(symfolder):
                    os.symlink(catalogue_folder, symfolder,
                               target_is_directory=True)
        except OSError as e:
            ret_code = 2
            print(e)
    else:
        ret_code = 1

    return ret, ret_code


def get_catalogue_contents():
    ret = {
        'catalogue_symbols': [chr(n) for n in range(ord('А'), ord('Я') + 1)] +
                             [chr(n) for n in range(ord('A'), ord('Z') + 1)] +
                             [str(n) for n in range(0, 9 + 1)] +
                             [settings.UNKNOWN_TITLES_SYMBOLS_SIGN],
        'default_artists': Artist.used.filter(id__in=(1, 2)),
        }

    ret['catalogue_symbols'].insert(6, chr(ord('Ё')))

    return ret


def store_track(file_object, mode_mdl):
    if isinstance(mode_mdl, Artist):
        dst_folder = prepare_artist_folder(mode_mdl)[0]
        track_artist = mode_mdl.__class__.used.filter(id=mode_mdl.id)
    elif isinstance(mode_mdl, Album):
        dst_folder = prepare_album_folder(mode_mdl)[0][0]
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

        if isinstance(mode_mdl, Album):
            mode_mdl.track.add(track)

        return True

    return False


def create_album_zip(album: Album) -> BytesIO:
    return create_zip_arch(construct_album_folder_path(album))


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


def get_disk_space_info_by_path(path: str) -> tuple[int, int, int]:
    total, used, free = 0, 0, 0

    if os.path.exists(path):
        total, used, free = shutil.disk_usage(path)

    return total, used, free


def expected_mp3_file_track_name(track: Track) -> list[str]:
    ret = []

    mp3_name = track.get_file_name()

    if mp3_name.endswith('.mp3'):
        mp3_name = mp3_name[:-4]
    ret.append(mp3_name)

    if ' ' not in mp3_name:
        mp3_name = (mp3_name.replace('-', ' ').replace('+', ' ')
                    .replace('_', ' ').replace('  ', ' '))
    ret.append(mp3_name) if mp3_name not in ret else None

    without_artist_name = mp3_name
    for artist_title in track.artist.all().values_list('title', flat=True):
        if artist_title.lower() in mp3_name.lower():
            without_artist_name = (re.sub(artist_title, '', without_artist_name,
                                          flags=re.IGNORECASE | re.UNICODE)
                                   .strip())

    if without_artist_name != mp3_name:
        mp3_name = without_artist_name.replace('- ', '').strip()
        ret.append(mp3_name) if mp3_name not in ret else None

    idx_num_re = re.search(r'^(\d+(\.|-|\s-\s))(.+?)$', mp3_name)
    if idx_num_re:
        mp3_name = idx_num_re.group(3).strip()
        ret.append(mp3_name) if mp3_name not in ret else None

    if re.search(r'[а-я]|[А-Я]', mp3_name):
        mp3_name = mp3_name.capitalize()
    else:
        mp3_name = mp3_name.title()
    ret.append(mp3_name) if mp3_name not in ret else None

    copy_num_re = re.search(r'^(.+?)\(\d+\)$', mp3_name)
    if copy_num_re:
        mp3_name = copy_num_re.group(1).strip()
        ret.append(mp3_name) if mp3_name not in ret else None

    mp3_name = re.sub(r'\(.+?(\.(com|ru|net|org|club|kz|fm))\)', '',
                      mp3_name, re.IGNORECASE | re.UNICODE)
    ret.append(mp3_name) if mp3_name not in ret else None

    mp3_name = re.sub(r'\s\d+$', '', mp3_name)
    ret.append(mp3_name) if mp3_name not in ret else None

    ret.reverse()

    return ret


def get_shamus_stat(mp3_qnt: bool = True, album_qnt: bool = True,
                    artist_qnt: bool = True, track_titles: bool = True) \
        -> dict:

    stat = {}

    if mp3_qnt or track_titles:
        stat['mp3_qnt'] = Track.used.all().count()

    if album_qnt:
        stat['album_qnt'] = Album.used.all().count()

    if artist_qnt:
        stat['artist_qnt'] = Artist.used.all().count()

    if track_titles:
        stat['track_with_title'] = Track.used.filter(title__gt='').count()
        stat['track_without_title'] = stat['mp3_qnt'] - stat['track_with_title']

    return stat


def get_genre_stat(include_empty=True):
    ret = {}

    for album in Album.used.all():
        for genre in album.genre.all():
            if genre.title not in ret:
                ret[genre.title] = 0

            ret[genre.title] += 1

    if include_empty:
        for genre in (Genre.used.all().exclude(title__in=ret.keys())
                      .values_list('title', flat=True)):
            ret[genre] = 0

    return ret


def get_random_track(data_format: str ='python_dict') -> Track | None:
    tracks_qnt = Track.used.all().count()
    search_repeat_max = tracks_qnt / 3
    search_repeat_cnt = 0

    while search_repeat_cnt < search_repeat_max:
        try:
            track = Track.used.get(id=random.randint(1, tracks_qnt + 1))

            return track.get_track_player_data(data_format=data_format)
        except Track.DoesNotExist:
            search_repeat_cnt += 1

    return None


def set_albums_for_track_qs(track_qs: QuerySet[Track]):
    track_album = dict(zip(track_qs.values_list('id', flat=True),
                          [None] * track_qs.count()))

    for track in track_qs:
        if track_album[track.id] is None:
            track_album[track.id] = track.get_track_album()

        if track_album[track.id]:
            for album_track_id in (track_album[track.id].track.all()
                    .values_list('id', flat=True)):
                if album_track_id in track_album:
                    track_album[album_track_id] = track_album[track.id]

    for track in track_qs:
        setattr(track, 'in_album', track_album[track.id])
