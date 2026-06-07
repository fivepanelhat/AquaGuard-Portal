"""
portal_core/av_capture.py - Audio/Video Capture Module for AquaGuard Portal.

Handles OpenCV camera frames and PyAudio recordings. Includes mock fallbacks for testing.
"""

import logging
from typing import Optional, Any
from datetime import datetime

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None  # type: ignore

try:
    import pyaudio  # type: ignore
except ImportError:
    pyaudio = None  # type: ignore

logger = logging.getLogger(__name__)


class AVCapture:
    """
    Interface for aquatic cameras and microphones/hydrophones.
    Allows capturing frames and audio chunks with software simulation fallbacks.
    """

    def __init__(
        self,
        camera_index: int = 0,
        video_fps: int = 30,
        audio_sample_rate: int = 16000,
        audio_chunk_size: int = 4096,
    ):
        self.camera_index = camera_index
        self.video_fps = video_fps
        self.audio_sample_rate = audio_sample_rate
        self.audio_chunk_size = audio_chunk_size

        self.video_capture: Optional[Any] = None
        self.audio_stream: Optional[Any] = None

        self.use_mock_video = False
        self.use_mock_audio = False

        logger.info(
            f"AV Capture configured: camera={camera_index}, fps={video_fps}, audio_sr={audio_sample_rate}"
        )

    async def start_video_stream(self) -> bool:
        if cv2 is None:
            logger.warning("OpenCV not installed; enabling video simulation mode.")
            self.use_mock_video = True
            return True

        try:
            self.video_capture = cv2.VideoCapture(self.camera_index)
            if not self.video_capture.isOpened():
                logger.warning(f"Could not open camera device at index {self.camera_index}. Enabling video simulation.")
                self.use_mock_video = True
                self.video_capture = None
                return True

            self.video_capture.set(cv2.CAP_PROP_FPS, self.video_fps)
            logger.info("✓ Camera stream connected successfully.")
            return True
        except Exception as e:
            logger.error(f"Error starting video stream: {e}. Enabling simulation.")
            self.use_mock_video = True
            return True

    async def start_audio_stream(self) -> bool:
        if pyaudio is None:
            logger.warning("PyAudio not installed; enabling audio simulation mode.")
            self.use_mock_audio = True
            return True

        try:
            pa = pyaudio.PyAudio()
            self.audio_stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.audio_sample_rate,
                input=True,
                frames_per_buffer=self.audio_chunk_size,
            )
            logger.info("✓ Microphone stream connected successfully.")
            return True
        except Exception as e:
            logger.error(f"Error starting audio stream: {e}. Enabling simulation.")
            self.use_mock_audio = True
            return True

    async def capture_frame(self) -> Optional[bytes]:
        """
        Capture a single video frame. If simulation mode is active, returns simulated JPEG bytes.
        """
        if self.use_mock_video:
            # Generate simulated dummy JPEG bytes
            logger.debug("Simulating video frame capture.")
            return b"MOCK_AQUATIC_JPEG_FRAME_DATA"

        if self.video_capture is None or not self.video_capture.isOpened():
            logger.warning("Video stream not online.")
            return None

        try:
            ret, frame = self.video_capture.read()
            if ret:
                _, jpeg = cv2.imencode(".jpg", frame)
                logger.debug(f"Frame captured: {jpeg.nbytes} bytes")
                return jpeg.tobytes()
            else:
                logger.warning("Failed reading frame from camera interface.")
                return None
        except Exception as e:
            logger.error(f"Error capturing camera frame: {e}")
            return None

    async def capture_audio_chunk(self) -> Optional[bytes]:
        """
        Capture a single audio chunk. If simulation mode is active, returns simulated audio bytes.
        """
        if self.use_mock_audio:
            logger.debug("Simulating audio chunk capture.")
            return b"MOCK_HYDROPHONE_AUDIO_DATA"

        if self.audio_stream is None:
            logger.warning("Audio stream not online.")
            return None

        try:
            # read from port
            data = self.audio_stream.read(self.audio_chunk_size, exception_on_overflow=False)
            logger.debug(f"Audio chunk read: {len(data)} bytes")
            return data
        except Exception as e:
            logger.error(f"Error capturing audio stream: {e}")
            return None

    async def stop(self):
        """Releases resource allocations."""
        if self.video_capture:
            try:
                self.video_capture.release()
                logger.info("Video capture released.")
            except Exception as e:
                logger.error(f"Error releasing video capture: {e}")
            self.video_capture = None

        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                logger.info("Audio stream closed.")
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
            self.audio_stream = None

    async def health_check(self) -> bool:
        """
        Returns True if capture streams are working or if simulation mode is active.
        """
        video_ok = self.use_mock_video or (self.video_capture is not None and self.video_capture.isOpened())
        audio_ok = self.use_mock_audio or (self.audio_stream is not None and self.audio_stream.is_active())
        logger.info(f"AV Health: video={video_ok}, audio={audio_ok}")
        return video_ok or audio_ok
