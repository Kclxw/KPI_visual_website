"""
测试分析 API 的手工验证脚本。
"""
# 导入发送 HTTP 请求所需的库。
import requests
# 导入 JSON 库，便于后续按需扩展调试输出。
import json

# 配置本地后端服务的访问地址。
BASE_URL = "http://localhost:8000"


def test_ifir_odm_analyze():
    '''
    功能概述：
    向 IFIR ODM 分析接口发送固定测试请求，并打印关键返回字段，便于快速确认接口是否可用。

    输入参数：
    - 无，使用脚本内置的时间范围与 ODM 列表。

    返回值：
    - 无，结果直接输出到控制台。

    关键流程：
    - 构造请求体。
    - 调用 IFIR ODM 分析接口。
    - 解析响应并打印摘要、卡片数量和部分样例数据。

    异常/边界：
    - 如果服务未启动或接口返回非 JSON，`requests` 或 `json()` 会直接抛出异常。
    - 当响应中没有 `data` 字段时，只输出状态码和消息。

    依赖：
    - `requests`
    - 本地后端接口 `/api/ifir/odm-analysis/analyze`

    示例：
    - 运行 `python Test/test_analyze.py`
    '''
    # 打印当前测试分段的标题。
    print("=" * 50)
    # 提示正在执行 IFIR ODM 分析测试。
    print("测试 IFIR ODM 分析")

    # 构造固定的测试请求体。
    data = {
        "time_range": {"start_month": "2024-01", "end_month": "2025-12"},
        "filters": {"odms": ["FOXCONN", "TPV"]},
    }

    # 调用 IFIR ODM 分析接口。
    response = requests.post(f"{BASE_URL}/api/ifir/odm-analysis/analyze", json=data)
    # 将响应体解析为字典。
    result = response.json()

    # 输出业务状态码。
    print(f"  code: {result.get('code')}")
    # 输出业务消息。
    print(f"  message: {result.get('message')}")

    # 仅在接口返回数据体时继续打印明细。
    if result.get("data"):
        # 取出分析结果主体。
        payload = result["data"]
        # 输出卡片数量。
        print(f"  cards: {len(payload.get('cards', []))}")

        # 如果存在汇总信息，则打印饼图项目数量。
        if payload.get("summary"):
            print(f"  summary.odm_pie: {len(payload['summary'].get('odm_pie', []))}")

        # 遍历每张卡片，检查趋势和 Top 机型数据。
        for card in payload.get("cards", []):
            # 输出当前卡片对应的 ODM。
            print(f"\n  ODM: {card['odm']}")
            # 输出趋势点数量。
            print(f"    trend points: {len(card['trend'])}")
            # 输出 Top 机型数量。
            print(f"    top models: {len(card['top_models'])}")

            # 仅在存在趋势数据时打印最近 3 个点。
            if card["trend"]:
                print(f"    Last 3 trends: {card['trend'][-3:]}")

            # 仅在存在 Top 机型时打印前 3 条样例。
            if card["top_models"]:
                print(f"    Top models: {card['top_models'][:3]}")


def test_ra_odm_analyze():
    '''
    功能概述：
    向 RA ODM 分析接口发送固定测试请求，并打印核心返回字段，用于与 IFIR 分析接口进行并行验证。

    输入参数：
    - 无，使用脚本内置的时间范围与 ODM 列表。

    返回值：
    - 无，结果直接输出到控制台。

    关键流程：
    - 构造请求体。
    - 调用 RA ODM 分析接口。
    - 输出状态码、消息和卡片核心内容。

    异常/边界：
    - 接口异常、服务未启动或返回非 JSON 时会直接抛出异常。
    - 当响应缺少 `data` 字段时，脚本不会继续遍历卡片。

    依赖：
    - `requests`
    - 本地后端接口 `/api/ra/odm-analysis/analyze`

    示例：
    - 运行 `python Test/test_analyze.py`
    '''
    # 在第二段测试前补一个空行并打印分隔线。
    print("\n" + "=" * 50)
    # 提示正在执行 RA ODM 分析测试。
    print("测试 RA ODM 分析")

    # 构造固定的测试请求体。
    data = {
        "time_range": {"start_month": "2024-01", "end_month": "2025-12"},
        "filters": {"odms": ["FOXCONN", "TPV"]},
    }

    # 调用 RA ODM 分析接口。
    response = requests.post(f"{BASE_URL}/api/ra/odm-analysis/analyze", json=data)
    # 将响应体解析为字典。
    result = response.json()

    # 输出业务状态码。
    print(f"  code: {result.get('code')}")
    # 输出业务消息。
    print(f"  message: {result.get('message')}")

    # 仅在接口返回数据体时继续打印卡片信息。
    if result.get("data"):
        # 取出分析结果主体。
        payload = result["data"]
        # 输出卡片数量。
        print(f"  cards: {len(payload.get('cards', []))}")

        # 遍历每张卡片，检查趋势和 Top 机型数据。
        for card in payload.get("cards", []):
            # 输出当前卡片对应的 ODM。
            print(f"\n  ODM: {card['odm']}")
            # 输出趋势点数量。
            print(f"    trend points: {len(card['trend'])}")
            # 输出 Top 机型数量。
            print(f"    top models: {len(card['top_models'])}")

            # 仅在存在趋势数据时打印最近 3 个点。
            if card["trend"]:
                print(f"    Last 3 trends: {card['trend'][-3:]}")


# 仅在直接运行脚本时执行全部测试。
if __name__ == "__main__":
    # 运行 IFIR ODM 分析测试。
    test_ifir_odm_analyze()
    # 运行 RA ODM 分析测试。
    test_ra_odm_analyze()
    # 打印整体完成分隔线。
    print("\n" + "=" * 50)
    # 提示脚本执行结束。
    print("测试完成")
