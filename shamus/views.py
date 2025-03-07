import json
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from .utils import numstr_list_to_int
from .logic import (get_catalogue_contents, store_track, create_album_zip)
from .models import Artist, Track, Album
from .forms import UploadFileForm, AddArtistForm, AddAlbumForm, AddTrackForm


def render_block_template(request, mdl: Artist | Album | Track | None,
                          mdl_id: int | None, tpl: str, get_rd):
    mdl_instance = None
    if mdl:
        try:
            mdl_instance = mdl.used.get(id=mdl_id)
        except mdl.DoesNotExist:
            return redirect('/')

    render_data = get_rd(mdl_instance)

    if not request.META.get('HTTP_X_SHAMUS'):
        render_data['tpl'] = (render(request, tpl, render_data)
                              .content.decode('utf-8'))
        tpl = 'index.html'

    return render(request, tpl, render_data)


@login_required
def catalogue(request):
    tpl = 'blocks/catalogue.html'

    def get_rd(_):
        ret = get_catalogue_contents()
        ret.update({'title': 'Каталог'})

        return ret

    return render_block_template(request, None, None, tpl, get_rd)


@login_required
def catalogue_by_first_symbol(request, symbol):
    tpl = 'blocks/catalogue_page.html'

    def get_rd(_):
        return {
            'title': f'Исполнители на "{symbol.upper()}"',
            'artists': (Artist.used.filter(title__startswith=symbol)
                        .order_by('title')),
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

    render_data = {'title': f'Загрузка Треков в {dst}'}

    if request.POST:
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            render_data['upload_result'] = []

            for f in form.cleaned_data['file_field']:
                render_data['upload_result'].append(
                        (f._name, store_track(f, dst)))
    else:
        form = UploadFileForm()

    render_data['form'] = form
    render_data['dst_cls'] = dst.__class__.__name__.lower()
    render_data['dst_instance'] = dst

    return render(request, 'tabs/upload.html', render_data)


@login_required
def add_artist(request):
    render_data = {'title': 'Добавление Исполнителя'}

    if request.POST:
        if request.POST.get('artist_repeat_allow'):
            form = AddArtistForm(request.POST, is_title_repeat_allowed=True)
        else:
            form = AddArtistForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect('/')
    else:
        form = AddArtistForm()

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

    render_data = {'title': f'Редактирование Исполнителя "{artist.title}"'}

    if request.POST:
        form = AddArtistForm(request.POST, instance=artist)

        if form.is_valid():
            form.save()

            return redirect(reverse('artist-view', args=(artist.id, )))
    else:
        form = AddArtistForm(instance=artist) 

    render_data['form'] = form
    tpl = 'tabs/artist_form.html'

    return render(request, tpl, render_data)


@login_required
def add_album(request, artist_id=None):
    render_data = {'title': f'Добавление Альбома'}

    artist = None
    if artist_id:
        try:
            artist = Artist.used.get(id=artist_id)
            render_data['artist'] = artist
        except Artist.DoesNotExist:
            pass

    if request.POST:
        form = AddAlbumForm(request.POST)

        if form.is_valid():
            album = form.save()

            return redirect(reverse('album-view', args=(album.id, )))
    else:
        form = AddAlbumForm(
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
        form = AddAlbumForm(request.POST, instance=album)

        if form.is_valid():
            form.save()

            return redirect(reverse('album-view', args=(album.id, )))
    else:
        form = AddAlbumForm(instance=album)

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

        form = AddTrackForm(
                request.POST, instance=track, 
                initial={'artist': Artist.used.filter(id__in=artist_ids)})

        if form.is_valid():
            form.save()

            return redirect('/')
    else:
        form = AddTrackForm(instance=track, 
                            initial={'artist': track.artist.all()})

    render_data = {'title': 'Редактирование сведений о Треке',
                   'form': form, 'track': track}

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
            open(instance.path, 'rb'),
            as_attachment=True,
            filename=instance.get_full_name(with_ext=True) or 'test.mp3')
    elif source == 'album':
        return FileResponse(create_album_zip(instance),
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
def last_uploaded(request):
    def get_rd(_):
        ret = {'tracks': Track.used.all().order_by('-id')[:100]}

        return ret

    return render_block_template(request, None, None,
                                 'blocks/last_uploaded.html', get_rd)
