from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from .models import Singer, Song

def index(request):
    """首页重定向到歌曲列表。"""
    return redirect('songlist')

def singer(request, singer_id):
    """
    歌手详情页。
    展示歌手信息（姓名、照片、简介）及其所有歌曲。
    通过标签切换"热门作品"和"艺人介绍"两个面板。
    """
    singer = Singer.objects.get(pk=singer_id)
    context = {
        "name": singer.name,
        "desc": singer.desc,
        "id": singer.id,
        "songlist": singer.songs.all(),
        "source_url": singer.source_url,
    }
    return render(request, "singer.html", context)

def song(request, song_id):
    """
    歌曲详情页。
    展示歌曲信息（歌名、歌手列表、封面图、歌词）。
    """
    song = Song.objects.get(pk=song_id)
    lyrics_text = song.lyrics or ""
    lyrics_len = len(lyrics_text.split("\n"))
    lyrics_cols=(lyrics_len+29)//30
    lyrics_cols=min(5,lyrics_cols)
    context = {
        "name": song.name,
        "id": song.id,
        "singerlist": song.singers.all(),
        "lyrics_lines": lyrics_text.split("\n") if lyrics_text else [],
        "lyrics_cols": lyrics_cols,
        "source_url": song.source_url,
    }
    return render(request, "song.html", context)

def songlist(request):
    """
    歌曲列表页。
    分页展示所有歌曲（每页 20 首），含序号、歌名链接、歌手链接。
    """
    songs = Song.objects.all()
    paginator = Paginator(songs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {
        "songlist": page_obj,
    }
    return render(request, "songlist.html", context)

def singerlist(request):
    """
    歌手列表页。
    网格卡片分页展示所有歌手（每页 25 位），含照片和姓名。
    """
    singers = Singer.objects.all()
    paginator = Paginator(singers, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {
        "singerlist": page_obj,
    }
    return render(request, "singerlist.html", context)
