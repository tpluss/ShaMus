import json
import random
from typing import Callable
from urllib import parse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from .utils import numstr_list_to_int
from . import logic
from .models import Artist, Track, Album, Genre
from . import forms


def render_block_template(request,
                          mdl: type[Artist] | type[Album] | type[Track] | None,
                          mdl_id: int | None, tpl: str, get_rd: Callable):
    """
    Возвращает HttpResponse с отрендеренным блоком tpl и нужным контекстом,
    получаемым из get_rd, где get_rd фукнция для формирования контекста,
    переданная при вызове.

    При указании mdl и mdl_id в вызов get_rd передаётся конкретный инстанс
    модели заданного типа.

    Если в заголовке запроса нет флага HTTP_X_SHAMUS, тогда рендер шаблона
    передаётся в виде параметра tpl контекста, а шаблон ответа tpl
    подменяется на главную страницу index.html.
    В противном случае отдаётся ответ с отрендеренным шаблоном tpl, а в куки
    добавляется shamus-title, дублирующий title из контекста, если ключ задан.

    :param request: HttpRequest;
    :param mdl: тип модели;
    :param mdl_id: id для подбора инстанса заданного типа модели;
    :param tpl: путь к шаблону;
    :param get_rd: функция, возвращаюая контекст для рендера.
    """
    mdl_instance = None
    if mdl:
        if not mdl_id:
            raise ValueError('Parameter "mdl_id" expected with "mdl".')
        try:
            mdl_instance = mdl.used.get(id=mdl_id)
        except mdl.DoesNotExist:
            return redirect('/')

    render_data = get_rd(mdl_instance)

    if not request.META.get('HTTP_X_SHAMUS'):
        render_data['tpl'] = (render(request, tpl, render_data)
                              .content.decode('utf-8'))

        # replace '\' char to '\\' sequence for method |safe in template
        render_data['tpl'] = render_data['tpl'].replace('\\', '\\\\')
        render_data['tpl'] = render_data['tpl'].replace('`', '\`')

        tpl = 'index.html'

    resp = render(request, tpl, render_data)
    if 'title' in render_data and request.META.get('HTTP_X_SHAMUS'):
        resp.set_cookie('shamus-title', parse.quote(render_data['title']))

    return resp


@login_required
def catalogue(request):
    tpl = 'blocks/catalogue.html'

    def get_rd(_):
        ret = logic.get_catalogue_contents()
        ret.update({'title': 'Каталог'})

        return ret

    return render_block_template(request, None, None, tpl, get_rd)


@login_required
def catalogue_by_first_symbol(request, symbol):
    tpl = 'blocks/catalogue_page.html'

    def get_rd(_):
        if symbol != settings.UNKNOWN_TITLES_SYMBOLS_SIGN:
            artist_qs = Artist.used.filter(title__istartswith=symbol)
        else:
            artist_qs = Artist.used.exclude(
                title__iregex=settings.ALLOWED_PATHS_SYMBOLS_RE)

        return {
            'title': f'Исполнители на "{symbol.upper()}"',
            'artists': (artist_qs.order_by('title')),
            'symbol': symbol.upper()}

    return render_block_template(request, None, None, tpl, get_rd)


@login_required
def upload(request, dst, dst_id):
    if dst == 'artist':
        dst_mdl = Artist
    elif dst == 'album':
        dst_mdl = Album
    else:
        raise NotImplementedError

    try:
        dst = dst_mdl.used.get(id=dst_id)
    except dst_mdl.DoesNotExist:
        return redirect('/')

    render_data = dict()
    render_data['title'] = f'Загрузка Треков в {dst}'
    render_data['disk'] = logic.get_disk_space_info_by_path(settings.MEDIA_ROOT)

    if request.POST:
        form = forms.UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            render_data['upload_result'] = []

            for f in form.cleaned_data['file_field']:
                render_data['upload_result'].append(
                        (f._name, logic.store_track(f, dst)))
    else:
        form = forms.UploadFileForm()

    render_data['form'] = form
    render_data['dst_cls'] = dst.__class__.__name__.lower()
    render_data['dst_instance'] = dst

    return render(request, 'tabs/upload.html', render_data)


@login_required
def add_artist(request):
    render_data = dict()
    render_data['title'] = 'Добавление Исполнителя'

    if request.POST:
        if request.POST.get('artist_repeat_allow'):
            form = forms.AddArtistForm(request.POST, is_title_repeat_allowed=True)
        else:
            form = forms.AddArtistForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect('/')
    else:
        form = forms.AddArtistForm()

    render_data['form'] = form

    tpl = 'tabs/artist_form.html'

    return render(request, tpl, render_data)


@login_required
def view_artist(request, artist_id):
    tpl = 'blocks/artist_page.html'

    def get_rd(artist):
        return {
            'title': f'Исполнитель {artist.title}',
            'artist': artist,
            'albums': Album.used.filter(artist=artist).order_by('-year'),
            'tracks': artist.get_unalbumed_tracks()
        }

    return render_block_template(request, Artist, artist_id, tpl, get_rd)


@login_required
def edit_artist(request, artist_id):
    try:
        artist = Artist.used.get(id=artist_id)
    except Artist.DoesNotExist:
        return redirect('/')

    render_data = dict()
    render_data['title'] = f'Редактирование Исполнителя "{artist.title}"'

    if request.POST:
        form = forms.AddArtistForm(request.POST, instance=artist)

        if form.is_valid():
            form.save()

            return redirect(reverse('artist-view', args=(artist.id, )))
    else:
        form = forms.AddArtistForm(instance=artist)

    render_data['form'] = form

    tpl = 'tabs/artist_form.html'

    return render(request, tpl, render_data)


@login_required
def add_album(request, artist_id=None):
    render_data = dict()
    render_data['title'] = f'Добавление Альбома'

    artist = None
    if artist_id:
        try:
            artist = Artist.used.get(id=artist_id)
            render_data['artist'] = artist
        except Artist.DoesNotExist:
            pass

    if request.POST:
        form = forms.AddAlbumForm(request.POST)

        if form.is_valid():
            album = form.save()

            return redirect(reverse('album-view', args=(album.id, )))
    else:
        form = forms.AddAlbumForm(
                initial={'artist': Artist.used.filter(id=artist.id)})

    render_data['form'] = form

    tpl = 'tabs/album_form.html'

    return render(request, tpl, render_data)


@login_required
def view_album(request, album_id):
    def get_rd(album):
        return {'title': f'{album}', 'album': album}

    tpl = 'blocks/album_page.html'

    return render_block_template(request, Album, album_id, tpl, get_rd)


@login_required()
def edit_album(request, album_id):
    try:
        album = Album.used.get(id=album_id)
    except Album.DoesNotExist:
        return redirect('/')

    render_data = {'title': f'Редактирование Альбома {album}',
                   'album': album}

    if request.POST:
        form = forms.AddAlbumForm(request.POST, instance=album)

        if form.is_valid():
            form.save()

            return redirect(reverse('album-view', args=(album.id, )))
    else:
        form = forms.AddAlbumForm(instance=album)

        render_data['album_tracks'] = album.get_ordered_track()
        render_data['unalbumed_tracks'] = []
        for artist in album.artist.all():
            render_data['unalbumed_tracks'] += artist.get_unalbumed_tracks()

    render_data['form'] = form

    tpl = 'tabs/album_form.html'

    return render(request, tpl, render_data)


@login_required
def edit_track(request, track_id):
    try:
        track = Track.used.get(id=track_id)
    except Track.DoesNotExist:
        return redirect('/')

    if request.POST:
        artist_ids = numstr_list_to_int(request.POST.getlist('artist'))

        form = forms.AddTrackForm(
                request.POST, instance=track, 
                initial={'artist': Artist.used.filter(id__in=artist_ids)})

        if form.is_valid():
            form.save()

            return redirect('/')
    else:
        form = forms.AddTrackForm(instance=track,
                            initial={'artist': track.artist.all()})

    render_data = {'title': 'Редактирование сведений о Треке',
                   'form': form, 'track': track}
    render_data['expected_names'] = logic.expected_mp3_file_track_name(
        render_data['track'])

    tpl = 'tabs/track_form.html'

    return render(request, tpl, render_data)


@login_required
def download(_, source, source_id):
    if source == 'track':
        mdl = Track
    elif source == 'album':
        mdl = Album
    else:
        raise NotImplementedError

    try:
        instance = mdl.used.get(id=source_id)
    except mdl.DoesNotExist:
        return redirect('/')

    if source == 'track':
        return FileResponse(
            open(instance.get_full_path(), 'rb'),
            as_attachment=True,
            filename=instance.get_full_name(with_ext=True) or 'test.mp3')
    elif source == 'album':
        return FileResponse(logic.create_album_zip(instance),
                            as_attachment=True,
                            filename=f'{instance.__str__()}.zip')

    raise NotImplementedError()


@login_required
def search_field(request):
    qs_query, qs_mdl = request.GET.get('artist'), Artist
    if not qs_query:
        qs_query, qs_mdl = request.GET.get('album'), Album
    if not qs_query:
        qs_query, qs_mdl = request.GET.get('track'), Track
    if not qs_query:
        qs_query, qs_mdl = request.GET.get('genre'), Genre
    if not qs_query:
        return HttpResponse('unknown model')

    ret = qs_mdl.used.filter(title__icontains=qs_query)

    return HttpResponse(json.dumps({o.id: o.title for o in ret}),
                        content_type='application/json')


@login_required
def edit_track_duration_from_player(request):
    track_id = request.GET.get('id')
    track_duration = request.GET.get('duration')

    if track_id and track_duration:
        try:
            track = Track.used.get(id=track_id)

            track.duration = int(track_duration.split('.')[0])
            track.save()

            return HttpResponse(json.dumps({'duration': track.duration}),
                                content_type='application/json')
        except (Track.DoesNotExist, ValueError, TypeError):
            pass

    return HttpResponse(json.dumps({'duration': None}),
                        content_type='application/json')


@login_required
def last_uploaded(request, mdl: str, qnt: int):
    def create_get_rd():
        rd_opts = {
            'artist': ('artists', Artist, 'Исполнители'),
            'album': ('albums', Album, 'Альбомы'),
            'track': ('tracks', Track, 'Треки')
        }

        def get_rd(_):
            ret = {
                rd_opts[mdl][0]: (rd_opts[mdl][1].used.all()
                    .select_related().order_by('-id')[:int(qnt)]),
                'title': f'Последние {rd_opts[mdl][2]}, {qnt} шт.',
                'entity': rd_opts[mdl][0],
                'form': forms.LastUploadedParameters(
                    initial={'entity': mdl, 'qnt': qnt})
            }

            return ret

        return get_rd

    return render_block_template(request, None, None,
                                 'blocks/last_uploaded.html', create_get_rd())


@login_required
def rename_tracks(request, track_id=None):
    tpl = 'tabs/rename_tracks_form.html'

    render_data = dict()
    render_data['title'] = 'Режим переименования Треков'

    if request.POST:
        if request.POST.get('pass'):
            return redirect(reverse('track-renamer'))

        try:
            track_id = int(request.POST.get('track'))
        except ValueError:
            return redirect(reverse('track-renamer'))

        form = forms.TrackRenamerForm(request.POST, track_id=track_id)

        is_save = (request.POST.get('save_random') or
                   request.POST.get('save_next'))

        if is_save:
            if form.is_valid():
                track = form.cleaned_data['track']
                track.title = form.cleaned_data['title']
                track.save()

                request.POST = request.POST.copy()
                if request.POST.get('save_next'):
                    track_id = (Track.used.filter(id__gt=track.id, title='')
                                .values_list('id', flat=True)[:1])
                    if track_id:
                        track_id = track_id[0]
                        request.POST = {'track': track_id}
                    else:
                        return redirect(reverse('track-renamer'))
                else:
                    request.POST = {}

                return rename_tracks(request)
        else:
            if track_id:
                try:
                    render_data['track'] = Track.used.get(id=track_id)
                except Track.DoesNotExist:
                    return redirect(reverse('track-renamer'))
    else:
        if track_id is None:
            tracks = Track.used.filter(title='')
            if tracks.count():
                track = tracks[random.randint(0, tracks.count() - 1)]
                track_id = track.id
            else:
                return redirect(reverse('track-renamer'))

        try:
            track = Track.used.get(id=track_id)
        except Track.DoesNotExist:
            return redirect(reverse('track-renamer'))

        form = forms.TrackRenamerForm(track_id=track_id)
        render_data['track'] = track

    render_data['form'] = form
    render_data['track_stat'] = logic.get_shamus_stat(album_qnt=False,
                                                      artist_qnt=False)

    if 'track' in render_data:
        render_data['expected_names'] = logic.expected_mp3_file_track_name(
            render_data['track'])

    return render(request, tpl, render_data)


@login_required
def add_genre(request):
    render_data = dict()
    render_data['title'] = 'Добавление Жанра'

    if request.POST:
        form = forms.AddGenreForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect(reverse('genre-list', args=()))
    else:
        form = forms.AddGenreForm()

    render_data['form'] = form

    tpl = 'tabs/genre_form.html'

    return render(request, tpl, render_data)


@login_required()
def edit_genre(request, genre_id):
    try:
        genre = Genre.used.get(id=genre_id)
    except Genre.DoesNotExist:
        return redirect('/')

    render_data = dict()
    render_data['title'] = f'Редактирование Жанра {genre}'

    if request.POST:
        form = forms.AddGenreForm(request.POST, instance=genre)

        if form.is_valid():
            form.save()

            return redirect(reverse('genre-list', args=()))
    else:
        form = forms.AddGenreForm(instance=genre)

    render_data['form'] = form

    tpl = 'tabs/genre_form.html'

    return render(request, tpl, render_data)


@login_required()
def list_genre(request):
    tpl = 'tabs/genre_list.html'

    genres = {genre.title: genre.id for genre in Genre.used.all()}
    genres_data = logic.get_genre_stat()
    for k, v in genres_data.items():
        # genre_id, genre_album_qnt
        genres_data[k] = [genres[k], v]

    render_data = {'title': 'Просмотр Жанров', 'genres_data': genres_data}

    return render(request, tpl, render_data)


@login_required
def catalogue_by_genre(request, genre_id):
    try:
        genre = Genre.used.get(id=genre_id)
    except Genre.DoesNotExist:
        return redirect(reverse('catalogue', args=()))

    tpl = 'blocks/catalogue_page.html'

    def get_rd(_):
        return {
            'title': f'Альбомы в Жанре "{genre.title}"',
            'genre': genre,
            'albums': (Album.used.filter(genre=genre).order_by('title')),
        }

    return render_block_template(request, None, None, tpl, get_rd)


@login_required()
def radio(_):
    track = logic.get_random_track(data_format='json')

    return HttpResponse(track if track else json.dumps({'track': {}}),
                        content_type='application/json')


@login_required
def get_tracklist(_, source: str, source_id: int):
    track_data = []

    try:
        if source == 'album':
            album = Album.used.get(id=source_id)
            track_data += [track.get_track_player_data(track_album=album)
                           for track in album.get_ordered_track()]
        elif source == 'artist':
            artist = Artist.used.get(id=source_id)
            for album in artist.get_albums().order_by('year', 'id'):
                track_data += [track.get_track_player_data(track_album=album)
                               for track in album.get_ordered_track()]
            for track in artist.get_unalbumed_tracks():
                track_data += [track.get_track_player_data(track_album=False)]
        else:
            track_data = []
    except Album.DoesNotExist:
        pass
    except Artist.DoesNotExist:
        pass

    return HttpResponse(json.dumps({'tracklist': track_data}),
                        content_type='application/json')
