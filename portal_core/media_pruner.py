"""
portal_core/media_pruner.py - Media Pruner Module for AquaGuard Portal.

Manages disk capacity by pruning expired video frames and audio buffers while preserving compliance outputs.
"""

import asyncio
import logging
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)


class MediaPruner:
    """
    Background worker that runs indefinitely, executing cycles to:
    - Prune transient JPEG/WAV files in media directories older than `retention_hours`.
    - Compress historical sensor telemetry JSON files older than 7 days.
    - Audit disk utilization, logging critical warnings if the threshold is breached.
    - NOTE: structured compliance records inside `compliance_dir` are NEVER deleted or altered.
    """

    def __init__(
        self,
        media_dir: str = "./telemetry_data/media",
        sensor_logs_dir: str = "./telemetry_data/sensor_logs",
        compliance_dir: str = "./telemetry_data/compliance",
        retention_hours: int = 48,
        critical_disk_usage_pct: float = 85.0,
    ):
        self.media_dir = Path(media_dir)
        self.sensor_logs_dir = Path(sensor_logs_dir)
        self.compliance_dir = Path(compliance_dir)
        self.retention_hours = retention_hours
        self.critical_disk_usage_pct = critical_disk_usage_pct
        self.is_running = False

        logger.info(
            f"MediaPruner configured: media={media_dir}, retention={retention_hours} hrs, "
            f"critical_disk_usage={critical_disk_usage_pct}%"
        )

    async def start(self):
        self.is_running = True
        logger.info("MediaPruner loop started.")
        try:
            while self.is_running:
                await self.prune_old_media()
                await self.compress_old_logs()
                await self.check_disk_usage()
                # Run once an hour
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("MediaPruner loop terminated.")
            self.is_running = False

    async def stop(self):
        self.is_running = False
        logger.info("MediaPruner stopping...")

    async def prune_old_media(self) -> int:
        if not self.media_dir.exists():
            return 0

        deleted_count = 0
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)

        try:
            for file_path in self.media_dir.glob("*"):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"Pruned media buffer: {file_path.name}")
                        except Exception as e:
                            logger.error(f"Failed deleting media file {file_path.name}: {e}")

            if deleted_count > 0:
                logger.info(f"MediaPruner: pruned {deleted_count} expired files from media directory.")
        except Exception as e:
            logger.error(f"Error executing media pruning: {e}")

        return deleted_count

    async def compress_old_logs(self) -> int:
        if not self.sensor_logs_dir.exists():
            return 0

        compressed_count = 0
        cutoff = datetime.now() - timedelta(days=7)

        try:
            for file_path in self.sensor_logs_dir.glob("*.json"):
                if file_path.is_file() and not file_path.name.endswith(".gz"):
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        try:
                            gz_path = file_path.with_suffix(".json.gz")
                            with open(file_path, "rb") as f_in:
                                with gzip.open(gz_path, "wb") as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            file_path.unlink()
                            compressed_count += 1
                            logger.debug(f"Compressed log entry: {file_path.name}")
                        except Exception as e:
                            logger.error(f"Failed compressing log file {file_path.name}: {e}")

            if compressed_count > 0:
                logger.info(f"MediaPruner: compressed {compressed_count} historical log files.")
        except Exception as e:
            logger.error(f"Error executing log compression: {e}")

        return compressed_count

    async def check_disk_usage(self) -> float:
        try:
            total, used, free = shutil.disk_usage(self.media_dir)
            usage_pct = (used / total) * 100

            if usage_pct > self.critical_disk_usage_pct:
                logger.critical(
                    f"CRITICAL STORAGE THRESHOLD BREACHED: {usage_pct:.1f}% "
                    f"(target capacity max: {self.critical_disk_usage_pct}%)"
                )
            return usage_pct
        except Exception as e:
            logger.error(f"Error executing disk capacity audit: {e}")
            return 0.0

    def get_storage_stats(self) -> dict:
        stats = {
            "media_count": 0,
            "logs_count": 0,
            "compliance_count": 0,
            "total_size_mb": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        try:
            total_bytes = 0
            if self.media_dir.exists():
                m_files = [f for f in self.media_dir.glob("*") if f.is_file()]
                stats["media_count"] = len(m_files)
                total_bytes += sum(f.stat().st_size for f in m_files)

            if self.sensor_logs_dir.exists():
                l_files = [f for f in self.sensor_logs_dir.glob("*.json*") if f.is_file()]
                stats["logs_count"] = len(l_files)
                total_bytes += sum(f.stat().st_size for f in l_files)

            if self.compliance_dir.exists():
                c_files = [f for f in self.compliance_dir.glob("*") if f.is_file()]
                stats["compliance_count"] = len(c_files)
                total_bytes += sum(f.stat().st_size for f in c_files)

            stats["total_size_mb"] = round(total_bytes / (1024 * 1024), 2)
        except Exception as e:
            logger.error(f"Error collecting storage usage statistics: {e}")
        return stats
