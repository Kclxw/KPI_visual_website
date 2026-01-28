"""
测试ETL - 直接运行，绕过后台任务
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.etl_service import EtlService
from app.models.tables import UploadTask

def test_etl():
    """测试ETL处理"""
    print("=" * 50)
    print("开始测试ETL")
    print("=" * 50)
    
    # 查找最新的上传任务
    db = SessionLocal()
    try:
        task = db.query(UploadTask).order_by(UploadTask.id.desc()).first()
        
        if not task:
            print("没有找到上传任务")
            return
        
        print(f"找到任务: {task.task_id}")
        print(f"状态: {task.status}")
        print(f"IFIR Detail: {task.ifir_detail_file}")
        print(f"IFIR Row: {task.ifir_row_file}")
        print(f"RA Detail: {task.ra_detail_file}")
        print(f"RA Row: {task.ra_row_file}")
        
        # 构建文件字典
        files = {}
        if task.ifir_detail_file and os.path.exists(task.ifir_detail_file):
            files["ifir_detail"] = task.ifir_detail_file
        if task.ifir_row_file and os.path.exists(task.ifir_row_file):
            files["ifir_row"] = task.ifir_row_file
        if task.ra_detail_file and os.path.exists(task.ra_detail_file):
            files["ra_detail"] = task.ra_detail_file
        if task.ra_row_file and os.path.exists(task.ra_row_file):
            files["ra_row"] = task.ra_row_file
        
        print(f"有效文件: {list(files.keys())}")
        
        if not files:
            print("没有找到有效的文件！")
            return
        
        # 重置任务状态
        task.status = "queued"
        task.progress = 0
        task.error_message = None
        db.commit()
        
        # 运行ETL
        print("\n开始运行ETL...")
        service = EtlService(db)
        service.process_upload_task(task.task_id, files)
        
        # 刷新任务状态
        db.refresh(task)
        print(f"\n最终状态: {task.status}")
        print(f"进度: {task.progress}%")
        if task.error_message:
            print(f"错误: {task.error_message}")
        
        print("\n各文件处理结果:")
        print(f"  IFIR Detail: {task.ifir_detail_status}, 行数: {task.ifir_detail_rows}")
        print(f"  IFIR Row: {task.ifir_row_status}, 行数: {task.ifir_row_rows}")
        print(f"  RA Detail: {task.ra_detail_status}, 行数: {task.ra_detail_rows}")
        print(f"  RA Row: {task.ra_row_status}, 行数: {task.ra_row_rows}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_etl()
