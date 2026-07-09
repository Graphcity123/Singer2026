import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

SOLUTION_DIR = Path(__file__).resolve().parent
LYRICS_DIR = SOLUTION_DIR.parent / "lyrics"

# 读取数据
common = {}
with open(LYRICS_DIR / "lyrics_singer.txt", "r", encoding="utf-8") as f:
    for line in f:
        m = re.search(r"(.+): (\d+) (\d+)", line)
        if m:
            name = m.group(1).strip()
            common[name] = (int(m.group(2)), int(m.group(3)))

special = {}
with open(SOLUTION_DIR / "special_singer.txt", "r", encoding="utf-8") as f:
    for line in f:
        m = re.match(r"^([^:]+): ([\d.]+)$", line)
        if m:
            special[m.group(1).strip()] = float(m.group(2))

shared = set(common.keys()) & set(special.keys())
print(f"共有 {len(shared)} 位歌手")

names, x_vals, y_vals, coverages = [], [], [], []

# 数据转换
def trans_y(x):
    return 10 * (1 - np.exp(-18 * x))

def trans_x(x):
    if (500 <= x <= 1750):
        return 500 * 4 + (x - 500) * 6
    elif (x > 1750):
        return 500 * 4 + (1750 - 500) * 6 + (x - 1750) * 2
    else:
        return x * 4


for name in shared:
    names.append(name)
    x_vals.append(trans_x(common[name][1]))
    y_vals.append(trans_y(special[name]))
    coverages.append(common[name][0])
x, y = np.array(x_vals), np.array(y_vals)
sizes = np.array(coverages)

# 高亮标注
highlight = [
    "法老", "GAI周延", "陈致逸", "王菲", "赵雷", "万妮达Vinida Weng",
    "蔡徐坤", "汪苏泷", "张震岳", "洛天依", "毛不易",
    "G.E.M.邓紫棋", "塞壬唱片-MSR", "HOYO-MiX", "三Z-STUDIO", "铁痕电台-MSR",
    "李荣浩", "孙燕姿", "胡彦斌", "林俊杰", "周深", "许嵩",
]

# 绘图
fig, ax = plt.subplots(figsize=(16, 12))
plt.rcParams['font.sans-serif'] = ['HarmonyOS Sans SC', 'Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 分离高亮和非高亮
hx, hy, hnames = [], [], []
nx, ny, nnames = [], [], []
for i, name in enumerate(names):
    if name in highlight:
        hx.append(x[i])
        hy.append(y[i])
        hnames.append(name)
    else:
        nx.append(x[i])
        ny.append(y[i])
        nnames.append(name)

# 非高亮：灰色小点 + 灰色普通标签
ax.scatter(nx, ny, s=18, c='#cccccc', alpha=0.5, zorder=2)
for xv, yv, name in zip(nx, ny, nnames):
    ax.annotate(name, (xv, yv),
                textcoords="offset points", xytext=(0, 7),
                fontsize=8, fontweight='normal', color='#aaaaaa',
                ha='center', va='bottom', zorder=4)

# 高亮：彩色小点 + 上方名字
ax.scatter(hx, hy, s=28, c='#d94f4f', alpha=0.85,
           edgecolors='white', linewidth=0.5, zorder=3)
for xv, yv, name in zip(hx, hy, hnames):
    ax.annotate(name, (xv, yv),
                textcoords="offset points", xytext=(0, 7),
                fontsize=10, fontweight='bold', color='#d94f4f',
                ha='center', va='bottom', zorder=5)

# 象限分割线
x_med, y_med = np.median(x), np.median(y)
ax.axhline(y=y_med, color='#333', linewidth=1.2, linestyle='--', alpha=0.4, zorder=1)
ax.axvline(x=x_med, color='#333', linewidth=1.2, linestyle='--', alpha=0.4, zorder=1)

# 象限标签
xm = max(x) * 1.02
y_top = max(y) * 1.03
y_bot = min(y) * 0.97 + (max(y) - min(y)) * 0.03
ax.text(xm * 0.98, y_top, "全能型", ha='right', va='top',
        fontsize=15, fontweight='bold', color='#2c3e50')
ax.text(xm * 0.02, y_top, "纯独特型", ha='left', va='top',
        fontsize=15, fontweight='bold', color='#2c3e50')
ax.text(xm * 0.98, y_bot, "纯常用型", ha='right', va='bottom',
        fontsize=15, fontweight='bold', color='#2c3e50')
ax.text(xm * 0.02, y_bot, "双低型", ha='left', va='bottom',
        fontsize=15, fontweight='bold', color='#aaaaaa')

# 输出表格
ax.set_xlabel("常用词总使用次数（转换后）", fontsize=20, fontweight='bold')
ax.set_ylabel("TF-IDF 标志词总分（转换后）", fontsize=20, fontweight='bold')
ax.set_title("歌手词汇风格：常用 / 独特", fontsize=22, fontweight='bold', pad=12)
ax.set_xlim(-20, xm)
ax.set_ylim(min(y) * 0.98, max(y) * 1.05)
plt.tight_layout()
plt.savefig(SOLUTION_DIR / "quadrant_singer.png", dpi=120, bbox_inches='tight')
plt.close()
