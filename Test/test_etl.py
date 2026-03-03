"""
测试 ETL 处理流程，直接运行并绕过后台任务调度。
"""
# 导入系统模块，用于调整模块搜索路径。
import sys
# 导入文件路径处理所需的库。
import os

# 将当前测试目录加入模块搜索路径，确保可以导入项目代码。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入数据库会话工厂。
from app.core.database import SessionLocal
# 导入 ETL 服务。
from app.services.etl_service import EtlService
# 导入上传任务模型。
from app.models.tables import UploadTask


def test_etl():
    '''
    功能概述：
    读取最近一次上传任务，重置状态后直接调用 ETL 服务执行处理，便于脱离后台线程排查问题。

    输入参数：
    - 无。

    返回值：
    - 无，结果直接输出到控制台。

    关键流程：
    - 获取最新上传任务。
    - 收集仍然存在的上传文件。
    - 重置任务状态。
    - 调用 ETL 服务执行处理。
    - 输出最终任务状态和各文件处理结果。

    异常/边界：
    - 如果没有上传任务或没有有效文件，函数会提前返回。
    - 处理异常会打印完整堆栈，便于定位问题。

    依赖：
    - `app.core.database.SessionLocal`
    - `app.services.etl_service.EtlService`
    - `app.models.tables.UploadTask`

    示例：
    - 运行 `python Test/test_etl.py`
    '''
    # 打印当前测试标题。
    print("=" * 50)
    # 提示开始执行 ETL 测试。
    print("开始测试ETL")
    # 输出分隔线。
    print("=" * 50)

    # 创建数据库会话。
    db = SessionLocal()
    # 使用异常处理包装整个 ETL 测试流程。
    try:
        # 查询最新的一条上传任务记录。
        task = db.query(UploadTask).order_by(UploadTask.id.desc()).first()

        # 如果没有任何上传任务，则直接结束测试。
        if not task:
            # 输出缺少任务的提示。
            print("没有找到上传任务")
            # 提前返回。
            return

        # 输出当前任务 ID。
        print(f"找到任务: {task.task_id}")
        # 输出当前任务状态。
        print(f"状态: {task.status}")
        # 输出 IFIR Detail 文件路径。
        print(f"IFIR Detail: {task.ifir_detail_file}")
        # 输出 IFIR Row 文件路径。
        print(f"IFIR Row: {task.ifir_row_file}")
        # 输出 RA Detail 文件路径。
        print(f"RA Detail: {task.ra_detail_file}")
        # 输出 RA Row 文件路径。
        print(f"RA Row: {task.ra_row_file}")

        # 初始化实际可供 ETL 使用的文件字典。
        files = {}
        # 仅在 IFIR Detail 文件存在时加入处理列表。
        if task.ifir_detail_file and os.path.exists(task.ifir_detail_file):
            # 记录 IFIR Detail 文件路径。
            files["ifir_detail"] = task.ifir_detail_file
        # 仅在 IFIR Row 文件存在时加入处理列表。
        if task.ifir_row_file and os.path.exists(task.ifir_row_file):
            # 记录 IFIR Row 文件路径。
            files["ifir_row"] = task.ifir_row_file
        # 仅在 RA Detail 文件存在时加入处理列表。
        if task.ra_detail_file and os.path.exists(task.ra_detail_file):
            # 记录 RA Detail 文件路径。
            files["ra_detail"] = task.ra_detail_file
        # 仅在 RA Row 文件存在时加入处理列表。
        if task.ra_row_file and os.path.exists(task.ra_row_file):
            # 记录 RA Row 文件路径。
            files["ra_row"] = task.ra_row_file

        # 输出最终参与处理的文件类型。
        print(f"有效文件: {list(files.keys())}")

        # 如果没有任何有效文件，则直接结束测试。
        if not files:
            # 输出缺少有效文件的提示。
            print("没有找到有效的文件！")
            # 提前返回。
            return

        # 将任务状态重置为排队中。
        task.status = "queued"
        # 将任务进度重置为 0。
        task.progress = 0
        # 清空旧的错误信息。
        task.error_message = None
        # 提交重置后的任务状态。
        db.commit()

        # 提示开始执行 ETL。
        print("\n开始运行ETL...")
        # 初始化 ETL 服务。
        service = EtlService(db)
        # 调用 ETL 服务处理当前任务。
        service.process_upload_task(task.task_id, files)

        # 从数据库刷新任务对象，读取最新状态。
        db.refresh(task)
        # 输出任务最终状态。
        print(f"\n最终状态: {task.status}")
        # 输出任务最终进度。
        print(f"进度: {task.progress}%")
        # 仅在存在错误信息时打印错误详情。
        if task.error_message:
            # 输出任务错误信息。
            print(f"错误: {task.error_message}")

        # 输出各文件类型的处理结果汇总。
        print("\n各文件处理结果:")
        # 输出 IFIR Detail 处理状态和行数。
        print(f"  IFIR Detail: {task.ifir_detail_status}, 行数: {task.ifir_detail_rows}")
        # 输出 IFIR Row 处理状态和行数。
        print(f"  IFIR Row: {task.ifir_row_status}, 行数: {task.ifir_row_rows}")
        # 输出 RA Detail 处理状态和行数。
        print(f"  RA Detail: {task.ra_detail_status}, 行数: {task.ra_detail_rows}")
        # 输出 RA Row 处理状态和行数。
        print(f"  RA Row: {task.ra_row_status}, 行数: {task.ra_row_rows}")
    except Exception as error:
        # 输出异常摘要信息。
        print(f"测试失败: {str(error)}")
        # 在异常分支中导入 traceback，保持顶部导入简洁。
        import traceback

        # 打印完整异常堆栈。
        traceback.print_exc()
    finally:
        # 无论成功与否都关闭数据库会话。
        db.close()


# 仅在直接运行脚本时执行 ETL 测试。
if __name__ == "__main__":
    # 执行 ETL 测试入口函数。
    test_etl()
