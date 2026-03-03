# -*- coding: utf-8 -*-
"""
Detail 数据上传测试脚本。
用于验证 IFIR Detail / RA Detail 数据从生成测试文件到写入数据库的完整链路。
"""
# 导入文件路径处理所需的库。
import os
# 导入进程退出所需的库。
import sys
# 导入轮询等待所需的库。
import time
# 导入发送 HTTP 请求所需的库。
import requests
# 导入构造测试 Excel 数据所需的库。
import pandas as pd
# 导入时间工具，便于记录测试开始时间。
from datetime import datetime, date
# 导入数据库连接与 SQL 执行工具。
from sqlalchemy import create_engine, text

# 将当前测试目录加入模块搜索路径，确保可以导入项目代码。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入项目配置读取函数。
from app.core.config import get_settings


def step1_check_database():
    '''
    功能概述：
    检查数据库连接是否可用，并确认明细上传链路依赖的关键表已经存在。

    输入参数：
    - 无，使用项目配置中的数据库连接信息。

    返回值：
    - `bool`：连接成功且关键表存在时返回 `True`，否则返回 `False`。

    关键流程：
    - 读取数据库配置。
    - 连接数据库并读取 MySQL 版本。
    - 列出当前库中的表。
    - 检查 `fact_ifir_detail`、`fact_ra_detail`、`upload_task` 的存在性与记录数。

    异常/边界：
    - 数据库不可达或 SQL 执行失败时会进入异常分支。
    - 任一关键表缺失时会直接返回 `False`。

    依赖：
    - `sqlalchemy`
    - `app.core.config.get_settings`

    示例：
    - `if not step1_check_database(): return False`
    '''
    # 打印步骤标题。
    print("\n" + "=" * 60)
    # 提示进入数据库检查步骤。
    print("步骤1: 数据库连接检查")
    # 输出分隔线。
    print("=" * 60)

    # 读取数据库配置。
    settings = get_settings()
    # 输出当前目标数据库位置。
    print(f"数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    # 使用异常处理包装数据库检查流程。
    try:
        # 创建数据库引擎。
        engine = create_engine(settings.DATABASE_URL)
        # 打开数据库连接。
        with engine.connect() as conn:
            # 查询 MySQL 版本，验证连接可用。
            result = conn.execute(text("SELECT VERSION()"))
            # 读取版本字符串。
            version = result.fetchone()[0]
            # 输出数据库版本。
            print(f"[OK] MySQL版本: {version}")

            # 列出当前数据库中的所有表。
            result = conn.execute(text("SHOW TABLES"))
            # 提取表名列表。
            tables = [row[0] for row in result.fetchall()]
            # 输出表数量。
            print(f"[OK] 数据库中共 {len(tables)} 张表")

            # 定义明细上传链路依赖的关键表。
            required_tables = ["fact_ifir_detail", "fact_ra_detail", "upload_task"]
            # 逐个检查关键表。
            for table in required_tables:
                # 如果关键表存在，则统计记录数。
                if table in tables:
                    # 查询当前表的记录数。
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    # 读取统计结果。
                    count = result.fetchone()[0]
                    # 输出记录数。
                    print(f"    - {table}: {count} 条记录")
                else:
                    # 输出缺表提示。
                    print(f"    - {table}: [ERROR] 表不存在!")
                    # 提前返回失败结果。
                    return False

            # 所有检查通过后返回成功。
            return True
    except Exception as error:
        # 输出异常信息。
        print(f"[ERROR] 数据库连接失败: {error}")
        # 返回失败结果。
        return False


def step2_create_test_files():
    '''
    功能概述：
    生成用于上传测试的 IFIR Detail 和 RA Detail Excel 文件，并写入 `Test/test_data` 目录。

    输入参数：
    - 无，测试数据在函数内构造。

    返回值：
    - `tuple[str, str]`：依次返回 IFIR Detail 和 RA Detail 测试文件路径。

    关键流程：
    - 创建测试数据目录。
    - 构造 IFIR Detail 样例数据并写入 Excel。
    - 构造 RA Detail 样例数据并写入 Excel。
    - 返回两个文件路径供上传步骤使用。

    异常/边界：
    - 如果目录无写权限或 Excel 写入失败，异常会向上抛出。

    依赖：
    - `os`
    - `pandas`

    示例：
    - `ifir_path, ra_path = step2_create_test_files()`
    '''
    # 打印步骤标题。
    print("\n" + "=" * 60)
    # 提示进入测试文件创建步骤。
    print("步骤2: 创建测试Excel文件")
    # 输出分隔线。
    print("=" * 60)

    # 拼接测试数据目录路径。
    test_dir = os.path.join(os.path.dirname(__file__), "test_data")
    # 确保测试数据目录存在。
    os.makedirs(test_dir, exist_ok=True)

    # 构造 IFIR Detail 样例数据。
    ifir_detail_data = {
        "Claim_Nbr": ["TEST_IFIR_001", "TEST_IFIR_002", "TEST_IFIR_003"],
        "Claim_Month": ["2025-01-01", "2025-01-01", "2025-02-01"],
        "Claim_Date": ["2025-01-15", "2025-01-20", "2025-02-10"],
        "Delivery_Month": ["2024-12-01", "2024-12-01", "2025-01-01"],
        "Delivery_Day": [15, 20, 10],
        "Geo_2012": ["PRC", "PRC", "AP"],
        "Financial Region": ["China", "China", "Asia Pacific"],
        "PLANT": ["FOXCONN_SZ", "TPV_QINGDAO", "FOXCONN_SZ"],
        "Brand": ["Lenovo", "Lenovo", "Lenovo"],
        "Segment": ["Consumer", "Commercial", "Consumer"],
        "Segment2": ["Desktop", "Laptop", "Desktop"],
        "Style": ["Tower", "Notebook", "Tower"],
        "Series": ["IdeaCentre", "ThinkPad", "IdeaCentre"],
        "Model": ["IC5-14IOB6", "T14 Gen3", "IC5-14IOB6"],
        "MTM": ["90RJ001UUS", "21AH00THUS", "90RJ001UUS"],
        "Serial_Nbr": ["SN001", "SN002", "SN003"],
        "StationName": ["Beijing Service Center", "Shanghai Service Center", "Guangzhou Service Center"],
        "Station_ID": [1001, 1002, 1003],
        "Data_Source": ["CRM", "CRM", "CRM"],
        "LastSln": ["Replaced motherboard", "Replaced battery", "Replaced power supply"],
        "Failure_Code": ["HW001", "HW002", "HW001"],
        "Fault_Category": ["Hardware", "Battery", "Power"],
        "Mach_Desc": ["Desktop PC", "Laptop", "Desktop PC"],
        "Problem_Descr": ["No power", "Battery drain", "Random shutdown"],
        "Problem_Descr_by_Tech": ["PSU failure", "Battery defect", "PSU unstable"],
        "Commodity": ["Motherboard", "Battery", "PSU"],
        "Down_Part_Code": ["MB001", "BAT001", "PSU001"],
        "Part_Nbr": ["5B20U53728", "5B10W13933", "5B20U53729"],
        "Part_desc": ["Motherboard IdeaCentre", "Battery 3cell", "Power Supply Unit"],
        "Part_Supplier": ["FOXCONN", "LG", "DELTA"],
        "Part_Barcode": ["BC001", "BC002", "BC003"],
        "Packing_Lot_No": ["LOT2024001", "LOT2024002", "LOT2024003"],
        "Claim_Item_Nbr": ["ITEM001", "ITEM002", "ITEM003"],
        "Claim_Status": ["Closed", "Closed", "Open"],
        "Channel": ["Direct", "Partner", "Direct"],
        "Cust_Nbr": ["CUST001", "CUST002", "CUST003"],
    }

    # 拼接 IFIR Detail 测试文件路径。
    ifir_detail_path = os.path.join(test_dir, "test_ifir_detail.xlsx")
    # 用样例数据构造 DataFrame。
    df_ifir = pd.DataFrame(ifir_detail_data)
    # 将 IFIR Detail 样例数据写入 Excel。
    df_ifir.to_excel(ifir_detail_path, index=False)
    # 输出 IFIR Detail 文件创建结果。
    print(f"[OK] 创建 IFIR Detail 测试文件: {ifir_detail_path}")
    # 输出 IFIR Detail 数据量。
    print(f"    - 数据量: {len(df_ifir)} 条")

    # 构造 RA Detail 样例数据。
    ra_detail_data = {
        "Claim_Nbr": ["TEST_RA_001", "TEST_RA_002", "TEST_RA_003"],
        "Claim_Month": ["2025-01-01", "2025-01-01", "2025-02-01"],
        "Claim_Date": ["2025-01-15", "2025-01-20", "2025-02-10"],
        "Geo_2012": ["PRC", "PRC", "AP"],
        "Financial Region": ["China", "China", "Asia Pacific"],
        "PLANT": ["FOXCONN_SZ", "TPV_QINGDAO", "FOXCONN_SZ"],
        "Brand": ["Lenovo", "Lenovo", "Lenovo"],
        "Segment": ["Consumer", "Commercial", "Consumer"],
        "Segment2": ["Desktop", "Laptop", "Desktop"],
        "Style": ["Tower", "Notebook", "Tower"],
        "Series": ["IdeaCentre", "ThinkPad", "IdeaCentre"],
        "Model": ["IC5-14IOB6", "T14 Gen3", "IC5-14IOB6"],
        "MTM": ["90RJ001UUS", "21AH00THUS", "90RJ001UUS"],
        "Serial_Nbr": ["SN101", "SN102", "SN103"],
        "StationName": ["Beijing Service Center", "Shanghai Service Center", "Guangzhou Service Center"],
        "Station_ID": [1001, 1002, 1003],
        "Data_Source": ["CRM", "CRM", "CRM"],
        "LastSln": ["Replaced screen", "Replaced keyboard", "Replaced fan"],
        "Failure_Code": ["HW101", "HW102", "HW103"],
        "Fault_Category": ["Display", "Input", "Thermal"],
        "Mach_Desc": ["Desktop PC", "Laptop", "Desktop PC"],
        "Problem_Descr": ["Screen flicker", "Keys not working", "Overheating"],
        "Problem_Descr_by_Tech": ["LCD panel issue", "Keyboard failure", "Fan malfunction"],
        "Commodity": ["Display", "Keyboard", "Cooling"],
        "Down_Part_Code": ["LCD001", "KB001", "FAN001"],
        "Part_Nbr": ["5D10V82348", "5CB0U43573", "5F10S13934"],
        "Part_desc": ["LCD Panel 14inch", "Keyboard US", "Cooling Fan"],
        "Part_Supplier": ["BOE", "CHICONY", "DELTA"],
        "Part_Barcode": ["BC101", "BC102", "BC103"],
        "Packing_Lot_No": ["LOT2024101", "LOT2024102", "LOT2024103"],
        "Claim_Item_Nbr": ["ITEM101", "ITEM102", "ITEM103"],
        "Claim_Status": ["Closed", "Closed", "Open"],
        "Channel": ["Direct", "Partner", "Direct"],
        "Cust_Nbr": ["CUST101", "CUST102", "CUST103"],
    }

    # 拼接 RA Detail 测试文件路径。
    ra_detail_path = os.path.join(test_dir, "test_ra_detail.xlsx")
    # 用样例数据构造 DataFrame。
    df_ra = pd.DataFrame(ra_detail_data)
    # 将 RA Detail 样例数据写入 Excel。
    df_ra.to_excel(ra_detail_path, index=False)
    # 输出 RA Detail 文件创建结果。
    print(f"[OK] 创建 RA Detail 测试文件: {ra_detail_path}")
    # 输出 RA Detail 数据量。
    print(f"    - 数据量: {len(df_ra)} 条")

    # 返回两个测试文件的路径。
    return ifir_detail_path, ra_detail_path


def step3_upload_files(ifir_path, ra_path):
    '''
    功能概述：
    调用上传接口，分别提交 IFIR Detail 和 RA Detail 测试文件，并返回对应任务 ID。

    输入参数：
    - `ifir_path`：IFIR Detail 测试文件路径。
    - `ra_path`：RA Detail 测试文件路径。

    返回值：
    - `tuple[str | None, str | None]`：依次返回 IFIR 与 RA 上传任务 ID。

    关键流程：
    - 构造上传接口地址。
    - 依次上传 IFIR Detail 与 RA Detail 文件。
    - 解析响应并提取任务 ID。

    异常/边界：
    - 任一文件上传失败时，对应任务 ID 会返回 `None`，但不会中断另一个文件上传。

    依赖：
    - `requests`
    - 本地后端接口 `/api/upload`

    示例：
    - `ifir_task_id, ra_task_id = step3_upload_files(ifir_path, ra_path)`
    '''
    # 打印步骤标题。
    print("\n" + "=" * 60)
    # 提示进入上传调用步骤。
    print("步骤3: 调用上传API")
    # 输出分隔线。
    print("=" * 60)

    # 配置本地后端服务的访问地址。
    base_url = "http://localhost:8000"

    # 提示开始上传 IFIR Detail 文件。
    print("\n--- 上传 IFIR Detail ---")
    # 使用异常处理包装 IFIR 上传流程。
    try:
        # 以二进制只读模式打开 IFIR Detail 文件。
        with open(ifir_path, "rb") as file_handle:
            # 组装 IFIR 上传所需的 multipart 数据。
            files = {
                "ifir_detail": (
                    "test_ifir_detail.xlsx",
                    file_handle,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            # 调用上传接口提交 IFIR Detail 文件。
            response = requests.post(f"{base_url}/api/upload", files=files, timeout=30)

        # 输出 IFIR 上传的 HTTP 状态码。
        print(f"HTTP状态码: {response.status_code}")
        # 解析 IFIR 上传响应体。
        result = response.json()
        # 输出 IFIR 上传响应。
        print(f"响应: {result}")

        # 仅在上传成功且返回数据体时提取任务 ID。
        if result.get("code") == 0 and result.get("data"):
            # 读取 IFIR 上传任务 ID。
            ifir_task_id = result["data"]["task_id"]
            # 输出 IFIR 上传成功信息。
            print(f"[OK] IFIR上传成功，task_id: {ifir_task_id}")
        else:
            # 输出 IFIR 上传失败信息。
            print(f"[ERROR] IFIR上传失败: {result.get('message')}")
            # 记录 IFIR 任务 ID 为空。
            ifir_task_id = None
    except Exception as error:
        # 输出 IFIR 上传异常。
        print(f"[ERROR] IFIR上传异常: {error}")
        # 记录 IFIR 任务 ID 为空。
        ifir_task_id = None

    # 提示开始上传 RA Detail 文件。
    print("\n--- 上传 RA Detail ---")
    # 使用异常处理包装 RA 上传流程。
    try:
        # 以二进制只读模式打开 RA Detail 文件。
        with open(ra_path, "rb") as file_handle:
            # 组装 RA 上传所需的 multipart 数据。
            files = {
                "ra_detail": (
                    "test_ra_detail.xlsx",
                    file_handle,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            # 调用上传接口提交 RA Detail 文件。
            response = requests.post(f"{base_url}/api/upload", files=files, timeout=30)

        # 输出 RA 上传的 HTTP 状态码。
        print(f"HTTP状态码: {response.status_code}")
        # 解析 RA 上传响应体。
        result = response.json()
        # 输出 RA 上传响应。
        print(f"响应: {result}")

        # 仅在上传成功且返回数据体时提取任务 ID。
        if result.get("code") == 0 and result.get("data"):
            # 读取 RA 上传任务 ID。
            ra_task_id = result["data"]["task_id"]
            # 输出 RA 上传成功信息。
            print(f"[OK] RA上传成功，task_id: {ra_task_id}")
        else:
            # 输出 RA 上传失败信息。
            print(f"[ERROR] RA上传失败: {result.get('message')}")
            # 记录 RA 任务 ID 为空。
            ra_task_id = None
    except Exception as error:
        # 输出 RA 上传异常。
        print(f"[ERROR] RA上传异常: {error}")
        # 记录 RA 任务 ID 为空。
        ra_task_id = None

    # 返回两个上传任务 ID。
    return ifir_task_id, ra_task_id


def step4_wait_for_completion(task_id, name, max_wait=60):
    '''
    功能概述：
    轮询上传任务状态接口，等待指定任务完成，并输出处理结果摘要。

    输入参数：
    - `task_id`：待轮询的任务 ID。
    - `name`：当前任务的人类可读名称。
    - `max_wait`：最大等待秒数，默认 60 秒。

    返回值：
    - `bool`：任务成功完成返回 `True`，失败或超时返回 `False`。

    关键流程：
    - 若任务 ID 为空则直接返回。
    - 在超时窗口内循环查询任务状态。
    - 根据任务状态输出成功、失败或超时信息。

    异常/边界：
    - 状态查询异常不会中断轮询，只会打印错误并继续。
    - 若接口持续没有可用结果，会在超时后返回 `False`。

    依赖：
    - `time`
    - `requests`
    - 本地后端接口 `/api/upload/{task_id}/status`

    示例：
    - `step4_wait_for_completion(ifir_task_id, "IFIR Detail")`
    '''
    # 如果没有任务 ID，则直接返回失败。
    if not task_id:
        # 返回失败结果。
        return False

    # 输出当前等待的任务信息。
    print(f"\n--- 等待 {name} 任务完成 (task_id: {task_id}) ---")
    # 配置本地后端服务的访问地址。
    base_url = "http://localhost:8000"

    # 记录轮询开始时间。
    start_time = time.time()
    # 在超时窗口内持续轮询。
    while time.time() - start_time < max_wait:
        # 使用异常处理包装单次轮询。
        try:
            # 请求任务状态接口。
            response = requests.get(f"{base_url}/api/upload/{task_id}/status", timeout=10)
            # 解析响应体。
            result = response.json()

            # 仅在返回成功且存在数据体时继续处理。
            if result.get("code") == 0 and result.get("data"):
                # 读取当前任务状态。
                status = result["data"]["status"]
                # 读取当前任务进度。
                progress = result["data"]["progress"]
                # 输出当前状态和进度。
                print(f"  状态: {status}, 进度: {progress}%")

                # 当任务完成时打印处理结果并返回成功。
                if status == "completed":
                    # 输出任务完成提示。
                    print(f"[OK] {name} 任务完成!")
                    # 取出任务数据体。
                    data = result["data"]
                    # 如果存在 IFIR Detail 结果，则输出导入行数。
                    if data.get("ifir_detail"):
                        print(f"    - IFIR Detail: {data['ifir_detail'].get('rows', 0)} 行")
                    # 如果存在 RA Detail 结果，则输出导入行数。
                    if data.get("ra_detail"):
                        print(f"    - RA Detail: {data['ra_detail'].get('rows', 0)} 行")
                    # 返回成功结果。
                    return True

                # 当任务失败时输出错误并返回失败。
                if status == "failed":
                    # 输出失败原因。
                    print(f"[ERROR] {name} 任务失败: {result['data'].get('error_message')}")
                    # 返回失败结果。
                    return False
        except Exception as error:
            # 输出本次轮询异常。
            print(f"  查询异常: {error}")

        # 每轮轮询之间等待 2 秒。
        time.sleep(2)

    # 超过等待上限后输出超时信息。
    print(f"[ERROR] {name} 任务超时")
    # 返回失败结果。
    return False


def step5_verify_database():
    '''
    功能概述：
    在上传任务结束后，直接查询数据库，验证测试数据是否已经落表并检查最近任务记录。

    输入参数：
    - 无。

    返回值：
    - 无，结果直接输出到控制台。

    关键流程：
    - 连接数据库。
    - 查询 IFIR Detail 测试数据数量及样本行。
    - 查询 RA Detail 测试数据数量及样本行。
    - 查询最近的上传任务记录。

    异常/边界：
    - 本函数未单独捕获异常，数据库异常会直接向上抛出。

    依赖：
    - `sqlalchemy`
    - `app.core.config.get_settings`

    示例：
    - `step5_verify_database()`
    '''
    # 打印步骤标题。
    print("\n" + "=" * 60)
    # 提示进入数据库校验步骤。
    print("步骤5: 验证数据库写入结果")
    # 输出分隔线。
    print("=" * 60)

    # 读取数据库配置。
    settings = get_settings()
    # 创建数据库引擎。
    engine = create_engine(settings.DATABASE_URL)

    # 打开数据库连接。
    with engine.connect() as conn:
        # 输出 IFIR Detail 表检查标题。
        print("\n--- IFIR Detail 表 ---")
        # 查询 IFIR Detail 测试数据量。
        result = conn.execute(text("SELECT COUNT(*) FROM fact_ifir_detail WHERE claim_nbr LIKE 'TEST_IFIR_%'"))
        # 读取统计结果。
        count = result.fetchone()[0]
        # 输出 IFIR Detail 测试数据量。
        print(f"测试数据量: {count} 条")

        # 仅在存在测试数据时读取样本行。
        if count > 0:
            # 查询 IFIR Detail 样本数据。
            result = conn.execute(
                text(
                    "SELECT claim_nbr, claim_month, plant, model, fault_category "
                    "FROM fact_ifir_detail WHERE claim_nbr LIKE 'TEST_IFIR_%' LIMIT 5"
                )
            )
            # 读取样本行。
            rows = result.fetchall()
            # 输出样本标题。
            print("样本数据:")
            # 逐行打印样本数据。
            for row in rows:
                # 输出单条样本记录。
                print(f"  {row}")

        # 输出 RA Detail 表检查标题。
        print("\n--- RA Detail 表 ---")
        # 查询 RA Detail 测试数据量。
        result = conn.execute(text("SELECT COUNT(*) FROM fact_ra_detail WHERE claim_nbr LIKE 'TEST_RA_%'"))
        # 读取统计结果。
        count = result.fetchone()[0]
        # 输出 RA Detail 测试数据量。
        print(f"测试数据量: {count} 条")

        # 仅在存在测试数据时读取样本行。
        if count > 0:
            # 查询 RA Detail 样本数据。
            result = conn.execute(
                text(
                    "SELECT claim_nbr, claim_month, plant, model, fault_category "
                    "FROM fact_ra_detail WHERE claim_nbr LIKE 'TEST_RA_%' LIMIT 5"
                )
            )
            # 读取样本行。
            rows = result.fetchall()
            # 输出样本标题。
            print("样本数据:")
            # 逐行打印样本数据。
            for row in rows:
                # 输出单条样本记录。
                print(f"  {row}")

        # 输出最近上传任务标题。
        print("\n--- Upload Task 表 (最近5条) ---")
        # 查询最近 5 条上传任务记录。
        result = conn.execute(
            text(
                "SELECT task_id, status, progress, ifir_detail_rows, ra_detail_rows "
                "FROM upload_task ORDER BY created_at DESC LIMIT 5"
            )
        )
        # 读取查询结果。
        rows = result.fetchall()
        # 逐行输出最近任务记录。
        for row in rows:
            # 输出单条任务记录。
            print(f"  {row}")


def main():
    '''
    功能概述：
    串联执行数据库检查、测试文件生成、上传调用、状态轮询和落库校验，完成整条明细上传测试链路。

    输入参数：
    - 无。

    返回值：
    - `bool`：IFIR 和 RA 明细任务都成功时返回 `True`，否则返回 `False`。

    关键流程：
    - 打印测试头信息。
    - 依次执行五个测试步骤。
    - 输出最终总结。

    异常/边界：
    - 若步骤 1 失败，会立即终止后续步骤。
    - 步骤 5 的异常会继续向上抛出，保持失败可见。

    依赖：
    - 本模块的五个步骤函数。

    示例：
    - `success = main()`
    '''
    # 打印脚本级标题。
    print("=" * 60)
    # 提示当前正在执行明细上传测试。
    print("Detail数据上传测试")
    # 输出当前测试时间。
    print("测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # 输出分隔线。
    print("=" * 60)

    # 先执行数据库检查，不通过则直接终止测试。
    if not step1_check_database():
        # 输出终止原因。
        print("\n[FAILED] 数据库检查失败，终止测试")
        # 返回失败结果。
        return False

    # 创建上传所需的测试文件。
    ifir_path, ra_path = step2_create_test_files()

    # 调用上传接口，分别提交 IFIR 与 RA 明细文件。
    ifir_task_id, ra_task_id = step3_upload_files(ifir_path, ra_path)

    # 等待 IFIR Detail 任务完成并记录结果。
    ifir_ok = step4_wait_for_completion(ifir_task_id, "IFIR Detail")
    # 等待 RA Detail 任务完成并记录结果。
    ra_ok = step4_wait_for_completion(ra_task_id, "RA Detail")

    # 直接查询数据库验证写入结果。
    step5_verify_database()

    # 打印总结标题。
    print("\n" + "=" * 60)
    # 输出测试总结说明。
    print("测试总结")
    # 输出分隔线。
    print("=" * 60)
    # 输出 IFIR Detail 上传结果。
    print(f"IFIR Detail 上传: {'[OK]' if ifir_ok else '[FAILED]'}")
    # 输出 RA Detail 上传结果。
    print(f"RA Detail 上传: {'[OK]' if ra_ok else '[FAILED]'}")

    # 仅在两类任务都成功时返回成功。
    if ifir_ok and ra_ok:
        # 输出整体验证成功提示。
        print("\n[SUCCESS] 所有测试通过!")
        # 返回成功结果。
        return True

    # 输出部分测试失败提示。
    print("\n[FAILED] 部分测试失败")
    # 返回失败结果。
    return False


# 仅在直接运行脚本时执行完整上传测试链路。
if __name__ == "__main__":
    # 运行脚本入口函数。
    success = main()
    # 按测试结果返回进程状态码。
    sys.exit(0 if success else 1)
