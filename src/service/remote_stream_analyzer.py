import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.logger import setup_logger

logger = setup_logger(prefix="远端分析")


def calculate_frame_size(video_width: int, video_height: int) -> int:
    """BGR24 一帧的字节数。"""
    return video_width * video_height * 3


def build_rtp_sdp(listen_port: int, listen_host: str = "0.0.0.0") -> str:
    """构造 RTP H264 接收端 SDP。"""
    return "\n".join(
        [
            "v=0",
            "o=- 0 0 IN IP4 127.0.0.1",
            "s=YOLO RTP Input",
            f"c=IN IP4 {listen_host}",
            "t=0 0",
            f"m=video {listen_port} RTP/AVP 96",
            "a=rtpmap:96 H264/90000",
            "",
        ]
    )


class RemoteStreamAnalyzer:
    """接收边缘端 RTP 视频流并在本机执行推理分析。"""

    def __init__(
        self,
        model_path: str,
        listen_host: str = "0.0.0.0",
        listen_port: int = 5004,
        video_width: int = 640,
        video_height: int = 480,
        confidence: float = 0.5,
        device: str = "cpu",
    ):
        self.model_path = model_path
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.video_width = video_width
        self.video_height = video_height
        self.confidence = confidence
        self.device = device

        self.model = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.ffmpeg_monitor_thread: Optional[threading.Thread] = None
        self.sdp_path: Optional[Path] = None

    def _load_model(self) -> bool:
        model_file = Path(self.model_path)
        if not model_file.exists():
            logger.error(f"模型文件不存在: {self.model_path}")
            return False

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            logger.error(f"无法导入 ultralytics: {exc}")
            return False

        logger.info(f"正在加载模型: {self.model_path}")
        self.model = YOLO(self.model_path)
        self.model.to(self.device)
        logger.success(f"模型加载成功! (使用 {self.device})")
        logger.info(f"模型类别: {self.model.names}")
        return True

    def _write_sdp_file(self) -> Path:
        sdp_content = build_rtp_sdp(self.listen_port, self.listen_host)
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sdp",
            prefix="yolo-stream-",
            delete=False,
        ) as handle:
            handle.write(sdp_content)
            self.sdp_path = Path(handle.name)
        return self.sdp_path

    def _start_receiver(self) -> bool:
        sdp_path = self._write_sdp_file()
        ffmpeg_cmd = [
            "ffmpeg",
            "-protocol_whitelist", "file,udp,rtp",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-analyzeduration", "0",
            "-probesize", "32",
            "-i", str(sdp_path),
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-vf", f"scale={self.video_width}:{self.video_height}",
            "pipe:1",
        ]

        logger.info(f"开始监听 RTP 视频流: {self.listen_host}:{self.listen_port}")
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**8,
        )

        self.ffmpeg_monitor_thread = threading.Thread(
            target=self._monitor_ffmpeg_output,
            daemon=True,
        )
        self.ffmpeg_monitor_thread.start()
        return True

    def _monitor_ffmpeg_output(self):
        if not self.ffmpeg_process or not self.ffmpeg_process.stderr:
            return

        try:
            for line in iter(self.ffmpeg_process.stderr.readline, b""):
                if line:
                    line_str = line.decode("utf-8", errors="ignore").strip()
                    if "error" in line_str.lower() or "warning" in line_str.lower():
                        logger.debug(f"FFmpeg: {line_str}")
        except Exception as exc:
            logger.debug(f"FFmpeg 监控线程异常: {exc}")

    def start(self):
        if not self._load_model():
            return

        if not self._start_receiver():
            return

        frame_size = calculate_frame_size(self.video_width, self.video_height)
        frame_count = 0

        try:
            while True:
                if not self.ffmpeg_process or not self.ffmpeg_process.stdout:
                    logger.error("FFmpeg 接收进程未就绪")
                    break

                raw_frame = self.ffmpeg_process.stdout.read(frame_size)
                if len(raw_frame) != frame_size:
                    logger.warning("接收到的帧长度不足，停止分析")
                    break

                frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape(
                    (self.video_height, self.video_width, 3)
                )

                results = self.model.predict(
                    frame,
                    conf=self.confidence,
                    device=self.device,
                    verbose=False,
                )

                if results and len(results) > 0 and frame_count % 30 == 0:
                    boxes = results[0].boxes
                    if len(boxes) > 0:
                        detected_classes = {}
                        for box in boxes:
                            class_name = self.model.names[int(box.cls[0])]
                            detected_classes[class_name] = detected_classes.get(class_name, 0) + 1

                        detection_str = ", ".join(
                            [f"{class_name}:{count}" for class_name, count in detected_classes.items()]
                        )
                        logger.info(f"检测到: {detection_str}")

                frame_count += 1
        finally:
            self.stop()

    def stop(self):
        if self.ffmpeg_process:
            if self.ffmpeg_process.poll() is None:
                self.ffmpeg_process.terminate()
                try:
                    self.ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.ffmpeg_process.kill()
                    self.ffmpeg_process.wait()

        if self.sdp_path and self.sdp_path.exists():
            self.sdp_path.unlink(missing_ok=True)
