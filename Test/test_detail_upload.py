# -*- coding: utf-8 -*-
"""
Detail数据上传测试脚本
测试 IFIR Detail / RA Detail 数据上传到数据库的完整链路
"""
import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, date
from sqlalchemy import create_engine, text

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings

# ============================================================
# 步骤1: 数据库连接检查
# ============================================================
def step1_check_database():
    """检查数据库连接和表状态"""
    print("\n" + "="*60)
    print("步骤1: 数据库连接检查")
    print("="*60)
    
    settings = get_settings()
    print(f"数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # 检查MySQL版本
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"[OK] MySQL版本: {version}")
            
            # 检查表
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            print(f"[OK] 数据库中共 {len(tables)} 张表")
            
            # 检查关键表
            required_tables = ['fact_ifir_detail', 'fact_ra_detail', 'upload_task']
            for table in required_tables:
                if table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"    - {table}: {count} 条记录")
                else:
                    print(f"    - {table}: [ERROR] 表不存在!")
                    return False
            
            return True
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False

# ============================================================
# 步骤2: 创建测试Excel文件
# ============================================================
def step2_create_test_files():
    """创建测试用的Excel文件"""
    print("\n" + "="*60)
    print("步骤2: 创建测试Excel文件")
    print("="*60)
    
    test_dir = os.path.join(os.path.dirname(__file__), "test_data")
    os.makedirs(test_dir, exist_ok=True)
    
    # IFIR Detail 测试数据
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
        "Cust_Nbr": ["CUST001", "CUST002", "CUST003"]
    }
    
    ifir_detail_path = os.path.join(test_dir, "test_ifir_detail.xlsx")
    df_ifir = pd.DataFrame(ifir_detail_data)
    df_ifir.to_excel(ifir_detail_path, index=False)
    print(f"[OK] 创建 IFIR Detail 测试文件: {ifir_detail_path}")
    print(f"    - 数据量: {len(df_ifir)} 条")
    
    # RA Detail 测试数据 (类似结构，但没有Delivery相关字段)
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
        "Cust_Nbr": ["CUST101", "CUST102", "CUST103"]
    }
    
    ra_detail_path = os.path.join(test_dir, "test_ra_detail.xlsx")
    df_ra = pd.DataFrame(ra_detail_data)
    df_ra.to_excel(ra_detail_path, index=False)
    print(f"[OK] 创建 RA Detail 测试文件: {ra_detail_path}")
    print(f"    - 数据量: {len(df_ra)} 条")
    
    return ifir_detail_path, ra_detail_path

# ============================================================
# 步骤3: 调用上传API
# ============================================================
def step3_upload_files(ifir_path, ra_path):
    """调用上传API"""
    print("\n" + "="*60)
    print("步骤3: 调用上传API")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    # 上传IFIR Detail
    print("\n--- 上传 IFIR Detail ---")
    try:
        with open(ifir_path, 'rb') as f:
            files = {'ifir_detail': ('test_ifir_detail.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f"{base_url}/api/upload", files=files, timeout=30)
        
        print(f"HTTP状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if result.get('code') == 0 and result.get('data'):
            ifir_task_id = result['data']['task_id']
            print(f"[OK] IFIR上传成功，task_id: {ifir_task_id}")
        else:
            print(f"[ERROR] IFIR上传失败: {result.get('message')}")
            ifir_task_id = None
    except Exception as e:
        print(f"[ERROR] IFIR上传异常: {e}")
        ifir_task_id = None
    
    # 上传RA Detail
    print("\n--- 上传 RA Detail ---")
    try:
        with open(ra_path, 'rb') as f:
            files = {'ra_detail': ('test_ra_detail.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f"{base_url}/api/upload", files=files, timeout=30)
        
        print(f"HTTP状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if result.get('code') == 0 and result.get('data'):
            ra_task_id = result['data']['task_id']
            print(f"[OK] RA上传成功，task_id: {ra_task_id}")
        else:
            print(f"[ERROR] RA上传失败: {result.get('message')}")
            ra_task_id = None
    except Exception as e:
        print(f"[ERROR] RA上传异常: {e}")
        ra_task_id = None
    
    return ifir_task_id, ra_task_id

# ============================================================
# 步骤4: 查询任务状态并等待完成
# ============================================================
def step4_wait_for_completion(task_id, name, max_wait=60):
    """等待任务完成"""
    if not task_id:
        return False
    
    print(f"\n--- 等待 {name} 任务完成 (task_id: {task_id}) ---")
    base_url = "http://localhost:8000"
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/api/upload/{task_id}/status", timeout=10)
            result = response.json()
            
            if result.get('code') == 0 and result.get('data'):
                status = result['data']['status']
                progress = result['data']['progress']
                print(f"  状态: {status}, 进度: {progress}%")
                
                if status == 'completed':
                    print(f"[OK] {name} 任务完成!")
                    # 打印详细结果
                    data = result['data']
                    if data.get('ifir_detail'):
                        print(f"    - IFIR Detail: {data['ifir_detail'].get('rows', 0)} 行")
                    if data.get('ra_detail'):
                        print(f"    - RA Detail: {data['ra_detail'].get('rows', 0)} 行")
                    return True
                elif status == 'failed':
                    print(f"[ERROR] {name} 任务失败: {result['data'].get('error_message')}")
                    return False
        except Exception as e:
            print(f"  查询异常: {e}")
        
        time.sleep(2)
    
    print(f"[ERROR] {name} 任务超时")
    return False

# ============================================================
# 步骤5: 验证数据库写入结果
# ============================================================
def step5_verify_database():
    """验证数据是否写入数据库"""
    print("\n" + "="*60)
    print("步骤5: 验证数据库写入结果")
    print("="*60)
    
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 检查IFIR Detail
        print("\n--- IFIR Detail 表 ---")
        result = conn.execute(text("SELECT COUNT(*) FROM fact_ifir_detail WHERE claim_nbr LIKE 'TEST_IFIR_%'"))
        count = result.fetchone()[0]
        print(f"测试数据量: {count} 条")
        
        if count > 0:
            result = conn.execute(text("SELECT claim_nbr, claim_month, plant, model, fault_category FROM fact_ifir_detail WHERE claim_nbr LIKE 'TEST_IFIR_%' LIMIT 5"))
            rows = result.fetchall()
            print("样本数据:")
            for row in rows:
                print(f"  {row}")
        
        # 检查RA Detail
        print("\n--- RA Detail 表 ---")
        result = conn.execute(text("SELECT COUNT(*) FROM fact_ra_detail WHERE claim_nbr LIKE 'TEST_RA_%'"))
        count = result.fetchone()[0]
        print(f"测试数据量: {count} 条")
        
        if count > 0:
            result = conn.execute(text("SELECT claim_nbr, claim_month, plant, model, fault_category FROM fact_ra_detail WHERE claim_nbr LIKE 'TEST_RA_%' LIMIT 5"))
            rows = result.fetchall()
            print("样本数据:")
            for row in rows:
                print(f"  {row}")
        
        # 检查upload_task表
        print("\n--- Upload Task 表 (最近5条) ---")
        result = conn.execute(text("SELECT task_id, status, progress, ifir_detail_rows, ra_detail_rows FROM upload_task ORDER BY created_at DESC LIMIT 5"))
        rows = result.fetchall()
        for row in rows:
            print(f"  {row}")

# ============================================================
# 主函数
# ============================================================
def main():
    print("="*60)
    print("Detail数据上传测试")
    print("测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # 步骤1: 数据库检查
    if not step1_check_database():
        print("\n[FAILED] 数据库检查失败，终止测试")
        return False
    
    # 步骤2: 创建测试文件
    ifir_path, ra_path = step2_create_test_files()
    
    # 步骤3: 上传文件
    ifir_task_id, ra_task_id = step3_upload_files(ifir_path, ra_path)
    
    # 步骤4: 等待完成
    ifir_ok = step4_wait_for_completion(ifir_task_id, "IFIR Detail")
    ra_ok = step4_wait_for_completion(ra_task_id, "RA Detail")
    
    # 步骤5: 验证数据库
    step5_verify_database()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"IFIR Detail 上传: {'[OK]' if ifir_ok else '[FAILED]'}")
    print(f"RA Detail 上传: {'[OK]' if ra_ok else '[FAILED]'}")
    
    if ifir_ok and ra_ok:
        print("\n[SUCCESS] 所有测试通过!")
        return True
    else:
        print("\n[FAILED] 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
