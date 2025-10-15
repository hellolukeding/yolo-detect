"""
YOLO 视频检测示例
使用YOLO模型对视频进行实时目标检测
"""

from pathlib import Path

import cv2
from ultralytics import YOLO


def detect_video(model_path: str = "yolo11n.pt",
                 video_path: str = 0,
                 conf: float = 0.25,
                 save: bool = True,
                 show: bool = False):
    """
    使用YOLO模型检测视频中的目标

    Args:
        model_path: 模型路径
        video_path: 视频路径，0表示使用摄像头
        conf: 置信度阈值
        save: 是否保存结果视频
        show: 是否显示实时检测结果
    """
    # 加载模型
    print(f"加载模型: {model_path}")
    model = YOLO(model_path)

    # 执行检测
    if video_path == 0:
        print("使用摄像头进行实时检测...")
    else:
        print(f"检测视频: {video_path}")

    # 使用track方法进行目标跟踪
    results = model.track(
        source=video_path,
        conf=conf,
        save=save,
        show=show,
        stream=True  # 使用流式处理，适合长视频
    )

    # 逐帧处理结果
    for frame_idx, result in enumerate(results):
        boxes = result.boxes
        if boxes is not None and len(boxes) > 0:
            print(f"帧 {frame_idx}: 检测到 {len(boxes)} 个目标")

    print("\n检测完成!")
    return results


def detect_youtube_video(model_path: str = "yolo11n.pt",
                         youtube_url: str = "https://youtu.be/LNwODJXcvt4"):
    """
    检测YouTube视频

    Args:
        model_path: 模型路径
        youtube_url: YouTube视频URL
    """
    print(f"加载模型: {model_path}")
    model = YOLO(model_path)

    print(f"检测YouTube视频: {youtube_url}")
    results = model(youtube_url, save=True)

    print("检测完成!")
    return results


if __name__ == "__main__":
    # 示例1: 检测本地视频文件
    # detect_video(video_path="path/to/your/video.mp4")

    # 示例2: 使用摄像头进行实时检测
    # detect_video(video_path=0, show=True)

    # 示例3: 检测YouTube视频
    print("=" * 50)
    print("示例: 检测YouTube视频")
    print("=" * 50)
    detect_youtube_video()
