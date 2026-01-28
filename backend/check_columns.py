"""
检查 DETAIL Excel 文件的列名
"""
import pandas as pd

ifir_file = r"D:\WorkDocument\Project\Visual_KPI\VisualTeam\VisualTeam\IFIR DETAIL.xlsx"
ra_file = r"D:\WorkDocument\Project\Visual_KPI\VisualTeam\VisualTeam\RA DETAIL.xlsx"

output = []
output.append("=" * 50)
output.append("IFIR DETAIL 列名:")
output.append("=" * 50)
df_ifir = pd.read_excel(ifir_file)
for i, col in enumerate(df_ifir.columns):
    output.append(f"{i:2d}: {col}")

output.append("\n" + "=" * 50)
output.append("RA DETAIL 列名:")
output.append("=" * 50)
df_ra = pd.read_excel(ra_file)
for i, col in enumerate(df_ra.columns):
    output.append(f"{i:2d}: {col}")

output.append("\n" + "=" * 50)
output.append(f"IFIR DETAIL 行数: {len(df_ifir)}")
output.append(f"RA DETAIL 行数: {len(df_ra)}")

# 写入文件
with open("column_check.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("结果已写入 column_check.txt")
