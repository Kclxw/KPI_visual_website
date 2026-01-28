"""
API测试脚本
"""
import requests
import os

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("=" * 50)
    print("1. 测试健康检查")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"   状态码: {resp.status_code}")
    print(f"   响应: {resp.json()}")
    return resp.status_code == 200

def test_upload():
    """测试文件上传"""
    print("=" * 50)
    print("2. 测试文件上传")
    
    test_data_dir = "../test_data"
    files = {}
    
    # 检查并添加文件
    ifir_row = os.path.join(test_data_dir, "IFIR ROW.xlsx")
    ifir_detail = os.path.join(test_data_dir, "IFIR DETAIL.xlsx")
    ra_row = os.path.join(test_data_dir, "RA row.xlsx")
    ra_detail = os.path.join(test_data_dir, "RA DETAIL.xlsx")
    
    upload_files = {}
    if os.path.exists(ifir_row):
        upload_files["ifir_row"] = ("IFIR ROW.xlsx", open(ifir_row, "rb"))
        print(f"   找到: {ifir_row}")
    if os.path.exists(ifir_detail):
        upload_files["ifir_detail"] = ("IFIR DETAIL.xlsx", open(ifir_detail, "rb"))
        print(f"   找到: {ifir_detail}")
    if os.path.exists(ra_row):
        upload_files["ra_row"] = ("RA row.xlsx", open(ra_row, "rb"))
        print(f"   找到: {ra_row}")
    if os.path.exists(ra_detail):
        upload_files["ra_detail"] = ("RA DETAIL.xlsx", open(ra_detail, "rb"))
        print(f"   找到: {ra_detail}")
    
    if not upload_files:
        print("   错误: 没有找到测试数据文件")
        return False
    
    print(f"   上传 {len(upload_files)} 个文件...")
    resp = requests.post(f"{BASE_URL}/api/upload", files=upload_files)
    print(f"   状态码: {resp.status_code}")
    result = resp.json()
    print(f"   响应: code={result.get('code')}, message={result.get('message')}")
    
    if result.get("data"):
        task_id = result["data"]["task_id"]
        print(f"   任务ID: {task_id}")
        return task_id
    return None

def check_upload_status(task_id):
    """检查上传状态"""
    print("=" * 50)
    print(f"3. 检查上传状态: {task_id}")
    
    import time
    for i in range(30):  # 最多等待30秒
        resp = requests.get(f"{BASE_URL}/api/upload/{task_id}/status")
        result = resp.json()
        
        if result.get("data"):
            status = result["data"]["status"]
            progress = result["data"]["progress"]
            print(f"   [{i+1}] 状态: {status}, 进度: {progress}%")
            
            if status == "completed":
                print("   上传完成!")
                return True
            elif status == "failed":
                print(f"   上传失败: {result['data'].get('error_message')}")
                return False
        
        time.sleep(1)
    
    print("   超时")
    return False

def test_ifir_options():
    """测试IFIR Options API"""
    print("=" * 50)
    print("4. 测试IFIR Options API")
    
    resp = requests.get(f"{BASE_URL}/api/ifir/odm-analysis/options")
    result = resp.json()
    print(f"   状态码: {resp.status_code}")
    print(f"   code: {result.get('code')}")
    
    if result.get("data"):
        data = result["data"]
        print(f"   月份范围: {data.get('month_min')} ~ {data.get('month_max')}")
        print(f"   Segments数: {len(data.get('segments', []))}")
        print(f"   ODMs数: {len(data.get('odms', []))}")
        print(f"   Models数: {len(data.get('models', []))}")
        return data
    return None

def test_ifir_analyze(options_data):
    """测试IFIR ODM分析API"""
    print("=" * 50)
    print("5. 测试IFIR ODM分析API")
    
    if not options_data:
        print("   跳过: 没有options数据")
        return
    
    odms = options_data.get("odms", [])[:2]  # 取前2个ODM
    if not odms:
        print("   跳过: 没有ODM数据")
        return
    
    request_data = {
        "time_range": {
            "start_month": options_data.get("month_min", "2024-01"),
            "end_month": options_data.get("month_max", "2024-12")
        },
        "filters": {
            "odms": odms
        }
    }
    
    print(f"   请求ODMs: {odms}")
    print(f"   时间范围: {request_data['time_range']}")
    
    resp = requests.post(f"{BASE_URL}/api/ifir/odm-analysis/analyze", json=request_data)
    result = resp.json()
    print(f"   状态码: {resp.status_code}")
    print(f"   code: {result.get('code')}")
    
    if result.get("data"):
        data = result["data"]
        print(f"   返回卡片数: {len(data.get('cards', []))}")
        for card in data.get("cards", []):
            print(f"     - ODM: {card['odm']}, 趋势点数: {len(card['trend'])}, Top Models: {len(card['top_models'])}")
    else:
        print(f"   错误: {result.get('message')}")

def test_ra_options():
    """测试RA Options API"""
    print("=" * 50)
    print("6. 测试RA Options API")
    
    resp = requests.get(f"{BASE_URL}/api/ra/odm-analysis/options")
    result = resp.json()
    print(f"   状态码: {resp.status_code}")
    print(f"   code: {result.get('code')}")
    
    if result.get("data"):
        data = result["data"]
        print(f"   月份范围: {data.get('month_min')} ~ {data.get('month_max')}")
        print(f"   Segments数: {len(data.get('segments', []))}")
        print(f"   ODMs数: {len(data.get('odms', []))}")
        print(f"   Models数: {len(data.get('models', []))}")
        return data
    return None

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("KPI Visual API 测试")
    print("=" * 50)
    
    # 1. 健康检查
    if not test_health():
        print("健康检查失败，退出")
        exit(1)
    
    # 2. 上传文件
    task_id = test_upload()
    
    # 3. 等待上传完成
    if task_id:
        check_upload_status(task_id)
    
    # 4. 测试IFIR Options
    ifir_options = test_ifir_options()
    
    # 5. 测试IFIR分析
    test_ifir_analyze(ifir_options)
    
    # 6. 测试RA Options
    test_ra_options()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
