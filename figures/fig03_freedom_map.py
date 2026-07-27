#!/usr/bin/env python3
"""
圖 3：自由度地圖
論點：自動化目前攻下的，恰好是自由度最低的幾格；偏誤住在腦力那一端。
      這就是為什麼 κ=0.02 出現在 selective reporting，而不是資料萃取。
產生方式：python3 fig03_freedom_map.py
輸出：fig03-freedom-map.pdf / .png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 中文字型（macOS）
for cand in ["PingFang TC", "Heiti TC", "Arial Unicode MS"]:
    if any(cand in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [cand]
        break
plt.rcParams["axes.unicode_minus"] = False

# 各階段：(名稱, 自動化成熟度 0-1, 偏誤棲居度 0-1)
# 由「最機械」到「最需判斷」由上而下排列
stages = [
    ("去重",            0.98, 0.02),
    ("DOI／引用解析",   0.95, 0.05),
    ("統計合併",        0.90, 0.10),
    ("檢索執行",        0.85, 0.20),
    ("流程圖計數",      0.90, 0.15),
    ("標題摘要初篩",    0.70, 0.45),
    ("資料萃取",        0.55, 0.55),
    ("全文合格判定",    0.45, 0.65),
    ("偏誤風險評估",    0.35, 0.80),
    ("GRADE 間接性",    0.15, 0.90),
    ("選擇性報告判斷",  0.10, 0.95),
]

names = [s[0] for s in stages]
auto = [s[1] for s in stages]
bias = [s[2] for s in stages]
y = range(len(stages))

fig, ax = plt.subplots(figsize=(9.5, 6.2))

# 發散長條：自動化向左、偏誤向右
ax.barh(y, [-a for a in auto], color="#6a86a8", height=0.62,
        label="自動化成熟度", zorder=3)
ax.barh(y, bias, color="#c98a8a", height=0.62,
        label="偏誤棲居度", zorder=3)

# 中軸階段名
for i, name in enumerate(names):
    ax.text(0, i, "  " + name + "  ", ha="center", va="center",
            fontsize=10.5, zorder=5,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#cccccc", lw=0.6))

# κ=0.02 標註（選擇性報告）
ax.annotate("Gates 2018：κ=0.02\n機器在這一格幾乎抓不到",
            xy=(0.95, len(stages) - 1), xytext=(0.55, len(stages) - 2.6),
            fontsize=9.5, color="#8a4a4a", ha="left",
            arrowprops=dict(arrowstyle="->", color="#c98a8a", lw=1.2))

ax.set_yticks([])
ax.set_ylim(-0.7, len(stages) - 0.3)
ax.set_xlim(-1.08, 1.08)
ax.set_xticks([-1, -0.5, 0, 0.5, 1])
ax.set_xticklabels(["高", "中", "0", "中", "高"], fontsize=10)
ax.invert_yaxis()

# 兩端標題
ax.text(-1.0, -1.15, "← 自動化成熟度", ha="left", va="center",
        fontsize=11, color="#4a6a8a", fontweight="bold")
ax.text(1.0, -1.15, "偏誤棲居度 →", ha="right", va="center",
        fontsize=11, color="#a85a5a", fontweight="bold")

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.axvline(0, color="#999999", lw=0.8, zorder=1)
ax.grid(axis="x", color="#eeeeee", zorder=0)

ax.set_title("自動化攻下的是自由度最低的幾格，偏誤住在腦力那一端",
             fontsize=13, pad=28)

plt.tight_layout()
fig.savefig("fig03-freedom-map.pdf", bbox_inches="tight")
fig.savefig("fig03-freedom-map.png", dpi=200, bbox_inches="tight")
print("wrote fig03-freedom-map.pdf / .png")
