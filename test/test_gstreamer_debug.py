#!/usr/bin/env python3
"""
GStreamer 推流诊断脚本
用于诊断 GStreamer 推流问题
"""

import subprocess
import sys

import cv2
import numpy as np


def check_gstreamer_encoders():
    """检查可用的 GStreamer 编码器"""
    print("=" * 60)
    print("1. 检查 GStreamer 可用编码器")
    print("=" * 60)

    encoders = [
        ('x264enc', 'H.264 编码器（最佳质量）'),
        ('openh264enc', 'OpenH264 编码器'),
        ('avenc_h264', 'FFmpeg H.264 编码器'),
        ('omxh264enc', '硬件 H.264 编码器（树莓派）'),
        ('jpegenc', 'JPEG 编码器（备选）'),
    ]

    available_encoders = []

    for encoder, description in encoders:
        try:
            result = subprocess.run(
                ['gst-inspect-1.0', encoder],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                print(f"  ✅ {encoder:15s} - {description}")
                available_encoders.append(encoder)
            else:
                print(f"  ❌ {encoder:15s} - {description} (未安装)")
        except Exception as e:
            print(f"  ❌ {encoder:15s} - 检查失败: {str(e)}")

    if not available_encoders:
        print("\n⚠️  警告: 没有找到可用的编码器!")
        print("   请安装: sudo apt-get install gstreamer1.0-plugins-ugly")

    return available_encoders


def check_opencv_gstreamer():
    """检查 OpenCV 的 GStreamer 支持"""
    print("=" * 60)
    print("1. 检查 OpenCV GStreamer 支持")
    print("=" * 60)

    build_info = cv2.getBuildInformation()

    # 查找 GStreamer 相关信息
    lines = build_info.split('\n')
    gstreamer_found = False

    for line in lines:
        if 'GStreamer' in line or 'gstreamer' in line:
            print(f"  {line.strip()}")
            gstreamer_found = True

    if gstreamer_found:
        print("✅ OpenCV 包含 GStreamer 支持")
    else:
        print("❌ OpenCV 不包含 GStreamer 支持")

    return gstreamer_found


def test_gstreamer_pipeline(host="127.0.0.1", port=5004):
    """测试 GStreamer 管道"""
    print("\n" + "=" * 60)
    print("2. 测试 GStreamer 管道")
    print("=" * 60)

    # 测试多种管道格式
    pipelines = [
        # 格式 1: appsrc 方式
        (
            "appsrc ! videoconvert ! "
            "video/x-raw,format=I420,width=640,height=480,framerate=30/1 ! "
            "x264enc bitrate=500 tune=zerolatency speed-preset=ultrafast ! "
            "rtph264pay config-interval=1 pt=96 ! "
            f"udpsink host={host} port={port}"
        ),
        # 格式 2: 简化的 appsrc 方式
        (
            "appsrc ! videoconvert ! x264enc tune=zerolatency ! "
            f"rtph264pay ! udpsink host={host} port={port}"
        ),
        # 格式 3: 使用 XVID 编码
        (
            f"appsrc ! videoconvert ! avenc_mpeg4 ! "
            f"mpegtsmux ! udpsink host={host} port={port}"
        ),
    ]

    for idx, pipeline in enumerate(pipelines, 1):
        print(f"\n测试管道 {idx}:")
        print(f"  {pipeline}")

        try:
            # 尝试创建 VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            out = cv2.VideoWriter(
                pipeline,
                cv2.CAP_GSTREAMER,
                fourcc,
                30.0,
                (640, 480),
                True
            )

            if out.isOpened():
                print(f"  ✅ 管道 {idx} 初始化成功")

                # 尝试写入一帧测试图像
                test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(test_frame, "Test Frame", (200, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                result = out.write(test_frame)
                print(f"  ✅ 成功写入测试帧")

                out.release()
                return True, pipeline
            else:
                print(f"  ❌ 管道 {idx} 初始化失败")

        except Exception as e:
            print(f"  ❌ 管道 {idx} 异常: {str(e)}")

    return False, None


def test_alternative_method(host="127.0.0.1", port=5004):
    """测试替代方法：使用 CAP_GSTREAMER 常量"""
    print("\n" + "=" * 60)
    print("3. 测试替代初始化方法")
    print("=" * 60)

    pipeline = (
        f"appsrc ! videoconvert ! x264enc tune=zerolatency ! "
        f"rtph264pay ! udpsink host={host} port={port}"
    )

    print(f"管道: {pipeline}")

    try:
        # 方法 1: 使用 CAP_GSTREAMER 参数
        out = cv2.VideoWriter(
            pipeline,
            cv2.CAP_GSTREAMER,
            0,  # fourcc 设为 0
            30.0,
            (640, 480),
            True
        )

        if out.isOpened():
            print("  ✅ 方法 1 成功 (CAP_GSTREAMER + fourcc=0)")
            out.release()
            return True
        else:
            print("  ❌ 方法 1 失败")

    except Exception as e:
        print(f"  ❌ 方法 1 异常: {str(e)}")

    return False


def test_camera():
    """测试摄像头"""
    print("\n" + "=" * 60)
    print("4. 测试摄像头")
    print("=" * 60)

    try:
        cap = cv2.VideoCapture(0)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"  ✅ 摄像头工作正常")
                print(f"  - 分辨率: {frame.shape[1]}x{frame.shape[0]}")
                print(f"  - 帧率: {cap.get(cv2.CAP_PROP_FPS)}")
            else:
                print("  ⚠️  摄像头已打开但无法读取帧")

            cap.release()
            return True
        else:
            print("  ❌ 无法打开摄像头")
            return False

    except Exception as e:
        print(f"  ❌ 摄像头测试异常: {str(e)}")
        return False


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║       GStreamer 推流诊断工具                          ║
    ║                                                       ║
    ║  用于诊断 OpenCV GStreamer 推流问题                   ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    print(f"OpenCV 版本: {cv2.__version__}")
    print(f"Python 版本: {sys.version}")

    # 1. 检查可用编码器
    available_encoders = check_gstreamer_encoders()

    # 2. 检查 OpenCV GStreamer 支持
    has_gstreamer = check_opencv_gstreamer()

    if not has_gstreamer:
        print("\n❌ 错误: OpenCV 不支持 GStreamer")
        print("   请安装支持 GStreamer 的 OpenCV 版本")
        return 1

    # 3. 测试管道
    success, working_pipeline = test_gstreamer_pipeline()

    # 4. 测试替代方法
    if not success:
        success = test_alternative_method()

    # 5. 测试摄像头
    test_camera()

    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)

    print(f"\n可用编码器: {len(available_encoders)}/{5}")
    for encoder in available_encoders:
        print(f"  - {encoder}")

    if success:
        print("\n✅ GStreamer 推流功能正常")
        if working_pipeline:
            print(f"\n推荐使用的管道:")
            print(f"  {working_pipeline}")
    else:
        print("\n❌ GStreamer 推流存在问题")
        print("\n可能的解决方案:")

        if not available_encoders:
            print("  【关键】安装编码器 (必须):")
            print("     sudo apt-get install gstreamer1.0-plugins-ugly")
            print("     sudo apt-get install gstreamer1.0-plugins-bad")
            print("     sudo apt-get install gstreamer1.0-libav")

        print("\n  其他建议:")
        print("  1. 检查 GStreamer 是否正确安装:")
        print("     gst-launch-1.0 --version")
        print("  2. 测试 GStreamer 管道:")
        print("     gst-launch-1.0 videotestsrc ! autovideosink")
        print("  3. 验证编码器:")
        print("     gst-inspect-1.0 x264enc")
        print("  4. 检查网络和防火墙设置")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
