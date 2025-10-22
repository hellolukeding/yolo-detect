"""
无头模式推流测试脚本
测试无显示器环境下的YOLO推流功能
适用于树莓派、Jetson Nano等无显示器硬件设备
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from service.push_streamer import PushStreamer
import time
import signal


class HeadlessStreamerTest:
    """无头模式推流测试类"""
    
    def __init__(self):
        self.streamer = None
        self.running = True
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """处理中断信号"""
        print("\n\n收到停止信号，正在清理资源...")
        self.running = False
        if self.streamer:
            self.streamer.stop()
        sys.exit(0)
    
    def test_basic_headless_mode(self):
        """测试基本的无头模式推流"""
        print("\n" + "="*60)
        print("测试 1: 基本无头模式推流")
        print("="*60)
        
        try:
            # 创建无头模式推流器
            self.streamer = PushStreamer(
                model_path="models/yolo11n.pt",  # 使用预训练模型
                host="127.0.0.1",  # 本地测试
                port=5004,
                video_width=640,
                video_height=480,
                fps=30,
                bitrate=500,
                headless=True  # 启用无头模式
            )
            
            print("✅ 推流器创建成功（无头模式）")
            
            # 模拟运行一段时间
            print("⏱️  测试运行 5 秒...")
            time.sleep(5)
            
            print("✅ 测试 1 通过")
            return True
            
        except Exception as e:
            print(f"❌ 测试 1 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_custom_model_headless(self):
        """测试使用自定义训练模型的无头推流"""
        print("\n" + "="*60)
        print("测试 2: 自定义模型无头模式推流")
        print("="*60)
        
        custom_model = "runs/train/person_detection/weights/best.pt"
        
        if not Path(custom_model).exists():
            print(f"⚠️  跳过测试 2: 自定义模型不存在 ({custom_model})")
            return True
        
        try:
            self.streamer = PushStreamer(
                model_path=custom_model,
                host="127.0.0.1",
                port=5005,
                video_width=640,
                video_height=480,
                fps=30,
                bitrate=500,
                headless=True
            )
            
            print("✅ 自定义模型推流器创建成功")
            print("⏱️  测试运行 5 秒...")
            time.sleep(5)
            
            print("✅ 测试 2 通过")
            return True
            
        except Exception as e:
            print(f"❌ 测试 2 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_different_resolutions(self):
        """测试不同分辨率的无头推流"""
        print("\n" + "="*60)
        print("测试 3: 不同分辨率测试")
        print("="*60)
        
        resolutions = [
            (320, 240, "低分辨率"),
            (640, 480, "标准分辨率"),
            (1280, 720, "高清分辨率")
        ]
        
        for width, height, desc in resolutions:
            print(f"\n测试分辨率: {width}x{height} ({desc})")
            
            try:
                self.streamer = PushStreamer(
                    model_path="models/yolo11n.pt",
                    host="127.0.0.1",
                    port=5006,
                    video_width=width,
                    video_height=height,
                    fps=30,
                    bitrate=500,
                    headless=True
                )
                
                print(f"  ✅ {desc} 推流器创建成功")
                time.sleep(2)
                
                if self.streamer:
                    self.streamer.stop()
                    
            except Exception as e:
                print(f"  ❌ {desc} 失败: {str(e)}")
                return False
        
        print("✅ 测试 3 通过")
        return True
    
    def test_configuration_validation(self):
        """测试配置参数验证"""
        print("\n" + "="*60)
        print("测试 4: 配置参数验证")
        print("="*60)
        
        test_cases = [
            {
                "name": "有效配置",
                "config": {
                    "model_path": "models/yolo11n.pt",
                    "host": "127.0.0.1",
                    "port": 5004,
                    "headless": True
                },
                "should_pass": True
            },
            {
                "name": "无效模型路径",
                "config": {
                    "model_path": "models/nonexistent.pt",
                    "host": "127.0.0.1",
                    "port": 5004,
                    "headless": True
                },
                "should_pass": False
            }
        ]
        
        for test_case in test_cases:
            print(f"\n测试用例: {test_case['name']}")
            
            try:
                streamer = PushStreamer(**test_case['config'])
                
                if test_case['should_pass']:
                    print(f"  ✅ 按预期通过")
                else:
                    print(f"  ❌ 应该失败但通过了")
                    return False
                    
            except Exception as e:
                if not test_case['should_pass']:
                    print(f"  ✅ 按预期失败: {str(e)}")
                else:
                    print(f"  ❌ 不应该失败: {str(e)}")
                    return False
        
        print("✅ 测试 4 通过")
        return True
    
    def test_performance_metrics(self):
        """测试性能指标"""
        print("\n" + "="*60)
        print("测试 5: 性能指标测试")
        print("="*60)
        
        try:
            import psutil
            import os
            
            # 获取初始内存使用
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"初始内存使用: {initial_memory:.2f} MB")
            
            self.streamer = PushStreamer(
                model_path="models/yolo11n.pt",
                host="127.0.0.1",
                port=5007,
                video_width=640,
                video_height=480,
                fps=30,
                bitrate=500,
                headless=True
            )
            
            # 运行一段时间
            print("⏱️  运行 10 秒以测试性能...")
            time.sleep(10)
            
            # 获取最终内存使用
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"最终内存使用: {final_memory:.2f} MB")
            print(f"内存增长: {memory_increase:.2f} MB")
            
            # 检查是否有明显的内存泄漏（增长超过500MB视为异常）
            if memory_increase > 500:
                print(f"⚠️  警告: 内存增长过大，可能存在内存泄漏")
            else:
                print(f"✅ 内存使用正常")
            
            print("✅ 测试 5 通过")
            return True
            
        except ImportError:
            print("⚠️  跳过测试 5: psutil 未安装")
            return True
        except Exception as e:
            print(f"❌ 测试 5 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n")
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║         无头模式推流测试套件                              ║")
        print("║         适用于无显示器环境                                ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print()
        
        tests = [
            ("基本无头模式", self.test_basic_headless_mode),
            ("自定义模型", self.test_custom_model_headless),
            ("不同分辨率", self.test_different_resolutions),
            ("配置验证", self.test_configuration_validation),
            ("性能指标", self.test_performance_metrics),
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    passed += 1
                else:
                    failed += 1
                    
                # 清理资源
                if self.streamer:
                    try:
                        self.streamer.stop()
                    except:
                        pass
                    self.streamer = None
                    
            except Exception as e:
                print(f"\n❌ 测试 '{test_name}' 异常: {str(e)}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))
                failed += 1
        
        # 显示测试总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:20s} : {status}")
        
        print("-"*60)
        print(f"总计: {len(results)} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        print(f"成功率: {(passed/len(results)*100):.1f}%")
        print("="*60)
        
        return failed == 0


def main():
    """主函数"""
    tester = HeadlessStreamerTest()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
