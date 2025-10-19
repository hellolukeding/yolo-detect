"""
YOLO 模型跨平台迁移工具
用于打包模型及相关文件，便于在不同平台间迁移
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import torch
from ultralytics import YOLO


def get_model_info(model_path: str):
    """获取模型详细信息"""
    try:
        model = YOLO(model_path)
        checkpoint = torch.load(model_path, map_location='cpu')

        info = {
            "model_path": str(model_path),
            "model_name": Path(model_path).name,
            "model_size_mb": Path(model_path).stat().st_size / (1024 * 1024),
            "model_type": model.model_name if hasattr(model, 'model_name') else "YOLO11",
            "classes": model.names,
            "num_classes": len(model.names),
            "pytorch_version": checkpoint.get('pytorch_version', 'unknown'),
            "ultralytics_version": checkpoint.get('version', 'unknown'),
            "training_date": checkpoint.get('date', 'unknown'),
            "epochs_trained": checkpoint.get('epoch', 'unknown'),
        }

        return info
    except Exception as e:
        print(f"❌ 无法读取模型信息: {e}")
        return None


def validate_model(model_path: str):
    """验证模型是否可以正常加载"""
    try:
        print(f"验证模型: {model_path}")
        model = YOLO(model_path)
        print("✅ 模型加载成功!")
        print(f"   类别数量: {len(model.names)}")
        print(f"   类别: {model.names}")
        return True
    except Exception as e:
        print(f"❌ 模型验证失败: {e}")
        return False


def package_model(
    model_path: str,
    output_dir: str = None,
    include_training_results: bool = True,
    include_dataset_config: bool = True
):
    """
    打包模型及相关文件

    Args:
        model_path: 模型文件路径
        output_dir: 输出目录
        include_training_results: 是否包含训练结果图表
        include_dataset_config: 是否包含数据集配置
    """
    model_path = Path(model_path)

    if not model_path.exists():
        print(f"❌ 模型文件不存在: {model_path}")
        return None

    # 验证模型
    if not validate_model(str(model_path)):
        return None

    # 创建输出目录
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"model_package_{timestamp}"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 开始打包模型...")
    print(f"   输出目录: {output_path.absolute()}")

    # 1. 复制模型文件
    print("\n1️⃣  复制模型文件...")
    model_dest = output_path / model_path.name
    shutil.copy2(model_path, model_dest)
    print(f"   ✅ {model_path.name}")

    # 2. 获取并保存模型信息
    print("\n2️⃣  保存模型信息...")
    model_info = get_model_info(str(model_path))
    if model_info:
        info_path = output_path / "model_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, indent=2, ensure_ascii=False)
        print(f"   ✅ model_info.json")

    # 3. 复制训练结果（如果存在）
    if include_training_results:
        print("\n3️⃣  复制训练结果...")
        # 假设模型在 runs/train/xxx/weights/best.pt
        if "runs/train" in str(model_path):
            training_dir = model_path.parent.parent

            # 复制结果图表
            for img_file in training_dir.glob("*.jpg"):
                dest = output_path / "training_results" / img_file.name
                dest.parent.mkdir(exist_ok=True)
                shutil.copy2(img_file, dest)
                print(f"   ✅ {img_file.name}")

            # 复制结果 CSV
            results_csv = training_dir / "results.csv"
            if results_csv.exists():
                shutil.copy2(results_csv, output_path /
                             "training_results" / "results.csv")
                print(f"   ✅ results.csv")

            # 复制训练参数
            args_yaml = training_dir / "args.yaml"
            if args_yaml.exists():
                shutil.copy2(args_yaml, output_path / "args.yaml")
                print(f"   ✅ args.yaml")

    # 4. 复制数据集配置（如果存在）
    if include_dataset_config:
        print("\n4️⃣  查找数据集配置...")
        dataset_configs = list(Path("configs").glob(
            "*.yaml")) if Path("configs").exists() else []
        if dataset_configs:
            for config in dataset_configs:
                dest = output_path / "configs" / config.name
                dest.parent.mkdir(exist_ok=True)
                shutil.copy2(config, dest)
                print(f"   ✅ {config.name}")

    # 5. 创建 requirements.txt
    print("\n5️⃣  创建依赖文件...")
    requirements = [
        f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# PyTorch 版本: {torch.__version__}",
        "",
        "ultralytics>=8.0.0",
        "torch>=2.0.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "pillow>=10.0.0",
    ]

    req_path = output_path / "requirements.txt"
    with open(req_path, 'w') as f:
        f.write('\n'.join(requirements))
    print(f"   ✅ requirements.txt")

    # 6. 创建使用说明
    print("\n6️⃣  创建使用说明...")
    readme_content = f"""# YOLO 模型包

## 📦 包含内容

- `{model_path.name}`: 训练好的 YOLO 模型
- `model_info.json`: 模型详细信息
- `requirements.txt`: Python 依赖
- `training_results/`: 训练结果图表（如果有）
- `configs/`: 数据集配置（如果有）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 加载模型

```python
from ultralytics import YOLO

# 加载模型
model = YOLO('{model_path.name}')

# 进行检测
results = model('image.jpg')

# 显示结果
results[0].show()
```

### 3. 命令行使用

```bash
# 图像检测
yolo predict model={model_path.name} source=image.jpg

# 视频检测
yolo predict model={model_path.name} source=video.mp4

# 网络摄像头
yolo predict model={model_path.name} source=0 show=True
```

## 📊 模型信息

"""

    if model_info:
        readme_content += f"""
- **模型类型**: {model_info.get('model_type', 'YOLO')}
- **类别数量**: {model_info.get('num_classes', 'unknown')}
- **训练轮数**: {model_info.get('epochs_trained', 'unknown')}
- **PyTorch 版本**: {model_info.get('pytorch_version', 'unknown')}
- **模型大小**: {model_info.get('model_size_mb', 0):.2f} MB

### 检测类别

```python
{model_info.get('classes', {})}
```
"""

    readme_content += """

## 🖥️ 跨平台兼容性

此模型可以在以下平台使用：

- ✅ macOS (Apple Silicon / Intel)
- ✅ Linux (x86_64)
- ✅ Windows (x86_64)
- ✅ ARM 设备 (树莓派, Jetson Nano 等)

### 不同平台的设备选择

```python
# macOS (Apple Silicon)
model.predict(source='image.jpg', device='mps')

# NVIDIA GPU
model.predict(source='image.jpg', device=0)  # or device='cuda'

# CPU
model.predict(source='image.jpg', device='cpu')
```

## 📝 注意事项

1. 确保 PyTorch 和 Ultralytics 版本匹配
2. 根据目标平台选择合适的硬件加速参数
3. 如需更好的兼容性，可以导出为 ONNX 格式

```bash
yolo export model={model_path.name} format=onnx
```

---

打包时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    readme_path = output_path / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"   ✅ README.md")

    # 完成
    print("\n" + "=" * 60)
    print("✅ 模型打包完成!")
    print("=" * 60)
    print(f"\n📁 输出目录: {output_path.absolute()}")

    # 显示文件列表
    print(f"\n📋 包含文件:")
    for file in sorted(output_path.rglob("*")):
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(
                f"   {str(file.relative_to(output_path)):40s} ({size_mb:.2f} MB)")

    # 计算总大小
    total_size = sum(
        f.stat().st_size for f in output_path.rglob("*") if f.is_file())
    print(f"\n💾 总大小: {total_size / (1024 * 1024):.2f} MB")

    # 压缩建议
    print(f"\n💡 压缩打包:")
    print(f"   tar -czf {output_path.name}.tar.gz {output_path.name}")
    print(f"   或")
    print(f"   zip -r {output_path.name}.zip {output_path.name}")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="YOLO 模型跨平台迁移打包工具"
    )
    parser.add_argument(
        "model",
        type=str,
        help="模型文件路径 (例如: runs/train/person_detection/weights/best.pt)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出目录 (默认: model_package_TIMESTAMP)"
    )
    parser.add_argument(
        "--no-training-results",
        action="store_true",
        help="不包含训练结果图表"
    )
    parser.add_argument(
        "--no-dataset-config",
        action="store_true",
        help="不包含数据集配置"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="仅验证模型，不打包"
    )

    args = parser.parse_args()

    if args.validate_only:
        # 仅验证
        if validate_model(args.model):
            info = get_model_info(args.model)
            if info:
                print("\n📊 模型信息:")
                for key, value in info.items():
                    print(f"   {key}: {value}")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # 打包
        result = package_model(
            model_path=args.model,
            output_dir=args.output,
            include_training_results=not args.no_training_results,
            include_dataset_config=not args.no_dataset_config
        )

        if result:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
