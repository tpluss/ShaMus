import os
import re
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .utils import (construct_album_folder_name, get_md5_hexdigest,
                    seconds_to_duration_str)


class UsedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class CommonModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(blank=True, default=False)

    objects = models.Manager()

    used = UsedManager()

    def save(self, *args, **kwargs):
        if self.id:
            elm = EditLogModel()
            elm.save()

        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class EditLogModel(CommonModel):
    desc = models.TextField(verbose_name='Описание')


class Track(CommonModel):
    title = models.CharField(verbose_name='Название',
                             blank=True, max_length=512)
 
    artist = models.ManyToManyField(verbose_name='Исполнитель', to='Artist')

    file_hash = models.CharField(verbose_name='md5', max_length=32)

    path = models.FilePathField(
            verbose_name='Путь на диске', path=str(settings.MEDIA_ROOT),
            match='.mp3', recursive=True, allow_files=True, max_length=1000)

    duration = models.PositiveIntegerField(verbose_name='Длительность',
                                           blank=True, null=True)

    is_forbiden = models.BooleanField(verbose_name='Запрещено', blank=True,
                                      default=False)

    is_explicit = models.BooleanField(verbose_name='Откровенная лексика',
                                      blank=True, default=False)

    def get_file_name(self):
        return os.path.basename(self.path)

    def get_full_path(self):
        return os.path.join(str(settings.BASE_DIR), self.path)

    def get_name(self):
        return (getattr(self, 'title', self.get_file_name()) or
                self.get_file_name())

    def get_artists_title(self):
        return ', '.join(self.artist.all().values_list('title', flat=True))

    def get_artists_data(self):
        artists_data = self.artist.all()

        return zip(
            ', '.join(artists_data.values_list('title', flat=True)),
            list(artists_data.values_list('id', flat=True))
        )

    def get_full_name(self, with_ext=True):
        artists = self.get_artists_title()
        ret = f'{artists} - {self.get_name()}'

        if not with_ext and ret.endswith('.mp3'):
            ret = ret[:-4]
        if with_ext and not ret.endswith('.mp3'):
            ret = f'{ret}.mp3'

        return ret

    def get_url(self):
        return '/' + self.path

    def get_duration_min(self):
        if self.duration:
            return seconds_to_duration_str(self.duration)

        return None

    def get_hash(self):
        if self.file_hash:
            return self.file_hash

        self.file_hash = get_md5_hexdigest(self.path)
        self.save()

        return self.get_hash()

    def __str__(self):
        return self.get_full_name(with_ext=False)


class Artist(CommonModel):
    title = models.CharField(verbose_name='Исполнитель', max_length=512)

    def __str__(self):
        return self.title

    def get_unalbumed_tracks(self) -> list[Track]:
        tracks = Track.objects.filter(artist=self)
        album_tracks_id = Album.objects.filter(artist=self).values_list(
            'track__id', flat=True)

        return [track for track in tracks if track.id not in album_tracks_id]

    def get_albums(self, order_by: str = '-year'):
        return Album.used.filter(artist=self.id).order_by(order_by)


class Album(CommonModel):
    title = models.CharField(verbose_name='Название', max_length=512)

    artist = models.ManyToManyField(verbose_name='Исполнитель', to='Artist')

    year = models.PositiveSmallIntegerField(verbose_name='Год')

    track = models.ManyToManyField(verbose_name='Трек',
                                   to='Track', blank=True)

    track_order = models.TextField(verbose_name='Порядок Треков', blank=True)

    def __str__(self):
        artists_name = ', '.join([a.title for a in self.artist.all()])

        return f'{artists_name} - {self.title} ({self.year})'

    def clean(self):
        super().clean()

        if self.track_order:
            if not re.match(r'^(\d{1,5},)+$', self.track_order):
                raise ValidationError('Invalid sequence of track ids!')
            else:
                ordered_tracks_id = self.get_track_order()
                artist_ids = self.artist.all().values_list('id', flat=True)
                artist_tracks_id = (Track.objects.filter(
                    artist__id__in=artist_ids)
                                    .values_list('id', flat=True))

                for tid in ordered_tracks_id:
                    if tid not in artist_tracks_id:
                        raise ValidationError(f'Track id={tid} unknown!')

                self.track.set(Track.objects.filter(id__in=ordered_tracks_id))

    def title_year(self):
        return f'{self.title} ({self.year})'

    def get_full_path(self):
        return construct_album_folder_name(
                self.artist.all().values_list('title', flat=True),
                self.title, self.year, system_path=True)

    def get_ordered_track(self):
        if self.track_order:
            ret = {k: None for k in self.get_track_order()}
            for track in self.track.all():
                ret[track.id] = track

            return list(ret.values())
        else:
            return self.track.all()

    def get_track_order(self):
        return list(map(int, self.track_order.split(',')[:-1]))

    def get_duration(self, mode: str = ''):
        duration = 0

        tracks_duration = self.track.all().values_list('duration', flat=True)

        if mode == 'strict':
            if None in tracks_duration:
                return [None, None]

        for td in tracks_duration:
            if td:
                duration += td

        return [seconds_to_duration_str(duration) if duration else None,
                None in tracks_duration]

    def get_sibling_albums(self):
        siblings = self.artist.all()[0].get_albums(order_by='year')

        sa_ids = list(siblings.values_list('id', flat=True))
        cur_idx = sa_ids.index(self.id)
        prev_alb = siblings[cur_idx-1] if cur_idx > 0 else None
        next_alb = siblings[cur_idx+1] if cur_idx < (len(sa_ids) - 1) else None

        return prev_alb, next_alb


class Playlist(CommonModel):
    user = models.ForeignKey(verbose_name='Пользователь', to=User,
                             on_delete=models.PROTECT)

    track = models.ManyToManyField(verbose_name='Трек', to='Track', blank=True)

    is_common = models.BooleanField(verbose_name='Виден другим', default=False)
