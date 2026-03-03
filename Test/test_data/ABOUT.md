# 目录职责
本目录用于：存放测试脚本使用的 Excel 样本数据，包括静态上传样本和运行时生成的明细测试文件。

# 关键模块 / 文件一览
- `IFIR ROW.xlsx`：IFIR 行级测试数据样本。
- `IFIR DETAIL.xlsx`：IFIR 明细测试数据样本。
- `RA row.xlsx`：RA 行级测试数据样本。
- `RA DETAIL.xlsx`：RA 明细测试数据样本。
- `test_ifir_detail.xlsx`：由 `test_detail_upload.py` 生成的 IFIR 明细临时测试文件。
- `test_ra_detail.xlsx`：由 `test_detail_upload.py` 生成的 RA 明细临时测试文件。

# 主要数据流 / 调用链
- `test_api.py` 与上传接口联调时会读取本目录内的 Excel 文件。
- `test_detail_upload.py` 会在运行过程中向本目录写入新的测试 Excel 文件，再上传到后端。

# 与上层 / 下层目录的关系
- 上层：`Test/` 目录中的测试脚本负责读取或生成这里的文件。
- 下层：无进一步子目录。

# 运行方式 / 配置项
- 目录内文件默认由测试脚本按固定文件名读取。
- 若替换样本文件，需保持脚本中使用的字段名和工作表结构兼容。

# 常见坑 / TODO
- 文件名区分大小写和空格，改名后脚本可能找不到样本。
- 运行 `test_detail_upload.py` 会覆盖同名的临时测试文件。
- TODO：后续可增加一份字段说明，明确每类 Excel 的必填列。
