#!/usr/bin/env python3
# coding=utf-8
"""
运行所有测试
"""

import sys
import os
import subprocess
import time

def run_test(test_file, description):
    """运行单个测试"""
    print(f"\n{'=' * 60}")
    print(f"运行测试: {description}")
    print(f"测试文件: {test_file}")
    print('=' * 60)
    
    start_time = time.time()
    
    try:
        # 运行测试
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        elapsed_time = time.time() - start_time
        
        # 打印输出
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        print(f"\n测试完成，耗时: {elapsed_time:.2f} 秒")
        
        if result.returncode == 0:
            print("[PASS] 测试通过")
            return True
        else:
            print(f"[FAIL] 测试失败 (返回码: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[FAIL] 测试超时 (60秒)")
        return False
    except Exception as e:
        print(f"[FAIL] 测试异常: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("SQL Lint Service 测试套件")
    print("=" * 60)
    
    # 测试文件列表
    tests = [
        {
            "file": "test_basic.py",
            "description": "基础功能测试"
        },
        {
            "file": "test_rule_ss01.py",
            "description": "SS01规则测试（禁止SELECT *）"
        },
        {
            "file": "test_rule_ss02.py",
            "description": "SS02规则测试（SQL关键字必须大写）"
        },
        {
            "file": "test_rules_integration.py",
            "description": "规则集成测试"
        },
        {
            "file": "test_rules_functionality.py",
            "description": "规则功能测试（综合）"
        },
        {
            "file": "test_simple.py",
            "description": "简单热加载测试"
        },
        {
            "file": "test_hot_reload.py",
            "description": "完整热加载测试"
        }
        # 注意：test_api.py 需要服务正在运行，已从默认测试中移除
        # 如果需要测试API，请单独运行：python test_api.py
    ]
    
    # 检查测试文件是否存在
    available_tests = []
    for test in tests:
        test_path = os.path.join(os.path.dirname(__file__), test["file"])
        if os.path.exists(test_path):
            available_tests.append(test)
        else:
            print(f"警告: 测试文件 {test['file']} 不存在")
    
    if not available_tests:
        print("错误: 没有可用的测试文件")
        return 1
    
    print(f"\n找到 {len(available_tests)} 个测试文件:")
    for test in available_tests:
        print(f"  - {test['file']}: {test['description']}")
    
    # 运行测试
    print("\n开始运行测试...")
    results = []
    
    for test in available_tests:
        test_path = os.path.join(os.path.dirname(__file__), test["file"])
        success = run_test(test_path, test["description"])
        results.append({
            "test": test["description"],
            "file": test["file"],
            "success": success
        })
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for result in results:
        status = "PASS" if result["success"] else "FAIL"
        print(f"{status}: {result['test']} ({result['file']})")
        
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    # 返回退出码
    if failed > 0:
        print("\n[FAIL] 有测试失败")
        return 1
    else:
        print("\n[PASS] 所有测试通过")
        return 0

if __name__ == "__main__":
    sys.exit(main())