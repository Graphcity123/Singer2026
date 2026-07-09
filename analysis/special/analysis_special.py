import json
import re
import jieba
import math
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

# 读取作者信息
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
    "架子鼓"]

singer_exist_count = {}
writer_exist_count = {}
word_exist_count = {}

# 载入作者信息到数据库
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


for singer in singer_data:
    singer_name[singer["pk"]] = singer["fields"]["name"]
    singer_dict[singer["fields"]["name"]] = singer["pk"]

singer_words = {}
writer_words = {}
singer_writer_set = set()
singer_set = set()

# 进行前期记录(歌手统计,作词统计,词语统计)方便后续筛选
for song in song_data:
    str = song["fields"]["lyrics"]
    if (not str or str == ""):
        continue
    seg_list = jieba.cut(str)
    singers_list = song["fields"]["singers"]
    writers_str = get_writer(str)
    writers_list = load_writer(writers_str)
    seg_list = [word for word in seg_list if (is_chinese_word(word) and word not in ban_words)]
    if (not seg_list):
        continue
    for word in seg_list:
        word_exist_count[word] = word_exist_count.get(word, 0) + 1
    for singer in singers_list:
        singer_exist_count[singer] = singer_exist_count.get(singer, 0) + 1
        singer_writer_set.add(singer_name[singer])
        singer_set.add(singer_name[singer])
    for writer in writers_list:
        writer_exist_count[writer] = writer_exist_count.get(writer, 0) + 1
        singer_writer_set.add(writer_name[writer])

# 判断词语是否符合收录标准
def isRight(word):
    global singer_writer_set
    if (not is_chinese_word(word)):
        return False
    if (word in ban_words):
        return False
    if (word in singer_writer_set):
        return False
    return word_exist_count[word] >= 10

# 给歌手和作词收录词语信息
for song in song_data:
    str = song["fields"]["lyrics"]
    if (not str or str == ""):
        continue

    writers_str = get_writer(str)
    writers_list = load_writer(writers_str)
    singers_list = song["fields"]["singers"]

    lines = str.split('\n')
    lines = [line for line in lines if not re.search(r'[:：/()、（）]', line)]
    str = '\n'.join(lines)
    seg_list = jieba.cut(str)
    seg_list = [word for word in seg_list if isRight(word)]

    if (not seg_list):
        continue
    for singer in singers_list:
        if (singer_exist_count[singer] < 20):
            continue
        if (singer not in singer_words):
            singer_words[singer] = seg_list
        else:
            singer_words[singer].extend(seg_list)
    for writer in writers_list:
        if (writer_exist_count[writer] < 20 or writer_name[writer] in singer_set):
            continue
        if (writer not in writer_words):
            writer_words[writer] = seg_list
        else:
            writer_words[writer].extend(seg_list)

# 建立 TF-IDF 数据库
def build_special(filename, singer_words, singer_name):
    singer_words_dict = {}
    singer_count_for_word = {}
    tf = {}
    idf = {}

    # 建立 TF
    for singer, words in singer_words.items():
        words_dict = {}
        tf_dict = {}
        for word in words:
            words_dict[word] = words_dict.get(word, 0) + 1
        singer_words_dict[singer] = words_dict
        total_count = sum(x[1] for x in words_dict.items())
        for word, cnt in words_dict.items():
            singer_count_for_word[word] = singer_count_for_word.get(word, 0) + 1
            tf_dict[word] = cnt / total_count
        tf[singer] = tf_dict

    # 建立 IDF
    total_singers = len(singer_words)
    for word, cnt in singer_count_for_word.items():
        idf[word] = math.log(total_singers / cnt)

    def tfidf(singer, word):
        return tf[singer][word] * idf[word]

    # 统计歌手 TF-IDF 总分
    singer_value = {}
    for singer, words_dict in singer_words_dict.items():
        value = 0
        wordlist = sorted(words_dict.keys(), key=(lambda x: tfidf(singer, x)), reverse=True)
        for word in wordlist[:10]:
            value += tfidf(singer, word)
        singer_value[singer] = value

    # 数据输出
    singer_list = sorted(singer_value.items(), key=(lambda x: x[1]), reverse=True)
    with open(SOLUTION_DIR / filename, "w", encoding="utf-8") as f:
        for singer, value in singer_list[:50]:
            f.write("%s: %.4f\n" % (singer_name[singer], value))
            wordlist = sorted(
                singer_words_dict[singer].keys(), key=(
                    lambda x: tfidf(
                        singer, x)), reverse=True)
            for word in wordlist[:10]:
                f.write("|  %s: %.4f\n" % (word, tfidf(singer, word)))


build_special("special_singer.txt", singer_words, singer_name)
build_special("special_writer.txt", writer_words, writer_name)
