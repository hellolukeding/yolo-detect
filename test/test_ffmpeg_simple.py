#!/usr/bin/env python3
"""
简单的 FFmpeg RTP 推流测试
不包含 YOLO 检测，仅测试推流功能
"""

import subprocess
import cv2
import time


def test_ffmpeg_rtp_stream(host="115.120.237.79", port=5004, duration=10):
    """测试 FFmpeg RTP 推流"""
    print(f"""
    ╔═══════════════════════════════════════════════════════╗
    ║      FFmpeg RTP 推流测试                              ║
    ║                                                       ║
    ║  测试 FFmpeg 是否能正常推流到 {host:15s}    ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # FFmpeg 命令
    ffmpeg_cmd = [
        'ffmpeg',
        '-f', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', '640x480',
        '-r', '15',
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-profile:v', 'baseline',
        '-b:v', '400k',
        '-g', '15',
        '-f', 'rtp',
        '-payload_type', '96',
        '-pkt_size', '1200',
        f'rtp://{host}:{port}'
    ]
    
    print(f"FFmpeg 命令:")
    print(f"  {' '.join(ffmpeg_cmd)}")
    print()
    
    try:
        # 启动 FFmpeg
        print("启动 FFmpeg 进程...")
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待一下，看看是否立即退出
        time.sleep(0.5)
        if process.poll() is not None:
            print(f"❌ FFmpeg 进程已退出，返回码: {process.returncode}")
            stderr = process.stderr.read().decode('utf-8', errors='ignore')
            print(f"\nFFmpeg 错误输出:")
            print(stderr)
            return False
        
        print("✅ FFmpeg 进程启动成功")
        print()
        
        # 打开摄像头
        print("打开摄像头...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ 无法打开摄像头")
            process.terminate()
            return False
        
        print("✅ 摄像头打开成功")
        print()
        print(f"开始推流 {duration} 秒...")
        print("按 Ctrl+C 提前停止")
        print()
        
        frame_count = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                print("❌ 无法读取摄像头帧")
                break
            
            # 调整尺寸
            frame = cv2.resize(frame, (640, 480))
            
            # 写入 FFmpeg
            try:
                if process.poll() is not None:
                    print(f"\n❌ FFmpeg 进程已退出，返回码: {process.returncode}")
                    stderr = process.stderr.read().decode('utf-8', errors='ignore')
                    print(f"FFmpeg 错误输出:\n{stderr[-500:]}")
                    break
                
                process.stdin.write(frame.tobytes())
                process.stdin.flush()
                frame_count += 1
                
                # 每秒显示一次状态
                if frame_count % 15 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"  已推流: {elapsed:.1f}s | {frame_count} 帧 | {fps:.1f} fps")
                
            except BrokenPipeError:
                print("\n❌ FFmpeg 管道断开")
                break
            except Exception as e:
                print(f"\n❌ 写入失败: {e}")
                break
        
        print()
        print("=" * 60)
        print("测试完成")
        print("=" * 60)
        print(f"总帧数: {frame_count}")
        print(f"总时长: {time.time() - start_time:.1f}s")
        print(f"平均帧率: {frame_count / (time.time() - start_time):.1f} fps")
        
        # 清理
        cap.release()
        process.stdin.close()
        process.wait(timeout=5)
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            if 'cap' in locals():
                cap.release()
            if 'process' in locals():
                process.terminate()
        except:
            pass


if __name__ == "__main__":
    import sys
    
    # 可以从命令行指定主机和端口
    host = sys.argv[1] if len(sys.argv) > 1 else "115.120.237.79"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5004
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    success = test_ffmpeg_rtp_stream(host, port, duration)
    exit(0 if success else 1)
