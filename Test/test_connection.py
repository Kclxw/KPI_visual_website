"""
测试数据库连接和API
"""
import sys
import requests
from sqlalchemy import create_engine, text
from app.core.config import get_settings

def test_database_connection():
    """测试数据库连接"""
    print("=== 测试数据库连接 ===")
    settings = get_settings()
    print(f"数据库URL: {settings.DATABASE_URL}")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"[OK] 数据库连接成功！MySQL版本: {version}")
            
            # 检查数据库是否存在
            result = conn.execute(text(f"SHOW DATABASES LIKE '{settings.DB_NAME}'"))
            if result.fetchone():
                print(f"[OK] 数据库 {settings.DB_NAME} 存在")
                
                # 检查表
                result = conn.execute(text(f"USE {settings.DB_NAME}"))
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]
                print(f"[OK] 数据库中的表: {', '.join(tables) if tables else '(无表)'}")
                
                # 检查各表的数据量
                if tables:
                    for table in tables:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.fetchone()[0]
                        print(f"  - {table}: {count} 条记录")
            else:
                print(f"[ERROR] 数据库 {settings.DB_NAME} 不存在")
                return False
        return True
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点"""
    print("\n=== 测试API端点 ===")
    base_url = "http://localhost:8000"
    
    endpoints = [
        ("/", "根路由"),
        ("/health", "健康检查"),
        ("/docs", "API文档"),
    ]
    
    for path, name in endpoints:
        try:
            response = requests.get(f"{base_url}{path}", timeout=5)
            if response.status_code == 200:
                print(f"[OK] {name} ({path}): OK")
                if path == "/":
                    print(f"  响应: {response.json()}")
            else:
                print(f"[ERROR] {name} ({path}): HTTP {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {name} ({path}): {e}")

if __name__ == "__main__":
    print("KPI可视化系统 - 连接测试\n")
    
    # 测试数据库
    db_ok = test_database_connection()
    
    # 测试API
    test_api_endpoints()
    
    print("\n=== 测试完成 ===")
    if db_ok:
        print("[OK] 数据库连接正常，可以进行数据导入测试")
    else:
        print("[ERROR] 数据库连接失败，请检查配置")
        sys.exit(1)
