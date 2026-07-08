import time
import re
import random
from datetime import datetime, date
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Singer, Song, Comment, CommentLike, FavoriteSong, FavoriteSinger, UserProfile

# 随机种子 (每天轮换一次)
DAILY_SEED = int(date.today().strftime('%Y%m%d'))
random.seed(DAILY_SEED)
RANDOM_LIST = [random.randint(1, 1000000000) for _ in range(10000)]

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
    song_paginator = Paginator(singer.songs.order_by('sort_order'), 20)
    song_page = song_paginator.get_page(request.GET.get("page", 1))
    context = {
        "name": singer.name,
        "desc": singer.desc.strip(),
        "id": singer.id,
        "song_page": song_page,
        "source_url": singer.source_url,
        "is_favorited": (
            request.user.is_authenticated
            and FavoriteSinger.objects.filter(user=request.user, singer=singer).exists()
        ),
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

    # 处理评论提交
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            if request.user.is_authenticated:
                user = request.user
                name = "匿名用户" if request.POST.get("anonymous") else request.user.username
            else:
                name = "匿名用户"
                user = None
            Comment.objects.create(
                content=content,
                song=song,
                name=name,
                user=user,
                create_time=datetime.now(),
            )
        return redirect(f"/song/{song.id}#comments")

    context = {
        "name": song.name,
        "id": song.id,
        "true_id": true_id,
        "singerlist": song.singers.all(),
        "lyrics_lines": lyrics_text.split("\n") if lyrics_text else [],
        "lyrics_cols": lyrics_cols,
        "source_url": song.source_url,
        "total_comments": song.comments.count(),
    }
    # 评论分页
    comment_queryset = song.comments.order_by("-like_count","-create_time","-id")
    comment_paginator = Paginator(comment_queryset, 15)
    comment_page = comment_paginator.get_page(request.GET.get("cpage", 1))
    context["commentlist"] = comment_page
    context["comment_page"] = comment_page
    if request.user.is_authenticated:
        liked_ids = set(
            CommentLike.objects.filter(
                user=request.user,
                comment__song=song,
            ).values_list("comment_id", flat=True)
        )
    else:
        liked_ids = set()
    context["liked_ids"] = liked_ids
    context["is_favorited"] = (
        request.user.is_authenticated
        and FavoriteSong.objects.filter(user=request.user, song=song).exists()
    )
    return render(request, "song.html", context)

def like_comment(request, comment_id):
    """点赞/取消点赞。需登录。"""
    if not request.user.is_authenticated:
        return redirect("login")
    comment = get_object_or_404(Comment, pk=comment_id)
    like, created = CommentLike.objects.get_or_create(
        user=request.user, comment=comment
    )
    if not created:
        like.delete()
        comment.like_count -= 1
    else:
        comment.like_count += 1
    comment.save()
    return redirect(f"/song/{comment.song_id}#comments")


def delete_comment(request, comment_id):
    """删除评论。管理员或评论作者可操作。"""
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user.is_superuser or (comment.user and comment.user == request.user):
        song_id = comment.song_id
        comment.delete()
        return redirect(f"/song/{song_id}#comments")
    return redirect(f"/song/{comment.song_id}#comments")


def register_view(request):
    """注册页面"""
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if username and password:
            if User.objects.filter(username=username).exists():
                error = "用户名已存在"
            else:
                user = User.objects.create_user(username=username, password=password)
                login(request, user)
                return redirect("songlist")
        else:
            error = "请填写用户名和密码"
    return render(request, "register.html", {"error": error})


def login_view(request):
    """登录页面"""
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next", "songlist"))
        error = "用户名或密码错误"
    return render(request, "login.html", {"error": error})


def logout_view(request):
    """登出"""
    logout(request)
    return redirect("songlist")


def favorite_song(request, song_id):
    """收藏/取消收藏歌曲。需登录。"""
    if not request.user.is_authenticated:
        return redirect("login")
    song = get_object_or_404(Song, pk=song_id)
    fav, created = FavoriteSong.objects.get_or_create(user=request.user, song=song)
    if not created:
        fav.delete()
    return redirect("song", song_id=song_id)


def favorite_singer(request, singer_id):
    """收藏/取消收藏歌手。需登录。"""
    if not request.user.is_authenticated:
        return redirect("login")
    singer = get_object_or_404(Singer, pk=singer_id)
    fav, created = FavoriteSinger.objects.get_or_create(user=request.user, singer=singer)
    if not created:
        fav.delete()
    return redirect("singer", singer_id=singer_id)


def profile_view(request):
    """个人主页，展示个人信息和收藏的歌曲/歌手（tab 切换）。管理员可通过 ?uid=X 查看他人。"""
    if not request.user.is_authenticated:
        return redirect("login")
    uid = request.GET.get("uid")
    if uid and request.user.is_superuser:
        target_user = get_object_or_404(User, pk=uid)
    else:
        target_user = request.user
    tab = request.GET.get("tab", "song")
    profile = UserProfile.objects.get_or_create(user=target_user)[0]
    fav_songs = FavoriteSong.objects.filter(user=target_user).select_related("song")
    fav_singers = FavoriteSinger.objects.filter(user=target_user).select_related("singer")
    # Get user's recent comments
    user_comments = Comment.objects.filter(user=target_user).order_by("-create_time")[:50]
    context = {
        "tab": tab,
        "profile": profile,
        "profile_user": target_user,
        "fav_songs": fav_songs,
        "fav_singers": fav_singers,
        "user_comments": user_comments,
    }
    return render(request, "profile.html", context)


def admin_users(request):
    """管理员查看所有用户及其活动统计。"""
    if not request.user.is_superuser:
        return redirect("songlist")
    from django.db.models import Count
    users = User.objects.annotate(
        fav_song_count=Count("favoritesong", distinct=True),
        fav_singer_count=Count("favoritesinger", distinct=True),
        comment_count=Count("comment", distinct=True),
    ).order_by("-comment_count")
    return render(request, "admin_users.html", {"users": users})


def profile_edit(request):
    """编辑个人资料（头像和简介）。"""
    if not request.user.is_authenticated:
        return redirect("login")
    profile = UserProfile.objects.get_or_create(user=request.user)[0]
    if request.method == "POST":
        bio = request.POST.get("bio", "").strip()
        profile.bio = bio
        if request.FILES.get("avatar"):
            profile.avatar = request.FILES["avatar"]
        profile.save()
        return redirect("profile")
    return render(request, "profile_edit.html", {"profile": profile})


def songlist(request):
    """
    歌曲列表页。
    分页展示所有歌曲（每页 20 首），含序号、歌名链接、歌手链接。
    每天随机轮换一次。
    """
    songs = list(Song.objects.all())
    songs.sort(key=lambda x: RANDOM_LIST[x.id])
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
    每天随机轮换一次。
    """
    singers = list(Singer.objects.all())
    singers.sort(key=lambda x: RANDOM_LIST[x.id])
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