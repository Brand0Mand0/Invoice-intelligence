import os
import hashlib
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.job import ProcessingJob
from app.core.config import get_settings
from app.utils.file_validator import validate_upload_file, create_safe_filepath
from app.core.logging_config import get_logger

settings = get_settings()
router = APIRouter()
logger = get_logger(__name__)


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def process_pdf_pipeline(file_path: str, job_id: str):
    """
    Background task to process PDF through extraction pipeline.
    Creates its own database session.
    """
    # Import here to avoid circular imports
    from app.services.parser import PDFParser
    from app.core.database import SessionLocal
    import asyncio

    # Create new database session for this background task
    db = SessionLocal()

    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        # Initialize parser and process (run async function in sync context)
        parser = PDFParser(db)
        result = asyncio.run(parser.process(file_path))

        job.status = "complete"
        job.result = result
        db.commit()

    except Exception as e:
        job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
        if job:
            job.status = "error"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload PDF invoice and queue for processing.

    Security validations:
    - Filename sanitization (path traversal protection)
    - Extension whitelist (.pdf only)
    - Streaming file size validation (DoS protection)
    - Magic byte verification (actual PDF check)
    - PDF structure validation

    Returns job_id for status tracking.
    """
    logger.info(
        "File upload started",
        extra={"extra_data": {"filename": file.filename, "content_type": file.content_type}}
    )

    # SECURITY: Comprehensive file validation (prevents malware, path traversal, DoS)
    try:
        content, safe_filename = await validate_upload_file(
            file,
            max_size=settings.MAX_FILE_SIZE
        )
    except HTTPException as e:
        logger.warning(
            "File upload rejected",
            extra={
                "extra_data": {
                    "filename": file.filename,
                    "reason": e.detail,
                    "status_code": e.status_code
                }
            }
        )
        raise

    # Create job
    job = ProcessingJob(status="queued", pdf_path="")
    db.add(job)
    db.commit()
    db.refresh(job)

    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # SECURITY: Create safe file path (prevents directory traversal)
    try:
        file_path = create_safe_filepath(
            settings.UPLOAD_DIR,
            str(job.job_id),
            safe_filename
        )
    except Exception as e:
        db.delete(job)
        db.commit()
        logger.error(
            "File path creation failed",
            exc_info=True,
            extra={"extra_data": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail="Failed to create secure file path")

    # Save validated content to disk
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        db.delete(job)
        db.commit()
        logger.error(
            "File write failed",
            exc_info=True,
            extra={"extra_data": {"error": str(e), "file_path": file_path}}
        )
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Update job with file path
    job.pdf_path = file_path
    db.commit()

    logger.info(
        "File upload successful",
        extra={
            "extra_data": {
                "job_id": str(job.job_id),
                "filename": safe_filename,
                "size_bytes": len(content)
            }
        }
    )

    # Queue processing (don't pass db - background task creates its own session)
    background_tasks.add_task(process_pdf_pipeline, file_path, str(job.job_id))

    return {
        "job_id": str(job.job_id),
        "filename": safe_filename,
        "status": "queued"
    }


@router.get("/status/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get processing job status and result."""
    job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": str(job.job_id),
        "status": job.status,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }

    if job.status == "complete":
        response["result"] = job.result
    elif job.status == "error":
        response["error"] = job.error_message

    return response
