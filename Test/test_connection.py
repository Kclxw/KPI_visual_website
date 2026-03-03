"""
测试数据库连接和基础 API 连通性。
"""
# 导入退出进程所需的库。
import sys
# 导入发送 HTTP 请求所需的库。
import requests
# 导入创建数据库连接和执行 SQL 所需的对象。
from sqlalchemy import create_engine, text
# 导入项目配置读取函数。
from app.core.config import get_settings


def test_database_connection():
    '''
    功能概述：
    验证数据库连接是否正常，并检查目标数据库及其表结构是否可访问。

    输入参数：
    - 无，使用项目配置中的数据库连接信息。

    返回值：
    - `bool`：数据库与目标库可访问时返回 `True`，否则返回 `False`。

    关键流程：
    - 读取数据库配置。
    - 连接数据库并读取 MySQL 版本。
    - 检查目标数据库是否存在。
    - 列出表并统计记录数。

    异常/边界：
    - 数据库不可达、权限不足或 SQL 执行失败时会进入异常分支。
    - 若目标数据库不存在，会直接返回 `False`。

    依赖：
    - `sqlalchemy`
    - `app.core.config.get_settings`

    示例：
    - `db_ok = test_database_connection()`
    '''
    # 打印当前测试分段的标题。
    print("=== 测试数据库连接 ===")
    # 读取数据库配置。
    settings = get_settings()
    # 输出当前数据库连接串，便于排查配置问题。
    print(f"数据库URL: {settings.DATABASE_URL}")

    # 使用异常处理包装整个数据库检查流程。
    try:
        # 创建数据库引擎。
        engine = create_engine(settings.DATABASE_URL)
        # 打开数据库连接。
        with engine.connect() as conn:
            # 查询 MySQL 版本，验证数据库可正常响应。
            result = conn.execute(text("SELECT VERSION()"))
            # 读取版本字符串。
            version = result.fetchone()[0]
            # 输出连接成功信息。
            print(f"[OK] 数据库连接成功！MySQL版本: {version}")

            # 查询目标数据库是否存在。
            result = conn.execute(text(f"SHOW DATABASES LIKE '{settings.DB_NAME}'"))
            # 仅在数据库存在时继续检查表结构。
            if result.fetchone():
                # 输出数据库存在信息。
                print(f"[OK] 数据库 {settings.DB_NAME} 存在")

                # 切换到目标数据库。
                conn.execute(text(f"USE {settings.DB_NAME}"))
                # 列出数据库中的所有表。
                result = conn.execute(text("SHOW TABLES"))
                # 提取表名列表。
                tables = [row[0] for row in result.fetchall()]
                # 输出当前数据库中的表。
                print(f"[OK] 数据库中的表: {', '.join(tables) if tables else '(无表)'}")

                # 仅在存在表时继续统计记录数。
                if tables:
                    # 逐表统计数据量。
                    for table in tables:
                        # 查询当前表的记录数。
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        # 读取统计结果。
                        count = result.fetchone()[0]
                        # 输出当前表的数据量。
                        print(f"  - {table}: {count} 条记录")
            else:
                # 输出数据库不存在的提示。
                print(f"[ERROR] 数据库 {settings.DB_NAME} 不存在")
                # 返回失败结果。
                return False
        # 所有检查通过后返回成功结果。
        return True
    except Exception as error:
        # 输出连接或 SQL 执行异常。
        print(f"[ERROR] 数据库连接失败: {error}")
        # 返回失败结果。
        return False


def test_api_endpoints():
    '''
    功能概述：
    验证根路由、健康检查和文档页等基础接口是否可访问。

    输入参数：
    - 无。

    返回值：
    - 无，结果直接输出到控制台。

    关键流程：
    - 定义待测试端点列表。
    - 逐个发起请求。
    - 输出状态码和根路由返回内容。

    异常/边界：
    - 任一端点请求失败时，只记录错误，不影响后续端点继续测试。

    依赖：
    - `requests`
    - 本地后端服务

    示例：
    - `test_api_endpoints()`
    '''
    # 打印当前测试分段的标题。
    print("\n=== 测试API端点 ===")
    # 配置本地后端服务的访问地址。
    base_url = "http://localhost:8000"

    # 定义需要测试的基础端点。
    endpoints = [
        ("/", "根路由"),
        ("/health", "健康检查"),
        ("/docs", "API文档"),
    ]

    # 逐个测试端点连通性。
    for path, name in endpoints:
        # 使用异常处理避免单个端点失败中断整轮测试。
        try:
            # 请求当前端点。
            response = requests.get(f"{base_url}{path}", timeout=5)
            # 仅在返回 200 时视为正常。
            if response.status_code == 200:
                # 输出当前端点测试成功。
                print(f"[OK] {name} ({path}): OK")
                # 根路由额外打印返回 JSON，便于确认服务元信息。
                if path == "/":
                    print(f"  响应: {response.json()}")
            else:
                # 输出非 200 状态码。
                print(f"[ERROR] {name} ({path}): HTTP {response.status_code}")
        except Exception as error:
            # 输出请求异常信息。
            print(f"[ERROR] {name} ({path}): {error}")


# 仅在直接运行脚本时执行数据库和接口检查。
if __name__ == "__main__":
    # 打印脚本标题。
    print("KPI可视化系统 - 连接测试\n")

    # 执行数据库连接检查并保存结果。
    db_ok = test_database_connection()

    # 执行基础 API 端点测试。
    test_api_endpoints()

    # 打印整体测试完成标识。
    print("\n=== 测试完成 ===")
    # 根据数据库检查结果给出最终提示。
    if db_ok:
        # 输出成功提示。
        print("[OK] 数据库连接正常，可以进行数据导入测试")
    else:
        # 输出失败提示。
        print("[ERROR] 数据库连接失败，请检查配置")
        # 以失败状态码退出。
        sys.exit(1)
