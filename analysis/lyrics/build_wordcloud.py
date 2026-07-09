import matplotlib.pyplot as plt
from wordcloud import WordCloud
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

# 判断词语是否符合收录标准


def isRight(word):
    if (not is_chinese_word(word)):
        return False
    if (word in ban_words):
        return False
    if (word in singer_dict):
        return False
    return True


# 添加词语
for song in song_data:
    str = song["fields"]["lyrics"]
    if (not str or str == ""):
        continue

    singers_list = song["fields"]["singers"]
    writers_str = get_writer(str)
    writers_list = load_writer(writers_str)

    lines = str.split('\n')
    lines = [line for line in lines if not re.search(r'[:：/()、（）]', line)]
    str = '\n'.join(lines)
    seg_list = jieba.cut(str)
    seg_list = [word for word in seg_list if isRight(word)]

    for word in seg_list:
        if (word not in word_count):
            word_count[word] = Word(singers_list, writers_list)
        else:
            word_count[word].Add(singers_list, writers_list)

sorted_word = sorted(word_count.items(), key=(lambda x: x[1].cnt), reverse=True)

# 建立词云
FONT_DIR = Path(__file__).resolve().parent.parent.parent / \
    "web" / "fonts" / "HarmonyOS_Sans_SC_Black.ttf"


def generate_wordcloud(name):
    id = singer_dict[name]
    word_dict = {}
    for word, data in sorted_word:
        if (isRight(word) and data.singers.get(id, 0) >= 5):
            word_dict[word] = data.singers[id]
    wordcloud = WordCloud(
        font_path=FONT_DIR,
        width=800,
        height=400,
        scale=2,
        background_color='white'
    ).generate_from_frequencies(word_dict)
    plt.rcParams['font.sans-serif'] = ['HarmonyOS Sans SC Black']
    plt.title(f"{name} - 词云图", fontsize=14)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(SOLUTION_DIR / (name + ".png"), dpi=600)
    plt.close()


generate_wordcloud("李荣浩")
generate_wordcloud("法老")
generate_wordcloud("汪苏泷")
generate_wordcloud("韦礼安")
generate_wordcloud("李宗盛")
