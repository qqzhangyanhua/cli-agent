"""
OpenAI API 连通性测试工具
用于测试 /v1/chat/completions 接口是否正常工作

运行方式: python test_demo.py
"""

import requests
import json
import time
from typing import Optional, Dict, Any


class OpenAIAPITester:
    """OpenAI API 测试器"""
    
    def __init__(self):
        self.base_url = "https://sdwfger.edu.kg"
        self.model = "gpt-4.1-mini"
        self.api_key = "sk-lCVcio0vmI5U16K1ru9gdJ7ZsszU3lsKnUurlNjhROjWLwxU"
        self.timeout = 30  # 请求超时时间（秒）
    
    def get_user_input(self) -> bool:
        """获取用户输入的配置信息（可选，如果已有默认值则跳过）"""
        print("=" * 60)
        print("🚀 OpenAI API 连通性测试工具")
        print("=" * 60)
        print()
        
        # 检查是否已有配置
        if self.base_url and self.model and self.api_key:
            print("📋 检测到预设配置，是否使用？")
            print(f"🌐 Base URL: {self.base_url}")
            print(f"🤖 Model: {self.model}")
            print(f"🔑 API Key: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else self.api_key}")
            print()
            
            use_default = input("使用预设配置？(y/n，默认y): ").strip().lower()
            if use_default in ['', 'y', 'yes', '是', '确定']:
                # 确保 base_url 格式正确
                if not self.base_url.endswith('/'):
                    self.base_url += '/'
                if not self.base_url.endswith('v1/'):
                    if self.base_url.endswith('/'):
                        self.base_url += 'v1/'
                    else:
                        self.base_url += '/v1/'
                return True
        
        try:
            # 获取 base_url
            new_base_url = input(f"请输入 API Base URL (当前: {self.base_url or 'https://api.openai.com'}): ").strip()
            if new_base_url:
                self.base_url = new_base_url
            elif not self.base_url:
                print("❌ Base URL 不能为空")
                return False
            
            # 确保 base_url 以正确格式结尾
            if not self.base_url.endswith('/'):
                self.base_url += '/'
            if not self.base_url.endswith('v1/'):
                if self.base_url.endswith('/'):
                    self.base_url += 'v1/'
                else:
                    self.base_url += '/v1/'
            
            # 获取 model
            new_model = input(f"请输入模型名称 (当前: {self.model or 'gpt-3.5-turbo'}): ").strip()
            if new_model:
                self.model = new_model
            elif not self.model:
                print("❌ 模型名称不能为空")
                return False
            
            # 获取 api_key
            current_key_display = f"{self.api_key[:10]}...{self.api_key[-4:]}" if self.api_key and len(self.api_key) > 14 else self.api_key
            new_api_key = input(f"请输入 API Key (当前: {current_key_display or '未设置'}): ").strip()
            if new_api_key:
                self.api_key = new_api_key
            elif not self.api_key:
                print("❌ API Key 不能为空")
                return False
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n👋 用户取消操作")
            return False
        except Exception as e:
            print(f"❌ 输入过程中发生错误: {e}")
            return False
    
    def display_config(self):
        """显示当前配置"""
        print("\n" + "=" * 60)
        print("📋 当前配置信息")
        print("=" * 60)
        print(f"🌐 Base URL: {self.base_url}")
        print(f"🤖 Model: {self.model}")
        print(f"🔑 API Key: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else self.api_key}")
        print(f"⏱️  Timeout: {self.timeout}秒")
        print()
    
    def test_api_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        print("🔄 开始测试API连接...")
        print()
        
        # 构建请求URL
        url = f"{self.base_url}chat/completions"
        
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! This is a connection test. Please respond with 'Connection successful!'"
                }
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        result = {
            "success": False,
            "status_code": None,
            "response_time": None,
            "error": None,
            "response_data": None,
            "url": url
        }
        
        try:
            print(f"📡 发送请求到: {url}")
            print(f"📦 请求模型: {self.model}")
            
            start_time = time.time()
            
            # 发送请求
            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # 转换为毫秒
            
            result["status_code"] = response.status_code
            result["response_time"] = response_time
            
            print(f"📊 响应状态码: {response.status_code}")
            print(f"⏱️  响应时间: {response_time}ms")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    result["response_data"] = response_data
                    result["success"] = True
                    
                    # 提取AI回复内容
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        ai_message = response_data["choices"][0].get("message", {}).get("content", "")
                        print(f"🤖 AI回复: {ai_message}")
                    
                    print("✅ API连接测试成功！")
                    
                except json.JSONDecodeError as e:
                    result["error"] = f"JSON解析错误: {e}"
                    print(f"❌ 响应JSON解析失败: {e}")
                    
            else:
                try:
                    error_data = response.json()
                    result["error"] = error_data
                    print(f"❌ API请求失败: {error_data}")
                except:
                    result["error"] = response.text
                    print(f"❌ API请求失败: {response.text}")
                    
        except requests.exceptions.Timeout:
            result["error"] = f"请求超时 (>{self.timeout}秒)"
            print(f"⏰ 请求超时 (>{self.timeout}秒)")
            
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"连接错误: {e}"
            print(f"🔌 连接错误: {e}")
            
        except requests.exceptions.RequestException as e:
            result["error"] = f"请求异常: {e}"
            print(f"❌ 请求异常: {e}")
            
        except Exception as e:
            result["error"] = f"未知错误: {e}"
            print(f"❌ 未知错误: {e}")
        
        return result
    
    def display_detailed_result(self, result: Dict[str, Any]):
        """显示详细的测试结果"""
        print("\n" + "=" * 60)
        print("📊 详细测试结果")
        print("=" * 60)
        
        print(f"🌐 请求URL: {result['url']}")
        print(f"📊 状态码: {result['status_code'] or 'N/A'}")
        print(f"⏱️  响应时间: {result['response_time'] or 'N/A'}ms")
        print(f"✅ 测试结果: {'成功' if result['success'] else '失败'}")
        
        if result['error']:
            print(f"❌ 错误信息: {result['error']}")
        
        if result['response_data']:
            print("\n📋 响应数据:")
            print(json.dumps(result['response_data'], indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 60)
    
    def run_test(self):
        """运行完整的测试流程"""
        try:
            # 获取用户输入
            if not self.get_user_input():
                return
            
            # 显示配置
            self.display_config()
            
            # 确认是否继续
            confirm = input("是否开始测试? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes', '是', '确定']:
                print("👋 测试已取消")
                return
            
            print()
            
            # 执行测试
            result = self.test_api_connection()
            
            # 显示结果
            self.display_detailed_result(result)
            
            # 询问是否重新测试
            while True:
                retry = input("\n是否重新测试? (y/n): ").strip().lower()
                if retry in ['y', 'yes', '是', '确定']:
                    print("\n" + "🔄" * 20)
                    result = self.test_api_connection()
                    self.display_detailed_result(result)
                else:
                    break
            
            print("\n👋 测试完成，感谢使用！")
            
        except KeyboardInterrupt:
            print("\n\n👋 用户中断操作")
        except Exception as e:
            print(f"\n❌ 程序运行出错: {e}")


def main():
    """主函数"""
    import sys
    
    # 检查是否有 --quick 参数，用于快速测试
    if "--quick" in sys.argv or "-q" in sys.argv:
        print("🚀 快速测试模式")
        tester = OpenAIAPITester()
        
        # 确保 base_url 格式正确
        if not tester.base_url.endswith('/'):
            tester.base_url += '/'
        if not tester.base_url.endswith('v1/'):
            if tester.base_url.endswith('/'):
                tester.base_url += 'v1/'
            else:
                tester.base_url += '/v1/'
        
        # 显示配置
        tester.display_config()
        
        # 直接执行测试
        result = tester.test_api_connection()
        tester.display_detailed_result(result)
        
        print("\n👋 快速测试完成！")
    else:
        # 正常交互模式
        tester = OpenAIAPITester()
        tester.run_test()


if __name__ == "__main__":
    main()
