"""
/upload-logs endpoint.

Accepts one or more JSON log files, each tagged with a source_type.
Creates a new AuditRun, stores each file as a RawLog, normalizes its
contents into NormalizedEvent rows, and returns a summary.
"""

import json
import os
import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.models import AuditRun, RawLog, NormalizedEvent, SourceType
from app.services.normalizer import normalize_entries
from app.schemas.schemas import UploadResponse

router = APIRouter()
settings = get_settings()


@router.post("/upload-logs", response_model=UploadResponse)
async def upload_logs(
    files: list[UploadFile] = File(...),
    source_types: list[str] = Form(...),
    company_name: str = Form("Demo SaaS Co"),
    db: Session = Depends(get_db),
):
    """
    files: one or more JSON files, each containing a list of log entries
    source_types: parallel list to `files` — one of iam_log, cloudtrail_log,
                  cloud_config, github_activity, matching each file by position
    """
    if len(files) != len(source_types):
        raise HTTPException(
            status_code=400,
            detail="files and source_types must be the same length",
        )

    valid_sources = {s.value for s in SourceType}
    for s in source_types:
        if s not in valid_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source_type '{s}'. Must be one of {valid_sources}",
            )

    audit_run = AuditRun(company_name=company_name, status="ingested")
    db.add(audit_run)
    db.flush()  # get audit_run.id without full commit yet

    os.makedirs(settings.upload_dir, exist_ok=True)

    total_events = 0
    seen_sources: set[str] = set()

    for upload, source_type_str in zip(files, source_types):
        source_type = SourceType(source_type_str)
        seen_sources.add(source_type_str)

        raw_bytes = await upload.read()
        try:
            entries = json.loads(raw_bytes)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail=f"File '{upload.filename}' is not valid JSON.",
            )

        if isinstance(entries, dict):
            entries = [entries]
        if not isinstance(entries, list):
            raise HTTPException(
                status_code=400,
                detail=f"File '{upload.filename}' must contain a JSON list of entries.",
            )

        # Persist the raw file to disk for audit-trail purposes
        stored_filename = f"{uuid.uuid4()}_{upload.filename}"
        storage_path = os.path.join(settings.upload_dir, stored_filename)
        with open(storage_path, "wb") as f:
            f.write(raw_bytes)

        raw_log = RawLog(
            audit_run_id=audit_run.id,
            source_type=source_type,
            original_filename=upload.filename,
            storage_path=storage_path,
        )
        db.add(raw_log)
        db.flush()

        normalized = normalize_entries(source_type, entries)
        for ev in normalized:
            db.add(NormalizedEvent(raw_log_id=raw_log.id, **ev))
        total_events += len(normalized)

    db.commit()

    return UploadResponse(
        audit_run_id=audit_run.id,
        files_received=len(files),
        events_normalized=total_events,
        source_types=sorted(seen_sources),
    )