from pathlib import Path
import re
import matplotlib.pyplot as plt

SOLUTION_DIR = Path(__file__).resolve().parent


def build_graph(filename, str1, str2):
    categories = []
    values = []
    colors = ['purple'] * 10 + ['red'] * 10 + ['orange'] * 10
    with open(SOLUTION_DIR / (filename + ".txt"), "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[:30]:
            item = re.search("(.+) & (.+) : (\\d+)", line)
            categories.append(item.group(1) + '\n' + item.group(2))
            values.append(int(item.group(3)))

    width_pixels = 5500
    height_pixels = 1080
    dpi = 100
    figsize = (width_pixels / dpi, height_pixels / dpi)
    plt.figure(figsize=figsize)
    plt.rcParams['font.sans-serif'] = ['HarmonyOS Sans SC']
    bars = plt.bar(categories, values, color=colors)
    plt.title(f"最佳拍档: {str1}", fontsize=34)
    plt.xlabel(str2)
    plt.ylabel("合作歌曲数", fontsize=34)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                 f'{int(height)}', ha='center', va='bottom', fontsize=24)

    plt.savefig(SOLUTION_DIR / (filename + ".png"), dpi=dpi)
    plt.close()


build_graph("match_singer_writer", "歌手&作词", "歌手\n作词")
build_graph("match_singer_melodier", "歌手&作曲", "歌手\n作曲")
build_graph("match_writer_melodier", "作词&作曲", "作词\n作曲")
