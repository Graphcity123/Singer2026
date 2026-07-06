import time
import random
import json
from .fetcher import fetch
from .fetcher import fetch_image
from .parser import parse_cd
from .parser import parse_songlist
from .parser import parse_data
from .parser import parse_lyric
from .parser import parse_singer_intro
from .parser import parse_singer
from .storage import storage_data
from .storage import storage_image
from .storage import include_data
from .storage import transform_data
from ..consts import LEAST_SINGER
from ..consts import LEAST_SONG

SINGERS=LEAST_SINGER
SONGS=LEAST_SONG
song_data=[{}]
singer_data=[{}]
singer_dict={}

def Sleep():
    time.sleep(random.uniform(1,2))

# 建立歌单 ID 列表
def build_cdlist():
    all_list=[]
    for cnt in range(35,200,35):
        print("正在获取第 %d 组歌单" %(cnt//35))
        html="https://music.163.com/api/playlist/list?cat=华语&limit=35&offset="+str(cnt)
        cd_html=fetch(html)
        cd_list=parse_cd(cd_html)
        for item in cd_list:
            all_list.append(item)
        Sleep()
    return all_list

# 建立歌曲 ID 列表
def build_songlist(prelist,cdlist):
    all_list={}
    for song in prelist:
        all_list[song]=1
    for cd in cdlist:
        print("正在解析歌单: %d" %(cd))
        html="https://music.163.com/api/v6/playlist/detail?id="+str(cd)
        item=fetch(html)
        songlist=parse_songlist(item)
        for song in songlist:
            all_list[song]=1
        Sleep()
        print(len(all_list))
        if(len(all_list)>SONGS):
            break
    return list(all_list.keys())

# 根据歌手列表添加歌曲
def build_songlist_by_singer():
    singer_ids=[]
    song_ids=set()

    # 添加男歌手
    html="https://music.163.com/api/artist/list?categoryCode=1001&limit=100&offset=0"
    singer_json=fetch(html)
    singers=json.loads(singer_json)
    for singer in singers["artists"]:
        singer_ids.append(singer["id"])
    Sleep()
    
    # 添加女歌手
    html="https://music.163.com/api/artist/list?categoryCode=1002&limit=100&offset=0"
    singer_json=fetch(html)
    singers=json.loads(singer_json)
    for singer in singers["artists"]:
        singer_ids.append(singer["id"])
    Sleep()

    random.shuffle(singer_ids)
    singer_ids=[12487174,61831313,34477557]+singer_ids # 小彩蛋, 把 HOYO-MiX,知更鸟,Chilichill 加进去
    
    # 添加代表作
    for id in singer_ids:
        html="https://music.163.com/api/artist/"+str(id)
        song_json=fetch(html)
        songs=json.loads(song_json)
        Sleep()
        print("正在添加"+songs["artist"]["name"]+"的代表作")
        songsize=len(songs["hotSongs"])
        randsize=random.randint(min(songsize,8),min(songsize,11))
        for song in songs["hotSongs"]:
            randsize-=1
            song_ids.add(song["id"])
            if(randsize==0):
                break
        if(len(song_ids)>SONGS-100):
            break
    return list(song_ids)

# 建立歌曲数据
def build_songs(songs):
    print("正在获取歌曲数据: "+','.join(map(str,songs)))
    html="https://music.163.com/api/song/detail?ids=["+','.join(map(str,songs))+']'
    item=fetch(html)
    Sleep()
    return parse_data(item)

# 建立歌词数据
def build_lyrics(song_id):
    print("正在建立歌词数据: "+str(song_id))
    html="https://music.163.com/api/song/lyric?id="+str(song_id)+"&lv=-1&kv=-1&tv=-1"
    item=fetch(html)
    lyric=json.loads(item)
    Sleep()
    lrc=lyric.get("lrc")
    if(lrc is None or lrc.get("lyric") is None):
        return ["纯音乐，请欣赏"]
    return parse_lyric(lrc["lyric"])

# 对数据重新标号
def rebuild_data():
    for cnt in range(1,len(song_data)):
            song_data[cnt]["id"]=cnt
    index=0

    # 根据歌曲建立对应的歌手库
    for song in song_data:
        if(not song):
            continue
        for id in song["singer_id"]:
            if(id not in singer_dict):
                index+=1
                singer_data.append({"id":id})
                singer_dict[id]=index
    for cnt in range(1,len(song_data)):
        old_ids=song_data[cnt]["singer_id"]
        new_ids=[]
        for id in old_ids:
            new_ids.append(singer_dict[id])
        song_data[cnt]["singer_id"]=new_ids
    
    # 给歌手添加对应的歌曲
    for cnt in range(1,len(singer_data)):
        singer_data[cnt]["song_id"]=[]
    for song in song_data:
        if(not song):
            continue
        for id in song["singer_id"]:
            singer_data[id]["song_id"].append(song["id"])

# 建立歌手数据
def build_singers():
    for id in range(1,len(singer_data)):
        if(singer_data[id]["id"]==0): # 特殊处理无名歌手
            singer_data[id]["id"]=id
            singer_data[id]["desc"]="该歌手在网易云上无页面, 故无简介"
            singer_data[id]["name"]="南久"
            singer_data[id]["source_url"]="https://music.163.com"
            singer_data[id]["image_url"]="https://p2.music.126.net/0KcMYyKmWR-6eCkR8znePw==/18198016951567516.jpg"
            continue

        # 处理歌手简介
        html="https://music.163.com/api/artist/introduction?id="+str(singer_data[id]["id"])
        item=fetch(html)
        singer_data[id]["desc"]=parse_singer_intro(item)
        Sleep()

        # 处理其它相关信息
        html="https://music.163.com/api/artist/"+str(singer_data[id]["id"])
        item=fetch(html)
        data=parse_singer(item)
        for key,value in data.items():
            singer_data[id][key]=value
        Sleep()
        singer_data[id]["id"]=id

        print("正在处理第 %d 位歌手: %s" %(id,singer_data[id]["name"]))

        # 处理图片
        html=singer_data[id]["image_url"]
        item=fetch_image(html)
        storage_image(item,"singer"+str(id)+".jpg")
        Sleep()

        if(id%200==0):
            storage_data(singer_data,song_data)
    
    storage_data(singer_data,song_data)
    # 处理歌曲图片
    for id in range(1,len(song_data)):
        print("正在处理第 %d 首歌图片: %s" %(id,song_data[id]["name"]))
        html=song_data[id]["image_url"]
        item=fetch_image(html)
        storage_image(item,"song"+str(id)+".jpg")
        Sleep()

def main():
    cd_list=build_cdlist()
    songlist=build_songlist(build_songlist_by_singer(),cd_list)
    data=[]
    for ids in range(0,len(songlist),10):
        data+=build_songs(songlist[ids:ids+10])
    data=data[:SONGS]
    for item in data:
        song=item
        song["lyrics"]=build_lyrics(item["id"])
        song_data.append(song)
    rebuild_data()
    storage_data(singer_data,song_data)
    build_singers()
    storage_data(singer_data,song_data)

singer_data,song_data=include_data()
# main()
transform_data(singer_data,song_data)