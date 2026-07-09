import json
import re
import jieba
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


def is_chinese_word(text):
    # 使用正则判断是否为中文词语
    pattern = r'^[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+$'
    if len(text) < 2:
        return False
    return bool(re.fullmatch(pattern, text))

# 提取作词/作曲数据
def get_writer(text):
    writer_data = re.search(r"作词(.+?)\n", text)
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

word_count = {}
singer_dict = {}  # name->id
writer_name = {}  # id->name
writer_dict = {}  # name->id
singer_name = {}  # id->name
writer_count = 0
ban_words = [
    "作词",
    "作曲",
    "混音",
    "制作",
    "编曲",
    "音乐",
    "演唱",
    "原唱",
    "母带",
    "吉他",
    "录音",
    "录音室",
    "弦乐",
    "编写",
    "总监",
    "牛班",
    "维伴",
    "贝斯",
    "统筹",
    "监制",
    "有限公司",
    "录音师",
    "人声",
    "出品",
    "键盘",
    "工程师",
    "录音棚",
    "北京",
    "纯音乐",
    "架子鼓",
    "工作室"]

# 载入数据到数据库
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

# 词语类
class Word:
    def __init__(self, singer, writer):
        self.cnt = 1
        self.singers = {}
        self.writers = {}
        for id in singer:
            self.singers[id] = self.singers.get(id, 0) + 1
        for id in writer:
            self.writers[id] = self.writers.get(id, 0) + 1

    def Add(self, singer, writer):
        self.cnt += 1
        for id in singer:
            self.singers[id] = self.singers.get(id, 0) + 1
        for id in writer:
            self.writers[id] = self.writers.get(id, 0) + 1


for singer in singer_data:
    singer_name[singer["pk"]] = singer["fields"]["name"]
    singer_dict[singer["fields"]["name"]] = singer["pk"]

# 添加词语
for song in song_data:
    str = song["fields"]["lyrics"]
    if (not str or str == ""):
        continue
    seg_list = jieba.cut(str)
    singers_list = song["fields"]["singers"]
    writers_str = get_writer(str)
    writers_list = load_writer(writers_str)

    for word in seg_list:
        if (word not in word_count):
            word_count[word] = Word(singers_list, writers_list)
        else:
            word_count[word].Add(singers_list, writers_list)

singer_cnt = {}
singer_total = {}
writer_cnt = {}
writer_total = {}

# 输出数据
sorted_word = sorted(word_count.items(), key=(lambda x: x[1].cnt), reverse=True)
with open(SOLUTION_DIR / "lyrics.txt", "w", encoding="utf-8") as f:
    for word, data in sorted_word:
        if (is_chinese_word(word) and word not in ban_words):
            if (data.cnt > 500):
                output = "%s: %d" % (word, data.cnt)
                f.write(output + '\n')
                sorted_writer = sorted(data.writers.items(), key=(lambda x: x[1]), reverse=True)
                output = ' '.join("(%s %d)" % (writer_name[writer], count)
                                  for writer, count in sorted_writer[:10])
                f.write(output + '\n')
                sorted_singer = sorted(data.singers.items(), key=(lambda x: x[1]), reverse=True)
                output = ' '.join("(%s %d)" % (singer_name[singer], count)
                                  for singer, count in sorted_singer[:10])
                f.write(output + '\n')

                for writer, count in sorted_writer:
                    writer_cnt[writer] = writer_cnt.get(writer, 0) + 1
                    writer_total[writer] = writer_total.get(writer, 0) + count
                for singer, count in sorted_singer:
                    singer_cnt[singer] = singer_cnt.get(singer, 0) + 1
                    singer_total[singer] = singer_total.get(singer, 0) + count

with open(SOLUTION_DIR / "lyrics_writer.txt", "w", encoding="utf-8") as f:
    sorted_writer = sorted(writer_total.items(), key=(lambda x: x[1]), reverse=True)
    for writer, cnt in sorted_writer:
        f.write("%s: %d %d\n" % (writer_name[writer], writer_cnt[writer], writer_total[writer]))

with open(SOLUTION_DIR / "lyrics_singer.txt", "w", encoding="utf-8") as f:
    sorted_singer = sorted(singer_total.items(), key=(lambda x: x[1]), reverse=True)
    for singer, cnt in sorted_singer:
        f.write("%s: %d %d\n" % (singer_name[singer], singer_cnt[singer], singer_total[singer]))