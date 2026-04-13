#!/usr/bin/env python3
# coding=utf-8
"""
测试API功能
"""

import sys
import os
import time
import requests
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

def wait_for_service(url, timeout=30):
    """等待服务启动"""
    print(f"等待服务启动: {url}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url.replace("/lint", "/rules"), timeout=1)
            if response.status_code == 200:
                print("服务已启动")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(1)
    
    print("\n服务启动超时")
    return False

def test_api_basic():
    """测试基础API功能"""
    print("=" * 60)
    print("测试基础API功能")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 1. 测试/rules端点
    print("\n1. 测试 /rules 端点...")
    try:
        response = requests.get(f"{base_url}/rules", timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"响应内容: {response.text}")
    except requests.exceptions.ConnectionError:
        print("连接失败，服务可能未运行")
        return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False
    
    # 2. 测试/lint端点
    print("\n2. 测试 /lint 端点...")
    
    test_cases = [
        {
            "sql": "SELECT * FROM users",
            "description": "应该触发自定义规则"
        },
        {
            "sql": "select id, name from users",
            "description": "不应该触发自定义规则"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        try:
            response = requests.post(
                f"{base_url}/lint",
                json={"sql": test_case['sql']},
                timeout=5
            )
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"状态: {data.get('status')}")
                
                if data.get('result'):
                    print("Lint结果:")
                    for item in data['result']:
                        if item['rule_id'] in ['SS01', 'SS02']:
                            print(f"  [自定义] {item['rule_id']}: {item['message']}")
                        else:
                            print(f"  [系统] {item['rule_id']}: {item['message']}")
                else:
                    print("无lint结果")
            else:
                print(f"错误: {response.text}")
                
        except Exception as e:
            print(f"请求失败: {e}")
    
    return True

def test_api_performance():
    """测试API性能"""
    print("\n" + "=" * 60)
    print("测试API性能")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    test_sql = "SELECT id, name, email, created_at FROM users WHERE status = 'active' ORDER BY created_at DESC"
    
    print(f"测试SQL: {test_sql}")
    print("进行10次连续请求测试...")
    
    times = []
    
    for i in range(10):
        start_time = time.time()
        try:
            response = requests.post(
                f"{base_url}/lint",
                json={"sql": test_sql},
                timeout=10
            )
            end_time = time.time()
            
            if response.status_code == 200:
                elapsed = (end_time - start_time) * 1000  # 转换为毫秒
                times.append(elapsed)
                print(f"请求 {i+1}: {elapsed:.2f} ms")
            else:
                print(f"请求 {i+1}: 失败 (状态码: {response.status_code})")
        except Exception as e:
            print(f"请求 {i+1}: 异常 ({e})")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n性能统计:")
        print(f"  请求次数: {len(times)}")
        print(f"  平均时间: {avg_time:.2f} ms")
        print(f"  最短时间: {min_time:.2f} ms")
        print(f"  最长时间: {max_time:.2f} ms")
    else:
        print("\n无有效性能数据")

def cleanup():
    """清理测试文件"""
    print("\n" + "=" * 60)
    print("清理测试文件")
    print("=" * 60)
    
    test_file = os.path.join("..", "app", "rules", "rule_api_test.py")
    
    if os.path.exists(test_file):
        try:
            os.remove(test_file)
            print(f"已删除测试文件: {test_file}")
        except Exception as e:
            print(f"删除文件失败: {e}")
    else:
        print("测试文件不存在，无需清理")

if __name__ == "__main__":
    # 检查服务是否运行
    base_url = "http://localhost:5000"
    
    if not wait_for_service(base_url, timeout=10):
        print("\n注意: 服务未运行，部分测试可能失败")
        print("请先启动服务: cd app && python main.py")
        print("或设置 BASE_URL 环境变量指向运行中的服务")
    
    # 运行测试
    test_api_basic()
    test_api_performance()
    
    # 清理
    cleanup()
    
    print("\n" + "=" * 60)
    print("API测试完成")
    print("=" * 60)