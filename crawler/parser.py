from bs4 import BeautifulSoup as BS
import re
import json

# 从排行榜网页中解析歌单 ID
def parse_cd(playlists_json):
    cd_list=[]
    playlists=json.loads(playlists_json)
    for playlist in playlists["playlists"]:
        cd_list.append(playlist["id"])
    return cd_list

# 从歌单网页中解析歌曲 ID
def parse_songlist(songlist_json):
    songlist=[]
    songs=json.loads(songlist_json)
    for song in songs["playlist"]["trackIds"]:
        songlist.append(song["id"])
    return songlist

# 从歌曲网页中解析需要的信息
def parse_data(song_json):
    datas=[]
    
    songs=json.loads(song_json)
    for song in songs["songs"]:
        data={}

        # 爬取歌曲名,歌曲图片,歌曲原始网站url
        data["name"]=song["name"]
        data["id"]=song["id"]
        data["source_url"]="https://music.163.com/#/song?id="+str(song["id"])
        data["image_url"]=song["album"]["picUrl"]

        # 爬取歌手姓名和歌手 ID (可能有多个)
        singers_item=song["artists"]
        names=[]
        ids=[]
        for singer in singers_item:
            names.append(singer["name"])
            ids.append(singer["id"])
        data["singer_name"]=names
        data["singer_id"]=ids

        datas.append(data)

    return datas

# 从歌词文件中筛选出歌词
def parse_lyric(lyric_data):
    lyric_list=[]
    lyrics=re.split(r'\[\d+:\d+\.\d+\]',lyric_data)
    for lyric_line in lyrics:
        lyric=lyric_line.strip()
        # if(lyric=="" or re.search(r'[:：]',lyric)):
        if(lyric==""):
            continue
        lyric_list.append(lyric)
    return lyric_list

# 从歌手文件中筛选歌手介绍
def parse_singer_intro(singer_json):
    data=json.loads(singer_json)
    return data["briefDesc"]

# 从歌手文件中筛选歌手其余信息
def parse_singer(singer_json):
    singer=json.loads(singer_json)
    data={}
    data["name"]=singer["artist"]["name"]
    data["source_url"]="https://music.163.com/#/artist/desc?id="+str(singer["artist"]["id"])
    data["image_url"]=singer["artist"]["picUrl"]
    return data