#!/usr/bin/env python3
"""快速诊断 FFmpeg RTP 推流问题"""

import subprocess
import sys

# FFmpeg 测试命令（推流到本地回环测试）
cmd = [
    'ffmpeg',
    '-f', 'lavfi',
    '-i', 'testsrc=duration=2:size=640x480:rate=15',
    '-c:v', 'libx264',
    '-preset', 'ultrafast',
    '-tune', 'zerolatency',
    '-profile:v', 'baseline',
    '-pix_fmt', 'yuv420p',  # 强制使用 YUV420P
    '-b:v', '400k',
    '-g', '15',
    '-f', 'rtp',
    '-payload_type', '96',
    '-pkt_size', '1200',
    'rtp://127.0.0.1:5004'
]

print("测试 FFmpeg RTP 推流到本地...")
print(f"命令: {' '.join(cmd)}")
print()

try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    print(f"返回码: {result.returncode}")
    print()
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
        print()
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode == 0:
        print("\n✅ FFmpeg RTP 推流测试成功！")
    else:
        print(f"\n❌ FFmpeg 失败，返回码: {result.returncode}")
        
except subprocess.TimeoutExpired:
    print("⚠️  命令超时（这可能是正常的，说明推流正在进行）")
except Exception as e:
    print(f"❌ 错误: {e}")
    sys.exit(1)
