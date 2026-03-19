import subprocess
import threading
import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.logger import setup_logger

logger = setup_logger(prefix="FFmpeg推流")


class FFmpegPushStreamer:
    """FFmpeg 推流检测模块
    使用 FFmpeg 替代 GStreamer，更容易部署

    优势：
    - 不需要 OpenCV 的 GStreamer 支持
    - FFmpeg 安装简单：apt-get install ffmpeg
    - 跨平台支持更好
    """

    def __init__(
        self,
        model_path: str = "runs/train/person_detection/weights/best.pt",
        host: str = "115.120.237.79",
        port: int = 5004,
        video_width: int = 640,
        video_height: int = 480,
        fps: int = 15,
        bitrate: int = 400,  # kbps
        camera_device: int = 0,  # 摄像头设备ID
        headless: bool = True,
    ):
        """
        初始化 FFmpeg 推流器

        Args:
            model_path: YOLO模型路径
            host: 推流目标主机地址
            port: 推流目标端口
            video_width: 视频宽度
            video_height: 视频高度
            fps: 帧率
            bitrate: 比特率(kbps)
            camera_device: 摄像头设备ID或路径（Linux: /dev/video4）
            headless: 无头模式
        """
        self.model_path = model_path
        self.host = host
        self.port = port
        self.video_width = video_width
        self.video_height = video_height
        self.fps = fps
        self.bitrate = bitrate
        self.camera_device = camera_device
        self.headless = headless

        self.model: Optional[YOLO] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.ffmpeg_monitor_thread: Optional[threading.Thread] = None

        logger.info(
            f"📹 推流配置: {host}:{port} | {video_width}x{video_height}@{fps}fps | {bitrate}kbps")

    def _load_model(self) -> bool:
        """加载 YOLO 模型"""
        model_file = Path(self.model_path)
        if not model_file.exists():
            logger.error(f"模型文件不存在: {self.model_path}")
            return False

        try:
            logger.info(f"正在加载模型: {self.model_path}")
            self.model = YOLO(self.model_path)

            # 强制使用 CPU，避免 CUDA 错误
            self.model.to('cpu')

            logger.success(f"模型加载成功! (使用 CPU)")
            logger.info(f"模型类别: {self.model.names}")
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            return False

    def _init_camera(self) -> bool:
        """初始化摄像头"""
        try:
            # 支持设备ID或设备路径
            if isinstance(self.camera_device, str):
                logger.info(f"打开摄像头设备: {self.camera_device}")
                self.cap = cv2.VideoCapture(self.camera_device)
            else:
                logger.info(f"打开摄像头ID: {self.camera_device}")
                self.cap = cv2.VideoCapture(self.camera_device)

            if not self.cap.isOpened():
                logger.error(f"无法打开摄像头")
                return False

            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # 读取一帧测试
            ret, frame = self.cap.read()
            if not ret:
                logger.error("无法从摄像头读取帧")
                return False

            actual_width = frame.shape[1]
            actual_height = frame.shape[0]
            logger.success(f"摄像头初始化成功: {actual_width}x{actual_height}")

            return True
        except Exception as e:
            logger.error(f"摄像头初始化失败: {str(e)}")
            return False

    def _init_ffmpeg(self) -> bool:
        """初始化 FFmpeg 推流进程

        FFmpeg 命令等效于您的 GStreamer 命令：
        x264enc tune=zerolatency bitrate=400 speed-preset=ultrafast 
        key-int-max=15 ref=1 bframes=0 threads=2
        """
        try:
            # 构建 FFmpeg 命令
            # 对应 GStreamer 的参数设置
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'rawvideo',           # 输入格式：原始视频
                '-pix_fmt', 'bgr24',        # OpenCV 使用 BGR24
                '-s', f'{self.video_width}x{self.video_height}',  # 视频尺寸
                '-r', str(self.fps),        # 帧率
                '-i', '-',                  # 从 stdin 读取

                # H.264 编码参数（对应 GStreamer 的 x264enc 参数）
                '-c:v', 'libx264',
                '-preset', 'ultrafast',     # speed-preset=ultrafast
                '-tune', 'zerolatency',     # tune=zerolatency
                '-profile:v', 'baseline',   # profile=baseline
                '-pix_fmt', 'yuv420p',      # 强制使用 YUV420P（baseline 兼容）
                '-b:v', f'{self.bitrate}k',  # bitrate
                '-maxrate', f'{self.bitrate}k',
                '-bufsize', f'{self.bitrate * 2}k',
                '-g', '15',                 # key-int-max=15 (GOP size)
                '-refs', '1',               # ref=1
                '-bf', '0',                 # bframes=0
                '-threads', '2',            # threads=2

                # RTP 输出参数（对应 rtph264pay）
                '-f', 'rtp',
                '-payload_type', '96',      # pt=96
                '-pkt_size', '1200',        # mtu=1200
                f'rtp://{self.host}:{self.port}'
            ]

            logger.info("启动 FFmpeg 推流进程...")
            logger.debug(f"FFmpeg 命令: {' '.join(ffmpeg_cmd)}")

            # 启动 FFmpeg 进程
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )

            # 等待一小段时间，检查 FFmpeg 是否正常启动
            import time
            time.sleep(0.5)

            if self.ffmpeg_process.poll() is not None:
                # FFmpeg 进程已经退出，读取错误信息
                stderr_output = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                logger.error(f"FFmpeg 启动失败，返回码: {self.ffmpeg_process.returncode}")
                logger.error(f"FFmpeg 错误输出:\n{stderr_output}")
                return False

            logger.success(f"FFmpeg 推流初始化成功: rtp://{self.host}:{self.port}")

            # 启动 FFmpeg 错误监控线程
            self.ffmpeg_monitor_thread = threading.Thread(
                target=self._monitor_ffmpeg_output,
                daemon=True
            )
            self.ffmpeg_monitor_thread.start()

            return True

        except FileNotFoundError:
            logger.error("FFmpeg 未安装！请运行: sudo apt-get install ffmpeg")
            return False
        except Exception as e:
            logger.error(f"FFmpeg 初始化失败: {str(e)}")
            return False

    def _monitor_ffmpeg_output(self):
        """监控 FFmpeg 的错误输出"""
        if not self.ffmpeg_process or not self.ffmpeg_process.stderr:
            return

        try:
            for line in iter(self.ffmpeg_process.stderr.readline, b''):
                if line:
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    # 只记录重要的错误信息
                    if 'error' in line_str.lower() or 'warning' in line_str.lower():
                        logger.debug(f"FFmpeg: {line_str}")
        except Exception as e:
            logger.debug(f"FFmpeg 监控线程异常: {e}")

    def _draw_detections(self, frame: np.ndarray, boxes) -> np.ndarray:
        """在帧上绘制检测结果"""
        if boxes is None or len(boxes) == 0:
            return frame

        for box in boxes:
            # 获取边界框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]

            # 绘制边界框
            color = (0, 255, 0)  # 绿色
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # 绘制标签
            label = f"{class_name} {confidence:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1

            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, thickness
            )

            # 标签背景
            cv2.rectangle(
                frame,
                (x1, y1 - text_height - baseline - 5),
                (x1 + text_width, y1),
                color,
                -1
            )

            # 标签文字
            cv2.putText(
                frame,
                label,
                (x1, y1 - baseline - 5),
                font,
                font_scale,
                (0, 0, 0),
                thickness
            )

        return frame

    def start_streaming(self):
        """开始推流"""
        logger.info("=" * 50)
        logger.info("🚀 启动 YOLO FFmpeg 推流系统")
        logger.info("=" * 50)

        # 1. 加载模型
        if not self._load_model():
            return

        # 2. 初始化摄像头
        if not self._init_camera():
            return

        # 3. 初始化 FFmpeg
        if not self._init_ffmpeg():
            return

        logger.info("=" * 50)
        logger.info(f"📡 开始推流到 {self.host}:{self.port}")
        logger.info("=" * 50)
        logger.info("按 Ctrl+C 停止推流")
        logger.info("")

        frame_count = 0
        try:
            while True:
                # 读取帧
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("无法读取摄像头帧")
                    break

                # YOLO 检测（使用 CPU）
                results = self.model.predict(
                    frame,
                    conf=0.5,
                    device='cpu',  # 强制使用 CPU
                    verbose=False
                )

                # 绘制检测结果
                if results and len(results) > 0:
                    boxes = results[0].boxes
                    frame = self._draw_detections(frame, boxes)

                    # 显示检测统计
                    if len(boxes) > 0:
                        detected_classes = {}
                        for box in boxes:
                            class_name = self.model.names[int(box.cls[0])]
                            detected_classes[class_name] = detected_classes.get(
                                class_name, 0) + 1

                        if frame_count % 30 == 0:  # 每30帧显示一次
                            detection_str = ", ".join(
                                [f"{k}:{v}" for k, v in detected_classes.items()])
                            logger.info(f"检测到: {detection_str}")

                # 确保帧尺寸正确
                if frame.shape[1] != self.video_width or frame.shape[0] != self.video_height:
                    frame = cv2.resize(
                        frame, (self.video_width, self.video_height))

                # 推流到 FFmpeg
                try:
                    # 检查 FFmpeg 进程是否还在运行
                    if self.ffmpeg_process.poll() is not None:
                        logger.error(f"FFmpeg 进程已退出，返回码: {self.ffmpeg_process.returncode}")
                        # 读取错误输出
                        stderr_output = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                        if stderr_output:
                            logger.error(f"FFmpeg 错误输出:\n{stderr_output[-1000:]}")  # 显示最后1000字符
                        break

                    self.ffmpeg_process.stdin.write(frame.tobytes())
                    self.ffmpeg_process.stdin.flush()  # 确保数据被发送
                except BrokenPipeError:
                    logger.error("FFmpeg 管道已断开")
                    break
                except Exception as e:
                    logger.error(f"写入 FFmpeg 失败: {e}")
                    break

                # 本地预览（可选）
                if not self.headless:
                    cv2.imshow('YOLO Detection Stream', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                frame_count += 1

        except KeyboardInterrupt:
            logger.info("\n⏹  用户停止推流")
        except Exception as e:
            logger.error(f"推流过程中发生错误: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        logger.info("正在清理资源...")

        # 释放摄像头
        if self.cap:
            try:
                self.cap.release()
                logger.debug("摄像头已释放")
            except Exception as e:
                logger.warning(f"释放摄像头时出错: {e}")

        # 关闭 FFmpeg 进程
        if self.ffmpeg_process:
            try:
                # 先尝试正常关闭 stdin
                if self.ffmpeg_process.stdin and not self.ffmpeg_process.stdin.closed:
                    try:
                        self.ffmpeg_process.stdin.close()
                    except BrokenPipeError:
                        pass  # FFmpeg 已经关闭了管道，忽略这个错误

                # 等待进程结束（最多等待5秒）
                try:
                    self.ffmpeg_process.wait(timeout=5)
                    logger.debug("FFmpeg 进程已正常结束")
                except subprocess.TimeoutExpired:
                    logger.warning("FFmpeg 进程未响应，强制终止")
                    self.ffmpeg_process.kill()
                    self.ffmpeg_process.wait()

                # 读取并记录 FFmpeg 的错误输出
                if self.ffmpeg_process.stderr:
                    stderr_output = self.ffmpeg_process.stderr.read()
                    if stderr_output:
                        logger.debug(f"FFmpeg stderr: {stderr_output[:500]}")  # 只显示前500字符

            except Exception as e:
                logger.warning(f"关闭 FFmpeg 进程时出错: {e}")

        # 关闭所有 OpenCV 窗口
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            logger.warning(f"关闭窗口时出错: {e}")

        logger.success("资源清理完成")


# 保持向后兼容
PushStreamer = FFmpegPushStreamer
