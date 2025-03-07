from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
import shamus.views as views


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('login/', auth_views.LoginView.as_view(next_page='catalogue'),
         name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', RedirectView.as_view(url='catalogue'), name='main-page'),
    path('catalogue', views.catalogue, name='catalogue'),
    re_path(r'upload/(?P<dst>artist|album)/(?P<dst_id>\d+)/$', views.upload,
            name='upload'),
    re_path(r'^fs/(?P<symbol>[0-9]|[а-я]|[a-z]|[А-Я]|[A-Z]|Ё|\!\#\@)/$',
            views.catalogue_by_first_symbol,
            name='catalogue-page-first-symbol'),
    path('artist/add/', views.add_artist, name='artist-add'),
    re_path(r'^artist/(?P<artist_id>\d+)/$', views.view_artist,
            name='artist-view'),
    re_path(r'artist/(?P<artist_id>\d+)/edit/$', views.edit_artist,
            name='artist-edit'),
    re_path(r'^artist/(?P<artist_id>\d+)/album/add/$', views.add_album,
            name='artist-add-album'),
    re_path(r'^album/(?P<album_id>\d+)/$', views.view_album,
            name='album-view'),
    re_path(r'^album/(?P<album_id>\d+)/edit/$', views.edit_album,
            name='album-edit'),
    # re_path(r'^playlist/(?P<playlist_id>\d+)/manage/$',
    #         views.manage_playlist, name='playlist-manage'),
    # re_path(r'playlist/(?P<mode>(my|common))/$', views.view_playlists,
    #         name='playlists-view'),
    re_path(r'track/(?P<track_id>\d+)/edit/$', views.edit_track,
            name='track-edit'),
    path('track/setduration', views.edit_track_duration_from_player,
         name='track-set-duration'),
    re_path(r'download/(?P<source>track|album)/(?P<source_id>\d+)/$',
            views.download, name='download'),
    path('search/field', views.search_field, name='search-field'),
    path('last', views.last_uploaded, name='last-uploaded')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
