"""
GStreamer 接收端脚本
用于接收来自 PushStreamer 的视频流
"""

import subprocess
import sys
from typing import Optional


class StreamReceiver:
    """视频流接收器"""

    def __init__(self, port: int = 5004, host: str = "0.0.0.0"):
        """
        初始化接收器

        Args:
            port: 监听端口
            host: 监听地址 (0.0.0.0 表示所有接口)
        """
        self.port = port
        self.host = host

    def receive_and_display(self) -> None:
        """接收并显示视频流"""
        print(f"正在监听 UDP 端口 {self.port}...")
        print("按 Ctrl+C 退出")
        print("-" * 60)

        pipeline = [
            "gst-launch-1.0",
            "udpsrc", f"port={self.port}",
            "!",
            "application/x-rtp,encoding-name=H264,payload=96",
            "!",
            "rtph264depay",
            "!",
            "h264parse",
            "!",
            "avdec_h264",
            "!",
            "videoconvert",
            "!",
            "autovideosink"
        ]

        try:
            subprocess.run(" ".join(pipeline), shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ 错误: {e}")
        except KeyboardInterrupt:
            print("\n✅ 接收已停止")

    def receive_and_save(self, output_file: str = "output.mp4") -> None:
        """接收并保存视频流到文件"""
        print(f"正在监听 UDP 端口 {self.port}...")
        print(f"保存到文件: {output_file}")
        print("按 Ctrl+C 停止录制")
        print("-" * 60)

        pipeline = [
            "gst-launch-1.0",
            "udpsrc", f"port={self.port}",
            "!",
            "application/x-rtp,encoding-name=H264,payload=96",
            "!",
            "rtph264depay",
            "!",
            "h264parse",
            "!",
            "mp4mux",
            "!",
            "filesink", f"location={output_file}"
        ]

        try:
            subprocess.run(" ".join(pipeline), shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ 错误: {e}")
        except KeyboardInterrupt:
            print(f"\n✅ 视频已保存到: {output_file}")

    def receive_with_vlc(self) -> None:
        """使用 VLC 接收视频流"""
        url = f"udp://@:{self.port}"
        print(f"正在使用 VLC 打开: {url}")
        print("-" * 60)

        try:
            subprocess.run(["vlc", url], check=True)
        except FileNotFoundError:
            print("❌ 错误: 未找到 VLC，请安装 VLC 播放器")
        except subprocess.CalledProcessError as e:
            print(f"❌ 错误: {e}")

    def receive_with_ffplay(self) -> None:
        """使用 FFplay 接收视频流"""
        url = f"udp://0.0.0.0:{self.port}"
        print(f"正在使用 FFplay 打开: {url}")
        print("-" * 60)

        try:
            subprocess.run([
                "ffplay",
                "-protocol_whitelist", "file,udp,rtp",
                "-i", url
            ], check=True)
        except FileNotFoundError:
            print("❌ 错误: 未找到 FFplay，请安装 FFmpeg")
        except subprocess.CalledProcessError as e:
            print(f"❌ 错误: {e}")

    def check_gstreamer_installed(self) -> bool:
        """检查 GStreamer 是否已安装"""
        try:
            result = subprocess.run(
                ["gst-launch-1.0", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ GStreamer 已安装:")
            print(result.stdout.split('\n')[0])
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("❌ GStreamer 未安装")
            print("\n安装方法:")
            print("macOS:   brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly")
            print("Ubuntu:  sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good")
            print("Windows: 从 https://gstreamer.freedesktop.org/download/ 下载安装")
            return False


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║         GStreamer 视频流接收器                        ║
    ║                                                       ║
    ║  功能：接收来自 PushStreamer 的视频流                ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    # 获取端口号
    port = 5004
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ 无效的端口号: {sys.argv[1]}")
            sys.exit(1)

    receiver = StreamReceiver(port=port)

    # 检查 GStreamer
    print("检查依赖...")
    print("-" * 60)
    if not receiver.check_gstreamer_installed():
        print("\n请先安装 GStreamer")
        sys.exit(1)

    print()

    # 显示菜单
    while True:
        print("\n" + "=" * 60)
        print("接收方式选择")
        print("=" * 60)
        print(f"监听端口: {port}")
        print()
        print("1. 使用 GStreamer 接收并显示")
        print("2. 使用 GStreamer 接收并保存到文件")
        print("3. 使用 VLC 播放器接收")
        print("4. 使用 FFplay 接收")
        print("0. 退出")
        print("=" * 60)

        choice = input("\n请选择 (0-4): ").strip()

        if choice == "1":
            receiver.receive_and_display()
        elif choice == "2":
            output_file = input("输入输出文件名 (默认: output.mp4): ").strip()
            if not output_file:
                output_file = "output.mp4"
            receiver.receive_and_save(output_file)
        elif choice == "3":
            receiver.receive_with_vlc()
        elif choice == "4":
            receiver.receive_with_ffplay()
        elif choice == "0":
            print("退出程序")
            break
        else:
            print("❌ 无效选择，请重试")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已退出")
        sys.exit(0)
