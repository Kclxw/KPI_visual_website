"""
文件上传API路由
"""
import os
import uuid
import threading
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import require_uploader
from app.models.tables import UploadTask
from app.schemas.upload import UploadResponse, UploadTaskStatus, FileInfo
from app.services.etl_service import EtlService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["文件上传"], dependencies=[Depends(require_uploader)])

# 上传文件存储目录 - 使用绝对路径
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=UploadResponse)
async def upload_files(
    ifir_detail: Optional[UploadFile] = File(None, description="IFIR Detail Excel文件"),
    ifir_row: Optional[UploadFile] = File(None, description="IFIR Row Excel文件"),
    ra_detail: Optional[UploadFile] = File(None, description="RA Detail Excel文件"),
    ra_row: Optional[UploadFile] = File(None, description="RA Row Excel文件"),
    db: Session = Depends(get_db)
):
    """
    上传Excel数据文件
    
    支持同时上传多个文件，至少需要上传一个文件
    """
    logger.info("========== 收到文件上传请求 ==========")
    
    # 检查是否有文件上传
    files = {
        "ifir_detail": ifir_detail,
        "ifir_row": ifir_row,
        "ra_detail": ra_detail,
        "ra_row": ra_row
    }
    
    uploaded_files = {k: v for k, v in files.items() if v is not None}
    
    if not uploaded_files:
        return UploadResponse(code=400, message="请至少上传一个文件")
    
    # 创建任务ID
    task_id = str(uuid.uuid4())
    
    # 保存文件并创建任务记录
    try:
        task = UploadTask(
            task_id=task_id,
            status="queued",
            progress=0
        )
        
        saved_files = {}
        for file_type, file in uploaded_files.items():
            # 保存文件
            file_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file_type}_{file.filename}")
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            saved_files[file_type] = file_path
            logger.info(f"文件已保存: {file_type} -> {file_path}")
            
            # 更新任务记录
            setattr(task, f"{file_type}_file", file_path)
            setattr(task, f"{file_type}_status", "pending")
        
        db.add(task)
        db.commit()
        
        logger.info(f"任务已创建: {task_id}")
        logger.info(f"保存的文件: {list(saved_files.keys())}")
        
        # 使用线程执行ETL（替代 BackgroundTasks）
        thread = threading.Thread(target=process_upload, args=(task_id, saved_files), daemon=True)
        thread.start()
        logger.info(f"后台线程已启动: {task_id}")
        
        # 返回任务状态
        return UploadResponse(data=UploadTaskStatus(
            task_id=task_id,
            status="queued",
            progress=0,
            ifir_detail=FileInfo(filename=ifir_detail.filename, status="pending") if ifir_detail else None,
            ifir_row=FileInfo(filename=ifir_row.filename, status="pending") if ifir_row else None,
            ra_detail=FileInfo(filename=ra_detail.filename, status="pending") if ra_detail else None,
            ra_row=FileInfo(filename=ra_row.filename, status="pending") if ra_row else None,
            created_at=datetime.now()
        ))
        
    except Exception as e:
        logger.error(f"上传失败: {str(e)}", exc_info=True)
        return UploadResponse(code=500, message=f"文件上传失败: {str(e)}")


@router.get("/{task_id}/status", response_model=UploadResponse)
async def get_upload_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    查询上传任务状态
    """
    task = db.query(UploadTask).filter(UploadTask.task_id == task_id).first()
    
    if not task:
        return UploadResponse(code=404, message="任务不存在")
    
    return UploadResponse(data=UploadTaskStatus(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        ifir_detail=FileInfo(
            filename=os.path.basename(task.ifir_detail_file) if task.ifir_detail_file else "",
            status=task.ifir_detail_status or "pending",
            rows=task.ifir_detail_rows
        ) if task.ifir_detail_file else None,
        ifir_row=FileInfo(
            filename=os.path.basename(task.ifir_row_file) if task.ifir_row_file else "",
            status=task.ifir_row_status or "pending",
            rows=task.ifir_row_rows
        ) if task.ifir_row_file else None,
        ra_detail=FileInfo(
            filename=os.path.basename(task.ra_detail_file) if task.ra_detail_file else "",
            status=task.ra_detail_status or "pending",
            rows=task.ra_detail_rows
        ) if task.ra_detail_file else None,
        ra_row=FileInfo(
            filename=os.path.basename(task.ra_row_file) if task.ra_row_file else "",
            status=task.ra_row_status or "pending",
            rows=task.ra_row_rows
        ) if task.ra_row_file else None,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    ))


def process_upload(task_id: str, files: dict):
    """
    后台线程处理上传文件
    """
    import traceback
    
    logger.info(f"[ETL] ========== 后台线程启动: {task_id} ==========")
    logger.info(f"[ETL] 文件列表: {list(files.keys())}")
    
    db = SessionLocal()
    try:
        # 验证文件是否存在
        for file_type, file_path in files.items():
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            logger.info(f"[ETL] 文件验证通过: {file_type} -> {file_path}")
        
        service = EtlService(db)
        service.process_upload_task(task_id, files)
        logger.info(f"[ETL] ========== 任务完成: {task_id} ==========")
    except Exception as e:
        logger.error(f"[ETL] ========== 任务失败: {task_id} ==========")
        logger.error(f"[ETL] 错误: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 确保数据库状态被更新为失败
        try:
            task = db.query(UploadTask).filter(UploadTask.task_id == task_id).first()
            if task and task.status != "failed":
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now()
                db.commit()
                logger.info(f"[ETL] 已更新任务状态为 failed")
        except Exception as db_err:
            logger.error(f"[ETL] 更新失败状态时出错: {str(db_err)}")
    finally:
        db.close()