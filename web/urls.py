"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from web import views

urlpatterns = [
    path("", views.index, name="index"),
    path("singer/<int:singer_id>", views.singer, name="singer"),
    path("song/<int:song_id>", views.song, name="song"),
    path("songlist", views.songlist, name="songlist"),
    path("singerlist", views.singerlist, name="singerlist"),
    path("search", views.search_view, name="search"),
    path("comment/<int:comment_id>/like", views.like_comment, name="like_comment"),
    path("comment/<int:comment_id>/delete", views.delete_comment, name="delete_comment"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("manage/users/", views.admin_users, name="admin_users"),
    path("song/<int:song_id>/favorite", views.favorite_song, name="favorite_song"),
    path("singer/<int:singer_id>/favorite", views.favorite_singer, name="favorite_singer"),
    path("analysis", views.analysis_view, name="analysis"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
