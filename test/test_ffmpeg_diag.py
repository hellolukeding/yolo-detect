#!/usr/bin/env python3
"""
FFmpeg 推流测试工具
用于测试 FFmpeg 是否正确配置
"""

import subprocess
import sys

import cv2
import numpy as np


def check_ffmpeg():
    """检查 FFmpeg 是否安装"""
    print("=" * 60)
    print("1. 检查 FFmpeg")
    print("=" * 60)

    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # 提取版本信息
            first_line = result.stdout.split('\n')[0]
            print(f"  ✅ {first_line}")
            return True
        else:
            print("  ❌ FFmpeg 未正确安装")
            return False
    except FileNotFoundError:
        print("  ❌ FFmpeg 未安装")
        print("     请运行: sudo apt-get install ffmpeg")
        return False
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        return False


def test_ffmpeg_encoding():
    """测试 FFmpeg 编码功能"""
    print("\n" + "=" * 60)
    print("2. 测试 FFmpeg H.264 编码")
    print("=" * 60)

    try:
        # 创建测试视频帧
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(test_frame, "Test Frame", (200, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # FFmpeg 命令（输出到文件）
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', '640x480',
            '-r', '15',
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-t', '1',  # 1秒测试
            '-f', 'null',
            '-'
        ]

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 写入15帧（1秒）
        for _ in range(15):
            process.stdin.write(test_frame.tobytes())

        process.stdin.close()
        process.wait(timeout=5)

        if process.returncode == 0:
            print("  ✅ H.264 编码测试成功")
            return True
        else:
            print("  ❌ H.264 编码测试失败")
            stderr = process.stderr.read().decode('utf-8', errors='ignore')
            print(f"     错误: {stderr[-200:]}")
            return False

    except Exception as e:
        print(f"  ❌ 编码测试失败: {e}")
        return False


def test_rtp_output():
    """测试 RTP 输出"""
    print("\n" + "=" * 60)
    print("3. 测试 RTP 推流配置")
    print("=" * 60)

    try:
        # 测试 RTP 输出格式
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', 'testsrc=duration=1:size=640x480:rate=15',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-f', 'rtp',
            '-'
        ]

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        process.wait(timeout=5)

        if process.returncode == 0:
            print("  ✅ RTP 输出格式支持")
            return True
        else:
            print("  ⚠️  RTP 输出可能有问题")
            return False

    except Exception as e:
        print(f"  ⚠️  RTP 测试失败: {e}")
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
                print(f"     分辨率: {frame.shape[1]}x{frame.shape[0]}")
                cap.release()
                return True
            else:
                print("  ❌ 无法读取摄像头帧")
                cap.release()
                return False
        else:
            print("  ❌ 无法打开摄像头")
            return False
    except Exception as e:
        print(f"  ❌ 摄像头测试失败: {e}")
        return False


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║       FFmpeg 推流诊断工具                             ║
    ║                                                       ║
    ║  用于诊断 FFmpeg 推流配置问题                         ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    print(f"OpenCV 版本: {cv2.__version__}")
    print(f"Python 版本: {sys.version.split()[0]}")
    print()

    results = []

    # 运行所有测试
    results.append(("FFmpeg 安装", check_ffmpeg()))
    results.append(("H.264 编码", test_ffmpeg_encoding()))
    results.append(("RTP 输出", test_rtp_output()))
    results.append(("摄像头", test_camera()))

    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:20s} {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n✅ 所有测试通过！可以使用 FFmpeg 推流")
        print("\n下一步:")
        print("  poetry run python test/test_push_ffmpeg.py")
    else:
        print("\n❌ 部分测试失败")
        print("\n建议:")
        if not results[0][1]:
            print("  1. 安装 FFmpeg:")
            print("     sudo apt-get install ffmpeg")
        print("  2. 检查网络连接")
        print("  3. 查看详细错误信息")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
