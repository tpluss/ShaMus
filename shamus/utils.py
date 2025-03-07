import os
import hashlib
from io import BytesIO
from zipfile import ZipFile
from django.conf import settings


def store_uploaded_file(f, dest: str) -> bool:
    try:
        with open(f'{dest}/{f._name}', 'wb+') as fdata:
            for chunk in f.chunks():
                fdata.write(chunk)
    except Exception as e:
        print(e)
        return False

    return True


def calc_md5_chunked(data_descriptor):
    md5 = hashlib.md5()
    
    seek_pos = 0
    chunk = True 
    while chunk:
        chunk = data_descriptor.read(1024000)
        md5.update(chunk)
        seek_pos += 1024000

    return md5.hexdigest()


def get_md5_hexdigest(f_path: str) -> str:
    try:
        if isinstance(f_path, str):
            with open(f_path, 'rb') as fdata:
                return calc_md5_chunked(fdata)
        else:
            return calc_md5_chunked(f_path)
    except Exception as e:
        print('Can\'t calculate md5', e)
        return ''


def list_folder_tree(path, depth=1):
    ret = {path: None}

    if depth == 0:
        ret[path] = os.listdir(path)
    else:
        ret[path] = []
        for f in os.scandir(path):
            if f.is_file():
                ret[path].append(f)
            elif f.is_dir():
                ret[path].append(list_folder_tree(f, depth-1))

    return ret


def numstr_list_to_int(numstr: list[str] | tuple[str]) -> list[int]:
    ret = []

    for _ in numstr:
        try:
            ret.append(int(_))
        except ValueError:
            continue

    return ret


def construct_album_folder_name(artists: list[str],
                                album_title: str, album_year: int,
                                system_path: bool = False) -> str:
    artists_title = ', '.join(artists)
    if system_path:
        tpl = os.path.join(
            settings.MEDIA_ROOT, artists[0][0], artists[0],
            construct_album_folder_name(artists, album_title, album_year))
    else:
        tpl = f'{artists_title} - {album_title} ({album_year})'

    return tpl 


def create_zip_arch(full_path: str) -> BytesIO:
    file_blueprint = BytesIO()
    zip_file = ZipFile(file_blueprint, 'a')

    for filename in os.listdir(full_path):
        try:
            zip_file.write(os.path.join(full_path, filename),
                           arcname=os.path.join(os.path.split(full_path)[-1],
                                                filename))
        except Exception as e:
            print(e)

    zip_file.close()
    file_blueprint.seek(0)

    return file_blueprint


def is_mp3_ext(path: str):
    return path.endswith('.mp3')
