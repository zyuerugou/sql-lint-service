#!/usr/bin/env python3
"""
按规则运行测试 - 支持运行单个规则的测试
"""

import sys
import os
import subprocess
import time
import argparse

def run_rule_test(rule_code):
    """运行指定规则的测试"""
    test_file = f"test_rule_{rule_code.lower()}.py"
    test_path = os.path.join(os.path.dirname(__file__), test_file)
    
    if not os.path.exists(test_path):
        print(f"错误: 找不到规则 {rule_code} 的测试文件")
        print(f"预期文件: {test_file}")
        print("\n可用的规则测试文件:")
        for file in os.listdir(os.path.dirname(__file__)):
            if file.startswith("test_rule_") and file.endswith(".py"):
                rule_name = file[10:-3].upper()
                print(f"  - {rule_name}: {file}")
        return False
    
    print(f"\n{'=' * 60}")
    print(f"运行规则测试: {rule_code}")
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
            print(f"[PASS] 规则 {rule_code} 测试通过")
            return True
        else:
            print(f"[FAIL] 规则 {rule_code} 测试失败 (返回码: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[FAIL] 规则 {rule_code} 测试超时 (60秒)")
        return False
    except Exception as e:
        print(f"[FAIL] 规则 {rule_code} 测试异常: {e}")
        return False

def list_available_rule_tests():
    """列出所有可用的规则测试"""
    print("可用的规则测试文件:")
    rule_tests = []
    
    for file in sorted(os.listdir(os.path.dirname(__file__))):
        if file.startswith("test_rule_") and file.endswith(".py") and file != "test_rule_template.py":
            rule_code = file[10:-3].upper()
            rule_tests.append((rule_code, file))
    
    if not rule_tests:
        print("  没有找到规则测试文件")
        return
    
    for rule_code, file in rule_tests:
        print(f"  - {rule_code}: {file}")
    
    return rule_tests

def run_all_rule_tests():
    """运行所有规则测试"""
    print("=" * 60)
    print("运行所有规则测试")
    print("=" * 60)
    
    rule_tests = list_available_rule_tests()
    if not rule_tests:
        return False
    
    print("\n开始运行所有规则测试...")
    results = []
    
    for rule_code, file in rule_tests:
        success = run_rule_test(rule_code)
        results.append({
            "rule": rule_code,
            "file": file,
            "success": success
        })
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("规则测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for result in results:
        status = "PASS" if result["success"] else "FAIL"
        print(f"{status}: 规则 {result['rule']} ({result['file']})")
        
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {len(results)} 个规则测试")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    return failed == 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='按规则运行SQL Lint测试')
    parser.add_argument('rule', nargs='?', help='规则代码（如SS01, SS02），不指定则列出所有规则')
    parser.add_argument('--all', action='store_true', help='运行所有规则测试')
    parser.add_argument('--list', action='store_true', help='列出所有可用的规则测试')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_rule_tests()
        return 0
    
    if args.all:
        success = run_all_rule_tests()
        return 0 if success else 1
    
    if args.rule:
        # 运行指定规则的测试
        success = run_rule_test(args.rule.upper())
        return 0 if success else 1
    else:
        # 没有指定规则，显示帮助信息
        print("SQL Lint Service 规则测试工具")
        print("=" * 60)
        print("\n使用方法:")
        print("  python run_rule_test.py SS01          # 运行SS01规则测试")
        print("  python run_rule_test.py SS02          # 运行SS02规则测试")
        print("  python run_rule_test.py --all         # 运行所有规则测试")
        print("  python run_rule_test.py --list        # 列出所有可用的规则测试")
        print("\n当前可用的规则测试:")
        list_available_rule_tests()
        return 0

if __name__ == "__main__":
    sys.exit(main())