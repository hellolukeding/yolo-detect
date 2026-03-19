# 多任务视觉检测系统

基于 YOLO11 和深度学习的多任务视觉检测系统，支持行人检测、人脸检测、表情识别和年龄估计。

## 功能特性

- 🚶 **行人检测** - 检测图像/视频中的行人 (mAP50: 0.72)
- 😊 **人脸检测** - 检测人脸区域 (mAP50: 0.76)
- 😀 **表情识别** - 识别7种表情 (准确率: 65%)
- 🎂 **年龄估计** - 预测年龄 (MAE: 8.7岁)

## 目录结构

```
yolo-detect/
├── assets/                  # 测试资源
├── configs/                 # 配置文件
│   ├── config.yaml         # 主配置
│   ├── dataset.yaml        # 数据集配置
│   ├── face_detection.yaml # 人脸检测配置
│   └── person_detection.yaml
├── datasets/                # 数据集
├── models/                  # 模型文件
│   ├── person_detector.pt  # 行人检测模型
│   ├── face_detector.pt    # 人脸检测模型
│   ├── emotion_model.pt    # 表情识别模型
│   ├── age_model.pt        # 年龄估计模型
│   └── pretrained/         # 预训练模型
├── outputs/                 # 输出结果
│   └── videos/             # 视频输出
├── scripts/                 # 工具脚本
├── src/                     # 源代码
│   ├── pipeline.py         # 推理流水线
│   ├── train_emotion.py    # 表情模型训练
│   ├── train_age.py        # 年龄模型训练
│   └── utils/              # 工具函数
├── docs/                    # 文档
├── pyproject.toml          # 项目配置
└── README.md
```

## 快速开始

### 安装依赖

```bash
poetry install
```

### 运行推理

```bash
# 处理视频
python -c "
from src.pipeline import MultiTaskPipeline
pipeline = MultiTaskPipeline('configs/config.yaml')
pipeline.process_video('assets/your_video.mp4', 'outputs/videos/result.mp4', show=False)
"

# 处理图片
python -c "
from src.pipeline import MultiTaskPipeline
pipeline = MultiTaskPipeline('configs/config.yaml')
result, persons = pipeline.process_frame(image)
"
```

### 测试所有模型

```bash
python scripts/test_all.py
```

## 模型信息

| 模型 | 任务 | 架构 | 数据集 | 性能 |
|------|------|------|--------|------|
| person_detector | 行人检测 | YOLO11x | CityPersons | mAP50: 0.72 |
| face_detector | 人脸检测 | YOLO11x | WiderFace | mAP50: 0.76 |
| emotion_model | 表情识别 | CNN | FER2013 | Acc: 65% |
| age_model | 年龄估计 | ResNet50 | WikiFace | MAE: 8.7 |

## 表情类别

- angry (愤怒)
- disgust (厌恶)
- fear (恐惧)
- happy (开心)
- neutral (中性)
- sad (悲伤)
- surprise (惊讶)

## 硬件要求

- GPU: NVIDIA RTX 5090 (32GB VRAM)
- CUDA: 13.0
- Python: 3.12

## License

MIT
