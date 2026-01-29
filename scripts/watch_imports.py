"""Watch folder for automatic JSON imports.

Monitors a directory for new JSON files and automatically imports them
into the Sportsbeams pipeline.

Usage:
    python scripts/watch_imports.py [--watch-dir PATH] [--poll-interval SECONDS]

Default watch directory: ./imports (created if doesn't exist)
Processed files are moved to ./imports/processed/
Failed files are moved to ./imports/failed/
"""
import os
import sys
import json
import time
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal, init_db
from api.import_service import import_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ImportHandler(FileSystemEventHandler):
    """Handle new JSON files in the watch directory."""

    def __init__(self, watch_dir: Path):
        self.watch_dir = watch_dir
        self.processed_dir = watch_dir / "processed"
        self.failed_dir = watch_dir / "failed"

        # Create subdirectories
        self.processed_dir.mkdir(exist_ok=True)
        self.failed_dir.mkdir(exist_ok=True)

        # Track files being written (to avoid importing incomplete files)
        self.pending_files: dict[str, float] = {}
        self.write_settle_time = 2.0  # seconds to wait after last modification

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        if not event.src_path.endswith('.json'):
            return

        # Mark file as pending
        self.pending_files[event.src_path] = time.time()
        logger.info(f"Detected new file: {os.path.basename(event.src_path)}")

    def on_modified(self, event):
        """Handle file modification events (file still being written)."""
        if event.is_directory:
            return

        if event.src_path in self.pending_files:
            self.pending_files[event.src_path] = time.time()

    def process_pending_files(self):
        """Process files that have settled (no recent modifications)."""
        now = time.time()
        to_process = []

        for filepath, last_modified in list(self.pending_files.items()):
            if now - last_modified >= self.write_settle_time:
                to_process.append(filepath)
                del self.pending_files[filepath]

        for filepath in to_process:
            self.import_file(filepath)

    def import_file(self, filepath: str):
        """Import a single JSON file."""
        filename = os.path.basename(filepath)
        logger.info(f"Importing: {filename}")

        try:
            # Read JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Create database session
            db = SessionLocal()

            try:
                # Import the data
                result = import_json_file(db, json_data)

                if result.success:
                    logger.info(
                        f"✓ Imported {filename}: "
                        f"{result.prospects_created} prospects created, "
                        f"{result.prospects_updated} updated, "
                        f"{result.contacts_created} contacts created"
                    )

                    # Move to processed directory
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest_name = f"{timestamp}_{filename}"
                    dest_path = self.processed_dir / dest_name
                    shutil.move(filepath, dest_path)
                    logger.info(f"  Moved to: processed/{dest_name}")

                    # Log any warnings
                    for warning in result.warnings:
                        logger.warning(f"  Warning: {warning}")
                else:
                    raise Exception("; ".join(result.errors))

            finally:
                db.close()

        except json.JSONDecodeError as e:
            logger.error(f"✗ Invalid JSON in {filename}: {e}")
            self._move_to_failed(filepath, filename, f"Invalid JSON: {e}")

        except Exception as e:
            logger.error(f"✗ Failed to import {filename}: {e}")
            self._move_to_failed(filepath, filename, str(e))

    def _move_to_failed(self, filepath: str, filename: str, error: str):
        """Move a failed file to the failed directory with error log."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_name = f"{timestamp}_{filename}"
        dest_path = self.failed_dir / dest_name

        try:
            shutil.move(filepath, dest_path)

            # Write error log
            error_log_path = self.failed_dir / f"{timestamp}_{filename}.error.txt"
            with open(error_log_path, 'w') as f:
                f.write(f"File: {filename}\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write(f"Error: {error}\n")

            logger.info(f"  Moved to: failed/{dest_name}")
        except Exception as e:
            logger.error(f"  Failed to move file: {e}")

    def process_existing_files(self):
        """Process any JSON files already in the watch directory."""
        for filepath in self.watch_dir.glob("*.json"):
            if filepath.is_file():
                logger.info(f"Found existing file: {filepath.name}")
                self.import_file(str(filepath))


def main():
    parser = argparse.ArgumentParser(
        description="Watch folder for automatic JSON imports"
    )
    parser.add_argument(
        "--watch-dir",
        type=str,
        default="./imports",
        help="Directory to watch for JSON files (default: ./imports)"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--use-polling",
        action="store_true",
        help="Use polling observer instead of native filesystem events"
    )
    parser.add_argument(
        "--process-existing",
        action="store_true",
        help="Process existing JSON files on startup"
    )

    args = parser.parse_args()

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    # Set up watch directory
    watch_dir = Path(args.watch_dir).resolve()
    watch_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Watch directory: {watch_dir}")
    logger.info(f"Processed files: {watch_dir}/processed/")
    logger.info(f"Failed files: {watch_dir}/failed/")

    # Create event handler
    handler = ImportHandler(watch_dir)

    # Process existing files if requested
    if args.process_existing:
        logger.info("Processing existing files...")
        handler.process_existing_files()

    # Set up observer
    if args.use_polling:
        logger.info("Using polling observer")
        observer = PollingObserver(timeout=args.poll_interval)
    else:
        logger.info("Using native filesystem observer")
        observer = Observer()

    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()

    logger.info("")
    logger.info("=" * 60)
    logger.info("Watch folder is running!")
    logger.info(f"Drop JSON files into: {watch_dir}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    logger.info("")

    try:
        while True:
            # Process any pending files
            handler.process_pending_files()
            time.sleep(args.poll_interval)
    except KeyboardInterrupt:
        logger.info("\nStopping watch folder...")
        observer.stop()

    observer.join()
    logger.info("Watch folder stopped.")


if __name__ == "__main__":
    main()
