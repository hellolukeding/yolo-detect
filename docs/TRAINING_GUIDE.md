# YOLO Person Detection 训练指南

## 🚀 快速开始

### 1. 使用默认参数训练（自动检测 GPU）

```bash
poetry run python scripts/start_training.py
```

### 2. 指定训练参数

```bash
# 使用 MPS (Mac GPU) 训练 100 轮
poetry run python scripts/start_training.py --device mps --epochs 100 --batch 16

# 使用更大的模型
poetry run python scripts/start_training.py --model models/yolo11m.pt --batch 8

# 快速测试（3 轮）
poetry run python scripts/start_training.py --epochs 3 --name quick_test
```

## 📊 训练参数说明

### 基本参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--data` | `configs/dataset.yaml` | 数据集配置文件 |
| `--model` | `models/yolo11n.pt` | 预训练模型 (n/s/m) |
| `--epochs` | `100` | 训练轮数 |
| `--batch` | `16` | 批次大小 |
| `--imgsz` | `640` | 图片尺寸 |
| `--device` | `auto` | 训练设备 (自动检测/mps/cpu/cuda) |

### 项目参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--project` | `runs/train` | 结果保存目录 |
| `--name` | `person_detection` | 实验名称 |
| `--workers` | `8` | 数据加载线程数 |
| `--patience` | `50` | 早停耐心值 |

### 优化器参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--lr0` | `0.01` | 初始学习率 |
| `--lrf` | `0.01` | 最终学习率比例 |
| `--momentum` | `0.937` | SGD 动量 |
| `--weight_decay` | `0.0005` | 权重衰减 |
| `--warmup_epochs` | `3.0` | 预热轮数 |
| `--cos_lr` | `False` | 余弦学习率调度 |

### 数据增强参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--hsv_h` | `0.015` | HSV 色调增强 |
| `--hsv_s` | `0.7` | HSV 饱和度增强 |
| `--hsv_v` | `0.4` | HSV 明度增强 |
| `--degrees` | `0.0` | 旋转角度 |
| `--translate` | `0.1` | 平移范围 |
| `--scale` | `0.5` | 缩放范围 |
| `--shear` | `0.0` | 剪切角度 |
| `--perspective` | `0.0` | 透视变换 |
| `--flipud` | `0.0` | 上下翻转概率 |
| `--fliplr` | `0.5` | 左右翻转概率 |
| `--mosaic` | `1.0` | Mosaic 增强概率 |
| `--mixup` | `0.0` | Mixup 增强概率 |

## 🎯 推荐配置

### Mac (Apple Silicon) - GPU 训练

```bash
# 标准训练（推荐）
poetry run python scripts/start_training.py \
    --device mps \
    --epochs 100 \
    --batch 16 \
    --model models/yolo11n.pt \
    --name person_det_mps

# 高精度训练（使用更大模型）
poetry run python scripts/start_training.py \
    --device mps \
    --epochs 150 \
    --batch 8 \
    --model models/yolo11m.pt \
    --patience 100 \
    --name person_det_high_acc
```

### CPU 训练（较慢）

```bash
poetry run python scripts/start_training.py \
    --device cpu \
    --epochs 50 \
    --batch 8 \
    --workers 4 \
    --name person_det_cpu
```

### 快速测试

```bash
# 3 轮快速测试
poetry run python scripts/start_training.py \
    --epochs 3 \
    --batch 16 \
    --name quick_test

# 单轮测试
poetry run python scripts/start_training.py \
    --epochs 1 \
    --batch 8 \
    --name single_epoch_test
```

## 📈 训练结果

训练结果会保存在 `runs/train/<实验名称>/` 目录下：

```
runs/train/person_detection/
├── weights/
│   ├── best.pt          # 最佳模型（根据 mAP）
│   └── last.pt          # 最后一轮模型
├── args.yaml            # 训练参数
├── results.csv          # 训练指标
├── results.png          # 训练曲线
├── confusion_matrix.png # 混淆矩阵
├── F1_curve.png         # F1 曲线
├── P_curve.png          # 精确率曲线
├── R_curve.png          # 召回率曲线
└── PR_curve.png         # PR 曲线
```

## 🔧 故障排除

### 问题：GPU 未被识别

```bash
# 检查 MPS 是否可用
poetry run python -c "import torch; print('MPS 可用:', torch.backends.mps.is_available())"
```

### 问题：内存不足

- 减小批次大小：`--batch 8` 或 `--batch 4`
- 减小图片尺寸：`--imgsz 416`
- 使用更小的模型：`--model models/yolo11n.pt`

### 问题：训练速度慢

- 确保使用 GPU：`--device mps`
- 增加工作线程：`--workers 8`
- 使用更小的模型：`--model models/yolo11n.pt`

## 📚 模型选择

| 模型 | 参数量 | 速度 | 精度 | 适用场景 |
|------|--------|------|------|----------|
| yolo11n.pt | 2.6M | 最快 | 中等 | 实时检测、嵌入式设备 |
| yolo11s.pt | 9.4M | 快 | 良好 | 平衡速度和精度 |
| yolo11m.pt | 20.1M | 中等 | 高 | 高精度需求 |

## 🎓 进阶技巧

### 1. 使用余弦学习率调度

```bash
poetry run python scripts/start_training.py --cos_lr --lrf 0.001
```

### 2. 增强数据增强

```bash
poetry run python scripts/start_training.py \
    --degrees 10 \
    --translate 0.2 \
    --scale 0.9 \
    --mixup 0.1
```

### 3. 自定义学习率

```bash
poetry run python scripts/start_training.py \
    --lr0 0.001 \
    --lrf 0.0001 \
    --warmup_epochs 5
```

## 📞 获取帮助

```bash
# 查看所有参数
poetry run python scripts/start_training.py --help
```
