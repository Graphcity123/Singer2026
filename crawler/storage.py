import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IMG_DIR = Path(__file__).resolve().parent.parent / "data" / "images"

# 引入数据
def include_data():
    singer_data=None
    song_data=None
    with open(DATA_DIR/"singer_data.json","r",encoding="utf-8") as f:
        singer_data=json.load(f)
    with open(DATA_DIR/"song_data.json","r",encoding="utf-8") as f:
        song_data=json.load(f)
    return singer_data,song_data

# 存储图片
def storage_image(data,filename):
    path=IMG_DIR/filename
    with open(path,"wb") as f:
        f.write(data)
    return str(path)

# 存储数据
def storage_data(singer_data,song_data):
    with open(DATA_DIR/"singer_data.json","w",encoding="utf-8") as f:
        json.dump(singer_data,f,ensure_ascii=False,indent=2)
    with open(DATA_DIR/"song_data.json","w",encoding="utf-8") as f:
        json.dump(song_data,f,ensure_ascii=False,indent=2)

# 把数据转换成 fixture 格式
def transform_data(singer_data,song_data):
    singer_fixture=[]
    song_fixture=[]

    # 转换歌手数据
    for id in range(1,len(singer_data)):
        item={}
        fields={}
        singer=singer_data[id]
        item["model"]="web.Singer"
        item["pk"]=id
        fields["id"]=id
        fields["name"]=singer["name"]
        fields["desc"]=singer["desc"]
        fields["source_url"]=singer["source_url"]
        fields["image_url"]=singer["image_url"]
        item["fields"]=fields
        singer_fixture.append(item)
    
    # 转换歌曲数据
    for id in range(1,len(song_data)):
        item={}
        fields={}
        song=song_data[id]
        item["model"]="web.Song"
        item["pk"]=id
        fields["id"]=id
        fields["name"]=song["name"]
        fields["source_url"]=song["source_url"]
        fields["image_url"]=song["image_url"]
        fields["singers"]=song["singer_id"]
        fields["lyrics"]="\n".join(song["lyrics"])
        item["fields"]=fields
        song_fixture.append(item)

    with open(DATA_DIR/"singer_fixture.json","w",encoding="utf-8") as f:
        json.dump(singer_fixture,f,ensure_ascii=False,indent=2)
    with open(DATA_DIR/"song_fixture.json","w",encoding="utf-8") as f:
        json.dump(song_fixture,f,ensure_ascii=False,indent=2)
    