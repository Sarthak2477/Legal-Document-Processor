"""
Cleanup utility for temporary files.
"""
import os
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def cleanup_old_files(directory: str = "uploads", max_age_hours: int = 24):
    """Remove files older than max_age_hours."""
    try:
        upload_dir = Path(directory)
        if not upload_dir.exists():
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in upload_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old file: {file_path}")
                    
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

if __name__ == "__main__":
    cleanup_old_files()