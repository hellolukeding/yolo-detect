from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

from utils.logger import setup_logger

logger = setup_logger(prefix="推流模块")


class PushStreamer:
    """推流检测模块
    使用训练好的YOLO模型进行网络摄像头实时检测
    推送到GStreamer流
    适用于训练完成后的模型推理

    基本流程：
    1. 使用 OpenCV 捕捉视频流。
    2. 将 YOLO 的检测结果叠加到视频帧上。
    3. 通过 GStreamer 推送视频流。
    """

    def __init__(
        self,
        model_path: str = "runs/train/person_detection/weights/best.pt",
        host: str = "115.120.237.79",
        port: int = 5004,
        video_width: int = 640,
        video_height: int = 480,
        fps: int = 30,
        bitrate: int = 500,
        headless: bool = False  # 无头模式，适用于无显示器的设备
    ):
        """
        初始化推流器

        Args:
            model_path: YOLO模型路径
            host: 推流目标主机地址
            port: 推流目标端口
            video_width: 视频宽度
            video_height: 视频高度
            fps: 帧率
            bitrate: 比特率(kbps)
            headless: 是否启用无头模式（无显示器环境）
        """
        self.model_path = model_path
        self.host = host
        self.port = port
        self.video_width = video_width
        self.video_height = video_height
        self.fps = fps
        self.bitrate = bitrate
        self.headless = headless  # 无头模式标志

        self.model: Optional[YOLO] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.out: Optional[cv2.VideoWriter] = None
        self.gst_pipeline: Optional[str] = None
        self.use_gstreamer: bool = True  # 是否使用GStreamer推流

        self._setup_gstreamer()

        if self.headless:
            logger.info("🤖 无头模式已启用 - 适用于无显示器环境")
            # 在无头模式下，禁用所有GUI相关功能
            import os
            os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'  # Windows
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Linux

    def _setup_gstreamer(self) -> None:
        """配置GStreamer推流参数，支持多种编码器"""
        # 定义多个备选管道（按优先级排序）
        self.gst_pipelines = [
            # 管道 1: x264enc (最好的质量，需要 gstreamer1.0-plugins-ugly)
            (
                f"appsrc ! videoconvert ! "
                f"video/x-raw,format=I420,width={self.video_width},height={self.video_height},framerate={self.fps}/1 ! "
                f"x264enc bitrate={self.bitrate} tune=zerolatency speed-preset=ultrafast ! "
                f"rtph264pay config-interval=1 pt=96 ! "
                f"udpsink host={self.host} port={self.port}",
                "x264enc"
            ),
            # 管道 2: openh264enc (开源 H264 编码器，质量较好)
            (
                f"appsrc ! videoconvert ! "
                f"openh264enc bitrate={self.bitrate * 1000} ! "
                f"rtph264pay config-interval=1 pt=96 ! "
                f"udpsink host={self.host} port={self.port}",
                "openh264enc"
            ),
            # 管道 3: avenc_h264 (FFmpeg H264 编码器)
            (
                f"appsrc ! videoconvert ! "
                f"avenc_h264 bitrate={self.bitrate * 1000} ! "
                f"rtph264pay config-interval=1 pt=96 ! "
                f"udpsink host={self.host} port={self.port}",
                "avenc_h264"
            ),
            # 管道 4: omxh264enc (硬件编码，适用于树莓派)
            (
                f"appsrc ! videoconvert ! "
                f"omxh264enc ! "
                f"rtph264pay config-interval=1 pt=96 ! "
                f"udpsink host={self.host} port={self.port}",
                "omxh264enc"
            ),
            # 管道 5: jpegenc (MJPEG，最兼容但质量较低)
            (
                f"appsrc ! videoconvert ! "
                f"jpegenc ! "
                f"rtpjpegpay ! "
                f"udpsink host={self.host} port={self.port}",
                "jpegenc"
            ),
        ]

        # 默认使用第一个管道
        self.gst_pipeline = self.gst_pipelines[0][0]
        logger.info(f"GStreamer管道配置完成: {self.host}:{self.port}")

    def _load_model(self, device: str = "mps") -> bool:
        """
        加载YOLO模型

        Args:
            device: 推理设备 ('mps', 'cuda', 'cpu')

        Returns:
            bool: 加载是否成功
        """
        model_file = Path(self.model_path)
        if not model_file.exists():
            logger.error(f"模型文件不存在: {self.model_path}")
            return False

        try:
            logger.info(f"正在加载模型: {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.success(f"模型加载成功! 设备: {device}")
            logger.info(f"模型类别: {self.model.names}")
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            return False

    def _init_camera(self, camera_id: int = 0) -> bool:
        """
        初始化摄像头

        Args:
            camera_id: 摄像头ID

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                logger.error(f"无法打开摄像头 {camera_id}")
                return False

            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            logger.success(f"摄像头初始化成功 (ID: {camera_id})")
            return True
        except Exception as e:
            logger.error(f"摄像头初始化失败: {str(e)}")
            return False

    def _init_video_writer(self) -> bool:
        """
        初始化视频写入器（用于GStreamer推流）

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 检查 OpenCV 是否支持 GStreamer
            opencv_build_info = cv2.getBuildInformation()
            has_gstreamer = 'GStreamer' in opencv_build_info

            if not has_gstreamer:
                logger.warning("OpenCV 未编译 GStreamer 支持")
                logger.info("将使用替代方案：直接显示检测结果")
                self.use_gstreamer = False
                return True  # 使用替代方案，返回成功

            # 尝试多种 GStreamer 管道和编码器
            logger.info("尝试初始化 GStreamer 推流...")

            # 遍历所有备选管道
            for idx, (pipeline, encoder_name) in enumerate(self.gst_pipelines, 1):
                logger.debug(
                    f"尝试编码器 {idx}/{len(self.gst_pipelines)}: {encoder_name}")

                # 方法 1: 使用 CAP_GSTREAMER 和 fourcc=0
                try:
                    self.out = cv2.VideoWriter(
                        pipeline,
                        cv2.CAP_GSTREAMER,
                        0,  # fourcc 设为 0，让 GStreamer 自动处理
                        float(self.fps),
                        (self.video_width, self.video_height),
                        True
                    )

                    if self.out.isOpened():
                        logger.success(
                            f"GStreamer 推流初始化成功！使用编码器: {encoder_name}")
                        self.gst_pipeline = pipeline  # 更新为工作的管道
                        return True
                except Exception as e:
                    logger.debug(f"编码器 {encoder_name} (方法1) 失败: {str(e)}")

                # 方法 2: 使用传统的 fourcc 方式
                try:
                    fourcc = cv2.VideoWriter_fourcc(*'H264')
                    self.out = cv2.VideoWriter(
                        pipeline,
                        fourcc,
                        float(self.fps),
                        (self.video_width, self.video_height),
                        True
                    )

                    if self.out.isOpened():
                        logger.success(
                            f"GStreamer 推流初始化成功！使用编码器: {encoder_name}")
                        self.gst_pipeline = pipeline  # 更新为工作的管道
                        return True
                except Exception as e:
                    logger.debug(f"编码器 {encoder_name} (方法2) 失败: {str(e)}")

            # 所有编码器都失败
            logger.warning("所有 GStreamer 编码器都初始化失败")
            logger.info("提示：")
            logger.info(
                "  1. 安装 x264 编码器: sudo apt-get install gstreamer1.0-plugins-ugly")
            logger.info(
                "  2. 运行诊断工具: poetry run python test/test_gstreamer_debug.py")
            logger.info("将使用替代方案：仅显示检测结果")
            self.use_gstreamer = False
            self.out = None
            return True  # 使用替代方案，返回成功

        except Exception as e:
            logger.warning(f"视频写入器初始化异常: {str(e)}")
            logger.info("将使用替代方案：仅显示检测结果")
            self.use_gstreamer = False
            self.out = None
            return True  # 使用替代方案，返回成功

    def _draw_detections(
        self,
        frame: np.ndarray,
        boxes,
        show_labels: bool = True
    ) -> np.ndarray:
        """
        在帧上绘制检测结果

        Args:
            frame: 输入帧
            boxes: YOLO检测结果boxes
            show_labels: 是否显示标签

        Returns:
            绘制后的帧
        """
        if boxes is None or len(boxes) == 0:
            return frame

        for box in boxes:
            # 获取边界框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # 获取置信度和类别
            conf = float(box.conf[0])
            cls = int(box.cls[0])

            # 获取跟踪ID（如果有）
            track_id = int(box.id[0]) if box.id is not None else None

            # 绘制边界框
            color = (0, 255, 0)  # 绿色
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # 绘制标签
            if show_labels:
                label = f"{self.model.names[cls]}"
                if track_id is not None:
                    label += f" ID:{track_id}"
                label += f" {conf:.2f}"

                # 计算标签背景大小
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )

                # 绘制标签背景
                cv2.rectangle(
                    frame,
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width, y1),
                    color,
                    -1
                )

                # 绘制标签文本
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - baseline - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1
                )

        return frame

    def _add_info_overlay(
        self,
        frame: np.ndarray,
        frame_count: int,
        detection_count: int,
        fps_value: float
    ) -> np.ndarray:
        """
        添加信息叠加层

        Args:
            frame: 输入帧
            frame_count: 帧计数
            detection_count: 检测数量
            fps_value: 实际FPS

        Returns:
            添加信息后的帧
        """
        # 添加半透明背景
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 100), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)

        # 添加文本信息
        info_texts = [
            f"Frame: {frame_count}",
            f"Detections: {detection_count}",
            f"FPS: {fps_value:.1f}",
        ]

        # 根据推流状态添加不同的信息
        if self.use_gstreamer:
            info_texts.append(f"Streaming to: {self.host}:{self.port}")
        else:
            info_texts.append("Status: Preview Only (No Streaming)")

        y_offset = 30
        for text in info_texts:
            cv2.putText(
                frame,
                text,
                (20, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            y_offset += 20

        return frame

    def _cleanup(self) -> None:
        """清理资源"""
        if self.cap is not None:
            self.cap.release()
            logger.info("摄像头已释放")

        if self.out is not None and self.use_gstreamer:
            self.out.release()
            logger.info("推流已停止")

        # 只在非无头模式下销毁窗口
        if not self.headless:
            cv2.destroyAllWindows()
            logger.info("所有窗口已关闭")

    def gstreamer_setup(self) -> None:
        """配置GStreamer推流参数（向后兼容的方法）"""
        self._setup_gstreamer()

    def start_streaming(
        self,
        camera_id: int = 0,
        conf: float = 0.25,
        iou: float = 0.45,
        device: str = "mps",
        show_preview: bool = True,
        enable_tracking: bool = True
    ) -> None:
        """
        开始推流检测

        Args:
            camera_id: 摄像头ID
            conf: 置信度阈值
            iou: IOU阈值
            device: 推理设备
            show_preview: 是否显示预览窗口
            enable_tracking: 是否启用目标跟踪
        """
        # 加载模型
        if not self._load_model(device):
            return

        # 初始化摄像头
        if not self._init_camera(camera_id):
            return

        # 初始化推流
        if not self._init_video_writer():
            self._cleanup()
            return

        logger.info("-" * 50)
        if self.use_gstreamer:
            logger.info(f"开始推流检测 (目标: {self.host}:{self.port})")
        else:
            logger.warning("⚠️  GStreamer 不可用，仅显示检测预览")
            logger.info("如需推流功能，请安装支持 GStreamer 的 OpenCV")
        logger.info(f"跟踪模式: {'开启' if enable_tracking else '关闭'}")
        logger.info(
            f"运行模式: {'无头模式 (Headless)' if self.headless else '图形界面模式'}")
        logger.info(
            f"预览窗口: {'禁用' if self.headless else ('显示' if show_preview else '隐藏')}")
        logger.info("按 Ctrl+C 退出")
        logger.info("-" * 50)

        frame_count = 0
        fps_counter = cv2.getTickFrequency()
        fps_value = 0.0
        prev_time = cv2.getTickCount()

        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    logger.error("无法读取摄像头帧")
                    break

                frame_count += 1

                # 调整帧大小
                frame = cv2.resize(
                    frame, (self.video_width, self.video_height))

                # 进行检测或跟踪
                if enable_tracking:
                    results = self.model.track(
                        frame,
                        conf=conf,
                        iou=iou,
                        device=device,
                        persist=True,
                        verbose=False
                    )
                else:
                    results = self.model.predict(
                        frame,
                        conf=conf,
                        iou=iou,
                        device=device,
                        verbose=False
                    )

                # 获取检测结果
                if results and len(results) > 0:
                    result = results[0]
                    boxes = result.boxes
                    detection_count = len(boxes) if boxes is not None else 0

                    # 绘制检测结果
                    frame = self._draw_detections(frame, boxes)
                else:
                    detection_count = 0

                # 计算FPS
                curr_time = cv2.getTickCount()
                fps_value = fps_counter / (curr_time - prev_time)
                prev_time = curr_time

                # 添加信息叠加
                frame = self._add_info_overlay(
                    frame,
                    frame_count,
                    detection_count,
                    fps_value
                )

                # 推流（如果启用了 GStreamer）
                if self.use_gstreamer and self.out is not None:
                    self.out.write(frame)

                # 显示预览（仅在非无头模式且需要预览时）
                if not self.headless and show_preview:
                    window_title = '推流预览 - 按q退出' if self.use_gstreamer else '检测预览 - 按q退出 (无推流)'
                    cv2.imshow(window_title, frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.info("用户退出")
                        break
                elif not self.headless:
                    # 即使不显示窗口，也需要处理事件循环（避免卡死）
                    cv2.waitKey(1)

                # 显示状态
                if frame_count % 30 == 0:
                    stream_status = "推流中" if self.use_gstreamer else "仅预览"
                    logger.info(
                        f"[{stream_status}] 帧: {frame_count} | 检测: {detection_count} | "
                        f"FPS: {fps_value:.1f}"
                    )

        except KeyboardInterrupt:
            logger.warning("检测被用户中断")
        except Exception as e:
            logger.error(f"检测过程中出错: {str(e)}")
        finally:
            self._cleanup()
            status_msg = "推流完成" if self.use_gstreamer else "检测完成"
            logger.success(f"{status_msg}! 共处理 {frame_count} 帧")

    def webcam_detect_with_tracking(
        self,
        conf: float = 0.25,
        iou: float = 0.45,
        device: str = "mps"
    ) -> None:
        """
        使用训练好的YOLO模型进行网络摄像头实时检测（带目标跟踪）
        此方法保留用于向后兼容，建议使用 start_streaming 方法

        Args:
            conf: 置信度阈值
            iou: IOU阈值
            device: 推理设备
        """
        logger.warning("此方法已弃用，建议使用 start_streaming 方法")
        self.start_streaming(
            camera_id=0,
            conf=conf,
            iou=iou,
            device=device,
            show_preview=True,
            enable_tracking=True
        )
