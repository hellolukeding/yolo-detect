# YOLO 使用指南

## 🚀 快速开始

### 最简单的使用方式

```bash
# 运行快速入门示例
poetry run python scripts/quickstart.py
```

这个脚本会：

1. 自动下载 YOLO11n 模型
2. 检测一张示例图像
3. 显示检测结果
4. 保存带标注的图像

## 📚 可用的示例脚本

### 1. 快速入门 (quickstart.py)

最简单的使用示例，适合初学者。

```bash
poetry run python scripts/quickstart.py
```

### 2. 图像检测 (detect_image.py)

检测单张或多张图像。

```bash
poetry run python scripts/detect_image.py
```

功能：

- 使用预训练模型检测图像
- 显示检测到的目标类别、置信度和位置
- 自动保存带标注的结果图像

### 3. 视频检测 (detect_video.py)

检测视频文件或实时摄像头。

```bash
poetry run python scripts/detect_video.py
```

功能：

- 视频文件检测
- 摄像头实时检测
- YouTube 视频检测
- 目标跟踪

### 4. 批量检测 (batch_detect.py)

批量处理多张图像。

```bash
poetry run python scripts/batch_detect.py
```

功能：

- 批量处理文件夹中的所有图像
- 导出 JSON 格式的检测结果
- 统计信息

### 5. 高级示例 (advanced_examples.py)

展示更多高级用法。

```bash
poetry run python scripts/advanced_examples.py
```

功能：

- 自定义结果处理
- 模型对比
- 类别过滤
- 性能基准测试

### 6. 模型训练 (train_model.py)

训练自定义 YOLO 模型。

```bash
poetry run python scripts/train_model.py
```

功能：

- 训练自定义数据集
- 模型验证
- 模型导出

## 🎯 常用命令

### 使用命令行工具

YOLO 提供了便捷的命令行接口：

```bash
# 检测图像
poetry run yolo predict model=yolo11n.pt source=image.jpg

# 检测视频
poetry run yolo predict model=yolo11n.pt source=video.mp4

# 使用摄像头
poetry run yolo predict model=yolo11n.pt source=0 show=True

# 训练模型
poetry run yolo train data=dataset.yaml model=yolo11n.pt epochs=100

# 验证模型
poetry run yolo val model=best.pt data=dataset.yaml

# 导出模型
poetry run yolo export model=yolo11n.pt format=onnx
```

### 使用 Python API

更灵活的 Python 代码方式：

```python
from ultralytics import YOLO

# 加载模型
model = YOLO('yolo11n.pt')

# 检测
results = model('image.jpg')

# 处理结果
for result in results:
    boxes = result.boxes
    for box in boxes:
        print(f"类别: {model.names[int(box.cls)]}")
        print(f"置信度: {box.conf[0]:.2f}")
```

## 🔧 自定义参数

### 调整置信度阈值

```python
# 只显示高置信度的检测结果
results = model('image.jpg', conf=0.5)  # 默认是0.25
```

### 只检测特定类别

```python
# 只检测人和车（COCO类别ID: 0=person, 2=car）
results = model('image.jpg', classes=[0, 2])
```

### 调整图像大小

```python
# 使用更大的图像尺寸可以提高准确度（但速度会变慢）
results = model('image.jpg', imgsz=1280)  # 默认是640
```

### 使用 GPU 加速

```python
# 使用GPU 0
results = model('image.jpg', device='0')

# 使用多个GPU
results = model('image.jpg', device='0,1')

# 使用CPU
results = model('image.jpg', device='cpu')
```

## 📊 YOLO 模型选择

| 模型       | 大小  | 速度      | 精度               | 适用场景           |
| ---------- | ----- | --------- | ------------------ | ------------------ |
| yolo11n.pt | 2.6MB | ⚡️⚡️⚡️ | ⭐️⭐️⭐️          | 实时应用、移动设备 |
| yolo11s.pt | 9.4MB | ⚡️⚡️    | ⭐️⭐️⭐️⭐️       | 平衡性能和速度     |
| yolo11m.pt | 20MB  | ⚡️       | ⭐️⭐️⭐️⭐️⭐️    | 高精度应用         |
| yolo11l.pt | 25MB  | 🐌        | ⭐️⭐️⭐️⭐️⭐️    | 服务器端部署       |
| yolo11x.pt | 57MB  | 🐌🐌      | ⭐️⭐️⭐️⭐️⭐️⭐️ | 最高精度要求       |

更换模型只需修改模型名称：

```python
model = YOLO('yolo11s.pt')  # 使用small模型
```

## 📁 结果保存位置

默认情况下，检测结果会保存在：

```
runs/
├── detect/
│   ├── predict/      # 预测结果
│   ├── predict2/     # 第二次预测
│   └── ...
└── train/
    ├── exp/          # 训练结果
    └── ...
```

## 🎨 结果可视化

检测结果会自动保存带标注的图像，包括：

- 边界框（bounding box）
- 类别标签
- 置信度分数

你可以在 `runs/detect/predict/` 文件夹中找到这些图像。

## 💡 使用技巧

### 1. 提高检测准确度

- 使用更大的模型（如 yolo11m.pt）
- 增加图像尺寸（imgsz=1280）
- 提高置信度阈值（conf=0.5）

### 2. 提高检测速度

- 使用更小的模型（如 yolo11n.pt）
- 减小图像尺寸（imgsz=320）
- 使用 GPU 加速

### 3. 减少误检

- 提高置信度阈值
- 调整 IOU 阈值（iou=0.5）
- 只检测需要的类别

### 4. 处理大量图像

- 使用批处理（batch=16）
- 使用流式处理（stream=True）

## 🔗 更多资源

- **详细使用说明**: 查看 `USAGE.md`
- **官方文档**: https://docs.ultralytics.com/
- **示例脚本**: `scripts/` 文件夹
- **社区支持**: https://community.ultralytics.com/

## ❓ 常见问题

### Q: 如何检测我自己的图像？

```python
# 方法1: 使用脚本（推荐）
poetry run python scripts/detect_image.py

# 方法2: 使用命令行
poetry run yolo predict model=yolo11n.pt source=/path/to/your/image.jpg

# 方法3: 修改脚本
# 编辑 scripts/quickstart.py，将图像路径改为你的图像
```

### Q: 如何使用摄像头？

```bash
poetry run yolo predict model=yolo11n.pt source=0 show=True
```

### Q: 模型下载很慢怎么办？

首次运行时会自动下载模型（约 5-50MB），请耐心等待。下载后会缓存在本地，之后使用不需要再次下载。

### Q: 如何训练自己的模型？

参考 `scripts/train_model.py` 中的示例，需要准备 YOLO 格式的数据集。

## 🎓 学习路径

1. **初学者**: 从 `quickstart.py` 开始
2. **进阶**: 尝试 `detect_image.py` 和 `detect_video.py`
3. **高级**: 查看 `advanced_examples.py`
4. **专家**: 学习 `train_model.py` 训练自定义模型

开始你的 YOLO 之旅吧！🚀
