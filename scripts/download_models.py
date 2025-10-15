"""
下载YOLO模型到models文件夹
"""

import shutil
from pathlib import Path

from ultralytics import YOLO

# 创建models文件夹
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

# 定义要下载的模型列表
models_to_download = [
    "yolo11n.pt",      # Nano - 最快
    "yolo11s.pt",      # Small - 平衡
    "yolo11m.pt",      # Medium - 更准确
    # "yolo11l.pt",    # Large - 大模型（取消注释如需下载）
    # "yolo11x.pt",    # Extra Large - 最大（取消注释如需下载）
]

print("开始下载YOLO模型到models文件夹...\n")

for model_name in models_to_download:
    print(f"正在下载: {model_name}")

    try:
        # 加载模型会自动下载
        model = YOLO(model_name)

        # 移动模型文件到models文件夹
        source = Path(model_name)
        destination = models_dir / model_name

        if source.exists() and source != destination:
            shutil.move(str(source), str(destination))
            print(f"✓ {model_name} 已下载并移动到 models/{model_name}\n")
        elif destination.exists():
            print(f"✓ {model_name} 已存在于 models/{model_name}\n")
        else:
            print(f"✓ {model_name} 下载完成\n")

    except Exception as e:
        print(f"✗ 下载 {model_name} 失败: {e}\n")

print("=" * 50)
print("下载完成！")
print(f"模型保存位置: {models_dir.absolute()}")
print("\n可用模型:")
for model_file in sorted(models_dir.glob("*.pt")):
    size_mb = model_file.stat().st_size / (1024 * 1024)
    print(f"  - {model_file.name} ({size_mb:.1f} MB)")
