"""
报告图表生成模块
使用 matplotlib 生成高质量图表供 Excel 报告嵌入
"""
import logging
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 配色方案（与前端 ECharts 保持一致）
# ---------------------------------------------------------------------------
COLORS = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
    '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ff9f7f',
]
TGT_COLOR = '#f56c6c'

# ---------------------------------------------------------------------------
# 中文字体配置
# ---------------------------------------------------------------------------
_FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
_FONT_CANDIDATES = [
    _FONT_DIR / "NotoSansCJKsc-Regular.otf",
    _FONT_DIR / "NotoSansSC-Regular.ttf",
    _FONT_DIR / "SourceHanSansSC-Regular.otf",
]
_FALLBACK_FAMILIES = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Source Han Sans SC",
    "WenQuanYi Micro Hei",
    "PingFang SC",
]

def _setup_chinese_font():
    for fp in _FONT_CANDIDATES:
        if fp.exists():
            fm.fontManager.addfont(str(fp))
            plt.rcParams["font.family"] = fm.FontProperties(fname=str(fp)).get_name()
            logger.info("report_chart: using font %s", fp.name)
            break
    else:
        available = {font.name for font in fm.fontManager.ttflist}
        for family in _FALLBACK_FAMILIES:
            if family in available:
                plt.rcParams["font.family"] = family
                logger.warning(
                    "report_chart: no bundled CJK font found, falling back to system font %s",
                    family,
                )
                break
        else:
            plt.rcParams["font.family"] = "DejaVu Sans"
            logger.warning(
                "report_chart: no bundled CJK font found and no known CJK system font detected"
            )
    plt.rcParams["axes.unicode_minus"] = False

_setup_chinese_font()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_trend_chart(
    entities: List[Dict],
    tgt: Optional[int] = None,
    value_label: str = "IFIR",
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 5),
    dpi: int = 150,
) -> bytes:
    """
    生成多实体趋势对比折线图。

    Parameters
    ----------
    entities : list[dict]
        [{"name": "ModelA", "trend": [{"month": "2024-07", "value": 0.001234}, ...]}, ...]
        value 为小数形式，内部会 ×1,000,000 转 DPPM。
    tgt : int | None
        TGT 目标线值 (DPPM)。
    value_label : str
        Y 轴标签前缀，"IFIR" 或 "RA"。
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    all_months = sorted({p["month"] for e in entities for p in e["trend"]})

    for i, entity in enumerate(entities):
        color = COLORS[i % len(COLORS)]
        month_map = {p["month"]: p["value"] * 1_000_000 for p in entity["trend"]}
        values = [month_map.get(m) for m in all_months]
        ax.plot(all_months, values, '-o', color=color, label=entity["name"],
                linewidth=2, markersize=4)

    if tgt is not None:
        ax.axhline(y=tgt, color=TGT_COLOR, linestyle='--', linewidth=1.5,
                    label=f'TGT ({tgt:,})')

    ax.set_ylabel(f'{value_label} (DPPM)')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    if len(all_months) > 8:
        ax.tick_params(axis='x', rotation=45)
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_pie_chart(
    items: List[Dict],
    value_label: str = "IFIR",
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (8, 6),
    dpi: int = 150,
) -> bytes:
    """
    生成占比环形饼图。

    Parameters
    ----------
    items : list[dict]
        [{"name": "ModelA", "value": 1234, "share": 0.452}, ...]
        value 为 DPPM 值。
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    names = [it["name"] for it in items]
    values = [it["value"] for it in items]
    colors = [COLORS[i % len(COLORS)] for i in range(len(items))]

    wedges, texts, autotexts = ax.pie(
        values, labels=names, colors=colors,
        autopct='%1.1f%%', pctdistance=0.82,
        wedgeprops=dict(width=0.35, edgecolor='white'),
    )
    for t in autotexts:
        t.set_fontsize(9)

    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
