import json
import re
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SOLUTION_DIR = Path(__file__).resolve().parent

# 引入数据


def include_data():
    singer_data = None
    song_data = None
    with open(DATA_DIR / "singer_fixture.json", "r", encoding="utf-8") as f:
        singer_data = json.load(f)
    with open(DATA_DIR / "song_fixture.json", "r", encoding="utf-8") as f:
        song_data = json.load(f)
    return singer_data, song_data

# 从歌词文件分离出作词/作曲列表


def get_writer(text, str):
    writer_data = re.search(rf"{str}(.+?)\n", text)
    if (writer_data):
        str = writer_data.group(1)
        name = re.search(r":([\s\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff+a-zA-Z0-9/,_\-.!]+)", str)
        if (name):
            namelist = name.group(1).strip()
            names = re.split(r"[/,]", namelist)
            namedata = []
            for name in names:
                name_str = name.strip()
                if (name_str != ""):
                    namedata.append(name_str)
            return namedata
        else:
            return None
    else:
        return None


singer_data, song_data = include_data()

singer_dict = {}  # name->id
writer_name = {}  # id->name
writer_dict = {}  # name->id
singer_name = {}  # id->name
melodier_dict = {}  # name->id
melodier_name = {}  # id->name
writer_count = 0
melodier_count = 0

match_singer_writer_dict = {}
match_singer_melodier_dict = {}
match_writer_melodier_dict = {}

# 读取作词数据，加入dict


def load_writer(data):
    if (not data):
        return []
    global writer_count
    for writer in data:
        if (writer not in writer_dict):
            writer_count += 1
            writer_name[writer_count] = writer
            writer_dict[writer] = writer_count
    return [writer_dict[writer] for writer in data]

# 读取作曲数据，加入dict


def load_melodier(data):
    if (not data):
        return []
    global melodier_count
    for melodier in data:
        if (melodier not in melodier_dict):
            melodier_count += 1
            melodier_name[melodier_count] = melodier
            melodier_dict[melodier] = melodier_count
    return [melodier_dict[melodier] for melodier in data]


for singer in singer_data:
    singer_name[singer["pk"]] = singer["fields"]["name"]
    singer_dict[singer["fields"]["name"]] = singer["pk"]

# 写入搭档数据dict


def build_match(data_dict, fir_dict, sec_dict):
    for fir in fir_dict:
        for sec in sec_dict:
            if ((fir, sec) not in data_dict):
                data_dict[fir, sec] = 1
            else:
                data_dict[fir, sec] += 1


# 读取歌曲
for song in song_data:
    str = song["fields"]["lyrics"]
    if (not str or str == ""):
        continue

    singers_list = song["fields"]["singers"]
    writers_str = get_writer(str, "作词")
    writers_list = load_writer(writers_str)
    melodiers_str = get_writer(str, "作曲")
    melodiers_list = load_melodier(melodiers_str)

    build_match(match_singer_writer_dict, singers_list, writers_list)
    build_match(match_singer_melodier_dict, singers_list, melodiers_list)
    build_match(match_writer_melodier_dict, writers_list, melodiers_list)

# 输出数据


def build_solution(data_dict, fir_dict, sec_dict, filename):
    sorted_match = sorted(data_dict.items(), key=(lambda x: x[1]), reverse=True)
    with open(SOLUTION_DIR / filename, "w", encoding="utf-8") as f:
        for (fir, sec), cnt in sorted_match:
            if (fir_dict[fir] == sec_dict[sec]):
                continue
            f.write("%s & %s : %d\n" % (fir_dict[fir], sec_dict[sec], cnt))


build_solution(match_singer_writer_dict, singer_name, writer_name, "match_singer_writer.txt")
build_solution(match_singer_melodier_dict, singer_name, melodier_name, "match_singer_melodier.txt")
build_solution(match_writer_melodier_dict, writer_name, melodier_name, "match_writer_melodier.txt")
