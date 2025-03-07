# Generated by Django 4.1.3 on 2025-03-06 03:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import pathlib


def create_untitled_artist(apps, schema_editor):
    Artist = apps.get_model("shamus", "Artist")
    Artist.objects.using(schema_editor.connection.alias).bulk_create(
        [Artist(title='Untitled Artist'), Artist(title='Сборник')])


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(blank=True)),
                ('title', models.CharField(max_length=512, verbose_name='Исполнитель')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditLogModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(blank=True)),
                ('desc', models.TextField(verbose_name='Описание')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Track',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(blank=True)),
                ('title', models.CharField(blank=True, max_length=512, verbose_name='Название')),
                ('file_hash', models.CharField(max_length=32, verbose_name='md5')),
                ('path', models.FilePathField(match='*.mp3', max_length=1000, path=pathlib.PureWindowsPath('C:/Users/r/PycharmProjects/shamus/media'), verbose_name='Путь на диске')),
                ('duration', models.PositiveIntegerField(blank=True, null=True, verbose_name='Длительность')),
                ('is_forbiden', models.BooleanField(blank=True, null=True, verbose_name='Запрещено')),
                ('is_explicit', models.BooleanField(blank=True, null=True, verbose_name='Откровенная лексика')),
                ('artist', models.ManyToManyField(to='shamus.artist', verbose_name='Исполнитель')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(blank=True)),
                ('is_common', models.BooleanField(default=False, null=True, verbose_name='Виден другим')),
                ('track', models.ManyToManyField(blank=True, to='shamus.track', verbose_name='Трек')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(blank=True)),
                ('title', models.CharField(max_length=512, verbose_name='Название')),
                ('year', models.PositiveSmallIntegerField(verbose_name='Год')),
                ('track_order', models.TextField(blank=True, verbose_name='Порядок Треков')),
                ('artist', models.ManyToManyField(to='shamus.artist', verbose_name='Исполнитель')),
                ('track', models.ManyToManyField(blank=True, to='shamus.track', verbose_name='Трек')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RunPython(create_untitled_artist)
    ]
