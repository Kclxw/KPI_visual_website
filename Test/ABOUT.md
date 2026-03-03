# 目录职责
本目录用于：存放后端联调、数据导入、ETL 与接口连通性的手工测试脚本，以及这些脚本依赖的测试样本文件。

# 关键模块 / 文件一览
- `test_api.py`：串行验证健康检查、上传接口、IFIR 选项接口与 IFIR 分析接口。
- `test_analyze.py`：直接验证 IFIR / RA 的 ODM 分析接口返回结构。
- `test_connection.py`：检查数据库连接和基础 HTTP 端点可用性。
- `test_detail_upload.py`：生成明细样本数据并验证完整上传链路。
- `test_etl.py`：直接调用 ETL 服务处理最新上传任务。
- `test_data/`：存放测试脚本生成或依赖的 Excel 数据。
- `test_files/`：存放单独准备的上传测试文件。

# 主要数据流 / 调用链
- 测试脚本读取本地配置后，调用本地 FastAPI 服务或数据库。
- `test_detail_upload.py` 会先生成 Excel，再调用上传接口，再轮询任务状态，最后回查数据库。
- `test_etl.py` 会读取最新 `upload_task` 记录，直接调用 `EtlService.process_upload_task`。

# 与上层 / 下层目录的关系
- 上层：仓库根目录，提供 `backend/app` 代码、配置文件和运行环境。
- 下层：`test_data/` 保存样本 Excel；`test_files/` 保存额外上传测试文件；`__pycache__/` 为 Python 运行缓存（不参与说明维护）。

# 运行方式 / 配置项
- 运行前需要先启动后端服务，且本地数据库配置可用。
- 常用执行方式：`python Test/test_api.py`、`python Test/test_detail_upload.py`、`python Test/test_etl.py`。
- 默认接口地址写死为 `http://localhost:8000`。

# 常见坑 / TODO
- 部分脚本依赖当前工作目录，跨目录运行时要注意相对路径是否仍然成立。
- 若数据库或接口未启动，脚本会直接报错或返回失败。
- TODO：后续可考虑把通用的接口地址、超时和测试数据路径抽成统一配置。
