"""
API 测试脚本。
"""
# 导入发送 HTTP 请求所需的库。
import requests
# 导入文件路径处理所需的库。
import os

# 配置本地后端服务的访问地址。
BASE_URL = "http://localhost:8000"


def test_health():
    '''
    功能概述：
    调用健康检查接口，确认后端服务是否已经启动并可正常响应。

    输入参数：
    - 无。

    返回值：
    - `bool`：当 HTTP 状态码为 200 时返回 `True`，否则返回 `False`。

    关键流程：
    - 调用 `/health`。
    - 输出 HTTP 状态码与响应体。
    - 返回健康检查结果。

    异常/边界：
    - 如果服务未启动，`requests.get` 会直接抛出异常。

    依赖：
    - `requests`
    - 本地后端接口 `/health`

    示例：
    - 在主流程中作为所有测试的前置检查使用。
    '''
    # 打印当前测试分段的标题。
    print("=" * 50)
    # 提示正在执行健康检查。
    print("1. 测试健康检查")
    # 请求后端健康检查接口。
    response = requests.get(f"{BASE_URL}/health")
    # 输出 HTTP 状态码。
    print(f"   状态码: {response.status_code}")
    # 输出接口响应内容。
    print(f"   响应: {response.json()}")
    # 返回是否为成功状态码。
    return response.status_code == 200


def test_upload():
    '''
    功能概述：
    从测试数据目录收集可用 Excel 文件，并调用上传接口创建上传任务。

    输入参数：
    - 无，文件路径使用脚本内置相对路径。

    返回值：
    - `str | None | bool`：成功时返回任务 ID；无文件时返回 `False`；接口无任务数据时返回 `None`。

    关键流程：
    - 拼接测试文件路径。
    - 收集存在的测试文件。
    - 调用上传接口。
    - 输出任务 ID 供后续轮询使用。

    异常/边界：
    - 若没有任何测试文件，函数会提前返回 `False`。
    - 文件句柄沿用原脚本写法直接交给 `requests`，脚本结束前不会显式关闭。

    依赖：
    - `os`
    - `requests`
    - 本地后端接口 `/api/upload`

    示例：
    - `task_id = test_upload()`
    '''
    # 打印当前测试分段的标题。
    print("=" * 50)
    # 提示正在执行文件上传测试。
    print("2. 测试文件上传")

    # 定义测试数据目录的相对路径。
    test_data_dir = "../test_data"
    # 预留原脚本中的变量位，保持调用结构一致。
    files = {}

    # 拼接各类测试 Excel 文件路径。
    ifir_row = os.path.join(test_data_dir, "IFIR ROW.xlsx")
    # 拼接 IFIR Detail 文件路径。
    ifir_detail = os.path.join(test_data_dir, "IFIR DETAIL.xlsx")
    # 拼接 RA Row 文件路径。
    ra_row = os.path.join(test_data_dir, "RA row.xlsx")
    # 拼接 RA Detail 文件路径。
    ra_detail = os.path.join(test_data_dir, "RA DETAIL.xlsx")

    # 初始化真正用于上传的文件字典。
    upload_files = {}
    # 如果 IFIR Row 文件存在，则加入上传列表。
    if os.path.exists(ifir_row):
        # 保存上传字段名、文件名和文件句柄。
        upload_files["ifir_row"] = ("IFIR ROW.xlsx", open(ifir_row, "rb"))
        # 输出已找到的文件。
        print(f"   找到: {ifir_row}")
    # 如果 IFIR Detail 文件存在，则加入上传列表。
    if os.path.exists(ifir_detail):
        # 保存上传字段名、文件名和文件句柄。
        upload_files["ifir_detail"] = ("IFIR DETAIL.xlsx", open(ifir_detail, "rb"))
        # 输出已找到的文件。
        print(f"   找到: {ifir_detail}")
    # 如果 RA Row 文件存在，则加入上传列表。
    if os.path.exists(ra_row):
        # 保存上传字段名、文件名和文件句柄。
        upload_files["ra_row"] = ("RA row.xlsx", open(ra_row, "rb"))
        # 输出已找到的文件。
        print(f"   找到: {ra_row}")
    # 如果 RA Detail 文件存在，则加入上传列表。
    if os.path.exists(ra_detail):
        # 保存上传字段名、文件名和文件句柄。
        upload_files["ra_detail"] = ("RA DETAIL.xlsx", open(ra_detail, "rb"))
        # 输出已找到的文件。
        print(f"   找到: {ra_detail}")

    # 当没有任何可上传文件时提前终止测试。
    if not upload_files:
        # 输出缺少测试数据的提示。
        print("   错误: 没有找到测试数据文件")
        # 返回失败标记。
        return False

    # 输出即将上传的文件数量。
    print(f"   上传 {len(upload_files)} 个文件...")
    # 调用上传接口创建任务。
    response = requests.post(f"{BASE_URL}/api/upload", files=upload_files)
    # 输出 HTTP 状态码。
    print(f"   状态码: {response.status_code}")
    # 解析接口返回值。
    result = response.json()
    # 输出业务码和业务消息。
    print(f"   响应: code={result.get('code')}, message={result.get('message')}")

    # 仅在存在数据体时继续提取任务 ID。
    if result.get("data"):
        # 读取任务 ID。
        task_id = result["data"]["task_id"]
        # 输出任务 ID。
        print(f"   任务ID: {task_id}")
        # 返回任务 ID，供轮询接口使用。
        return task_id
    # 当返回体没有 data 时返回空值。
    return None


def check_upload_status(task_id):
    '''
    功能概述：
    轮询上传任务状态接口，直到任务完成、失败或达到超时上限。

    输入参数：
    - `task_id`：上传接口返回的任务标识。

    返回值：
    - `bool`：任务完成返回 `True`，任务失败或超时返回 `False`。

    关键流程：
    - 循环调用状态查询接口。
    - 输出任务状态与进度。
    - 根据最终状态返回结果。

    异常/边界：
    - 若接口始终不返回 `data`，函数会在 30 次轮询后超时。
    - `time` 仅在函数内部导入，避免污染模块顶部。

    依赖：
    - `requests`
    - 本地后端接口 `/api/upload/{task_id}/status`

    示例：
    - `check_upload_status(task_id)`
    '''
    # 打印当前测试分段的标题。
    print("=" * 50)
    # 输出正在轮询的任务 ID。
    print(f"3. 检查上传状态: {task_id}")

    # 延迟导入时间模块，沿用原脚本结构。
    import time

    # 最多轮询 30 次，每次间隔 1 秒。
    for index in range(30):
        # 请求任务状态接口。
        response = requests.get(f"{BASE_URL}/api/upload/{task_id}/status")
        # 解析接口响应。
        result = response.json()

        # 仅在存在数据体时继续读取状态信息。
        if result.get("data"):
            # 读取当前任务状态。
            status = result["data"]["status"]
            # 读取当前任务进度。
            progress = result["data"]["progress"]
            # 输出轮询序号、状态和进度。
            print(f"   [{index + 1}] 状态: {status}, 进度: {progress}%")

            # 如果任务已经完成，则直接返回成功。
            if status == "completed":
                # 输出成功提示。
                print("   上传完成!")
                # 返回成功结果。
                return True
            # 如果任务已经失败，则直接返回失败。
            if status == "failed":
                # 输出失败原因。
                print(f"   上传失败: {result['data'].get('error_message')}")
                # 返回失败结果。
                return False

        # 每次轮询后等待 1 秒再继续。
        time.sleep(1)

    # 超过轮询上限后输出超时提示。
    print("   超时")
    # 返回失败结果。
    return False


def test_ifir_options():
    '''
    功能概述：
    调用 IFIR 选项接口，读取月份范围以及下拉项数据，供后续分析接口复用。

    输入参数：
    - 无。

    返回值：
    - `dict | None`：成功时返回选项数据，失败时返回 `None`。

    关键流程：
    - 请求 IFIR 选项接口。
    - 输出月份范围和各维度数量。
    - 返回完整数据体。

    异常/边界：
    - 如果接口没有返回 `data`，则直接返回 `None`。

    依赖：
    - `requests`
    - 本地后端接口 `/api/ifir/odm-analysis/options`

    示例：
    - `options = test_ifir_options()`
    '''
    # 打印当前测试分段的标题。
    print("=" * 50)
    # 提示正在执行 IFIR 选项接口测试。
    print("4. 测试IFIR Options API")

    # 请求 IFIR 选项接口。
    response = requests.get(f"{BASE_URL}/api/ifir/odm-analysis/options")
    # 解析响应体。
    result = response.json()
    # 输出 HTTP 状态码。
    print(f"   状态码: {response.status_code}")
    # 输出业务状态码。
    print(f"   code: {result.get('code')}")

    # 仅在返回数据体时继续打印明细。
    if result.get("data"):
        # 取出选项数据。
        data = result["data"]
        # 输出月份范围。
        print(f"   月份范围: {data.get('month_min')} ~ {data.get('month_max')}")
        # 输出 Segment 数量。
        print(f"   Segments数: {len(data.get('segments', []))}")
        # 输出 ODM 数量。
        print(f"   ODMs数: {len(data.get('odms', []))}")
        # 输出 Model 数量。
        print(f"   Models数: {len(data.get('models', []))}")
        # 返回选项数据，供后续分析接口复用。
        return data
    # 当没有数据体时返回空值。
    return None


def test_ifir_analyze(options_data):
    '''
    功能概述：
    基于 IFIR 选项接口返回的数据，选择前两个 ODM 调用 IFIR 分析接口。

    输入参数：
    - `options_data`：由 `test_ifir_options` 返回的选项数据。

    返回值：
    - 无，结果直接输出到控制台。

    关键流程：
    - 校验选项数据是否可用。
    - 选取前两个 ODM 生成请求体。
    - 调用分析接口并打印卡片摘要。

    异常/边界：
    - 如果选项数据为空或 ODM 列表为空，会直接跳过。
    - 如果接口返回失败，只打印错误消息，不抛出自定义异常。

    依赖：
    - `requests`
    - 本地后端接口 `/api/ifir/odm-analysis/analyze`

    示例：
    - `test_ifir_analyze(ifir_options)`
    '''
    # 打印当前测试分段的标题。
    print("=" * 50)
    # 提示正在执行 IFIR 分析接口测试。
    print("5. 测试IFIR ODM分析API")

    # 如果没有选项数据，则跳过当前测试。
    if not options_data:
        # 输出跳过原因。
        print("   跳过: 没有options数据")
        # 直接结束函数。
        return

    # 仅取前两个 ODM 作为测试样本。
    odms = options_data.get("odms", [])[:2]
    # 如果没有可用 ODM，则跳过当前测试。
    if not odms:
        # 输出跳过原因。
        print("   跳过: 没有ODM数据")
        # 直接结束函数。
        return

    # 组装分析接口请求体。
    request_data = {
        "time_range": {
            "start_month": options_data.get("month_min", "2024-01"),
            "end_month": options_data.get("month_max", "2024-12"),
        },
        "filters": {"odms": odms},
    }

    # 输出当前请求使用的 ODM 列表。
    print(f"   请求ODMs: {odms}")
    # 输出当前请求使用的时间范围。
    print(f"   时间范围: {request_data['time_range']}")

    # 调用 IFIR 分析接口。
    response = requests.post(f"{BASE_URL}/api/ifir/odm-analysis/analyze", json=request_data)
    # 解析响应体。
    result = response.json()
    # 输出 HTTP 状态码。
    print(f"   状态码: {response.status_code}")
    # 输出业务状态码。
    print(f"   code: {result.get('code')}")

    # 仅在返回数据体时继续输出卡片摘要。
    if result.get("data"):
        # 取出分析数据体。
        data = result["data"]
        # 输出返回卡片数量。
        print(f"   返回卡片数: {len(data.get('cards', []))}")
        # 遍历每张卡片并打印核心摘要。
        for card in data.get("cards", []):
            # 输出卡片中的 ODM、趋势点数量和 Top 机型数量。
            print(f"     - ODM: {card['odm']}, 趋势点数: {len(card['trend'])}, Top Models: {len(card['top_models'])}")
    else:
        # 输出业务错误消息。
        print(f"   错误: {result.get('message')}")


def test_ra_options():
    '''
    功能概述：
    调用 RA 选项接口，验证月份范围和筛选项是否正常返回。

    输入参数：
    - 无。

    返回值：
    - `dict | None`：成功时返回选项数据，失败时返回 `None`。

    关键流程：
    - 请求 RA 选项接口。
    - 输出月份范围和各维度数量。
    - 返回接口数据体。

    异常/边界：
    - 当接口未返回 `data` 字段时返回 `None`。

    依赖：
    - `requests`
    - 本地后端接口 `/api/ra/odm-analysis/options`

    示例：
    - `ra_options = test_ra_options()`
    '''
    # 打印当前测试分段的标题。
    print("=" * 50)
    # 提示正在执行 RA 选项接口测试。
    print("6. 测试RA Options API")

    # 请求 RA 选项接口。
    response = requests.get(f"{BASE_URL}/api/ra/odm-analysis/options")
    # 解析响应体。
    result = response.json()
    # 输出 HTTP 状态码。
    print(f"   状态码: {response.status_code}")
    # 输出业务状态码。
    print(f"   code: {result.get('code')}")

    # 仅在返回数据体时继续打印明细。
    if result.get("data"):
        # 取出选项数据。
        data = result["data"]
        # 输出月份范围。
        print(f"   月份范围: {data.get('month_min')} ~ {data.get('month_max')}")
        # 输出 Segment 数量。
        print(f"   Segments数: {len(data.get('segments', []))}")
        # 输出 ODM 数量。
        print(f"   ODMs数: {len(data.get('odms', []))}")
        # 输出 Model 数量。
        print(f"   Models数: {len(data.get('models', []))}")
        # 返回选项数据。
        return data
    # 当没有数据体时返回空值。
    return None


# 仅在直接运行脚本时串行执行全部测试步骤。
if __name__ == "__main__":
    # 打印脚本级标题。
    print("\n" + "=" * 50)
    # 提示开始执行整套 API 测试。
    print("KPI Visual API 测试")
    # 输出分隔线。
    print("=" * 50)

    # 先执行健康检查，如果失败则直接退出。
    if not test_health():
        # 输出退出原因。
        print("健康检查失败，退出")
        # 以失败状态退出进程。
        exit(1)

    # 创建上传任务并拿到任务 ID。
    task_id = test_upload()

    # 仅在上传任务创建成功时才继续轮询状态。
    if task_id:
        # 轮询上传任务直到结束。
        check_upload_status(task_id)

    # 拉取 IFIR 选项，供后续分析接口复用。
    ifir_options = test_ifir_options()

    # 使用 IFIR 选项数据执行分析测试。
    test_ifir_analyze(ifir_options)

    # 执行 RA 选项接口测试。
    test_ra_options()

    # 打印测试结束分隔线。
    print("\n" + "=" * 50)
    # 提示整套测试执行完毕。
    print("测试完成")
    # 输出最终分隔线。
    print("=" * 50)
