import time
import re
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
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
        "desc": singer.desc.strip(),
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
    true_id =int(re.search(r"id=(\d+)",song.source_url).group(1))
    context = {
        "name": song.name,
        "id": song.id,
        "true_id": true_id,
        "singerlist": song.singers.all(),
        "lyrics_lines": lyrics_text.split("\n") if lyrics_text else [],
        "lyrics_cols": lyrics_cols,
        "source_url": song.source_url,
        "commentlist": song.comments.all(),
        "total_comments": song.comments.count()
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

def search_view(request):
    """
    搜索栏。
    优先级：歌手:名称>简介；歌曲:歌名>歌手名>歌词。
    分页：歌手 25/页，歌曲 20/页，tab 切换。
    """
    query = request.GET.get('q', '').strip()
    tab = request.GET.get('tab', 'singer')
    singers = Singer.objects.none()
    songs = Song.objects.none()
    singer_page = None
    song_page = None
    elapsed = 0
    total_singers = 0
    total_songs = 0

    if query:
        t0 = time.perf_counter()
        singers = Singer.objects.filter(
            Q(name__icontains=query) | Q(desc__icontains=query)
        ).annotate(
            priority=Case(
                When(name__icontains=query, then=Value(1)),
                When(desc__icontains=query, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('priority', 'name').distinct()

        songs = Song.objects.filter(
            Q(name__icontains=query)
            | Q(singers__name__icontains=query)
            | Q(lyrics__icontains=query)
        ).annotate(
            priority=Case(
                When(name__icontains=query, then=Value(1)),
                When(singers__name__icontains=query, then=Value(2)),
                When(lyrics__icontains=query, then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        ).order_by('priority', 'name').distinct()

        elapsed = (time.perf_counter() - t0) * 1000  # ms

        total_singers = singers.count()
        total_songs = songs.count()

        # Paginate based on active tab
        if tab == 'song':
            song_paginator = Paginator(songs, 20)
            song_page = song_paginator.get_page(request.GET.get('page', 1))
        else:
            singer_paginator = Paginator(singers, 25)
            singer_page = singer_paginator.get_page(request.GET.get('page', 1))

    context = {
        'query': query,
        'elapsed': elapsed,
        'tab': tab,
        'singer_page': singer_page,
        'song_page': song_page,
        'total_singers': total_singers,
        'total_songs': total_songs,
        'singer_count': total_singers,
        'song_count': total_songs,
    }
    return render(request, 'search_results.html', context)