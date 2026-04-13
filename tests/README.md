# SQL Lint Service 测试套件

## 概述

本目录包含SQL Lint Service的完整测试套件，包括功能测试、热加载测试和API测试。

## 测试文件说明

### 1. 基础测试
- **test.py** - 基础功能测试，测试基本的lint功能
- **test_rules_functionality.py** - 规则功能测试，测试所有自定义规则的行为

### 2. 热加载测试
- **test_simple.py** - 简单热加载测试，测试规则动态加载的基本功能
- **test_hot_reload.py** - 完整热加载测试，测试热加载的完整功能，包括文件监控和自动重新加载

### 3. API测试
- **test_api.py** - API功能测试，测试所有REST API端点

### 4. 测试运行器
- **run_all_tests.py** - 运行所有测试的脚本
- **run_rule_test.py** - 按规则运行测试的脚本

## 运行测试

### 方法1: 运行所有测试
```bash
cd tests
python run_all_tests.py
```

### 方法2: 运行单个测试
```bash
cd tests

# 运行基础功能测试
python test_basic.py

# 运行规则功能测试
python test_rules_functionality.py

# 运行热加载测试
python test_simple.py
python test_hot_reload.py

# 运行API测试
python test_api.py

# 按规则运行测试
python run_rule_test.py SS01          # 运行SS01规则测试
python run_rule_test.py SS02          # 运行SS02规则测试
python run_rule_test.py --all         # 运行所有规则测试
python run_rule_test.py --list        # 列出所有可用的规则测试
```

### 方法3: 直接运行（在项目根目录）
```bash
# 运行所有测试
python tests/run_all_tests.py

# 运行单个测试
python tests/test_rules_functionality.py

# 按规则运行测试
python tests/run_rule_test.py SS01
python tests/run_rule_test.py SS02
```

## 测试要求

### 1. 环境要求
- Python 3.12+
- 已安装项目依赖 (`poetry install` 或 `pip install -r requirements.txt`)
- 对于API测试，需要服务正在运行或设置正确的BASE_URL

### 2. 服务运行
对于API测试，需要先启动服务：
```bash
cd app
python main.py
```

或者设置环境变量：
```bash
export BASE_URL=http://localhost:5000
```

## 测试内容

### 1. 规则功能测试
- **test_rule_ss01.py** - 测试SS01规则：禁止使用 `SELECT *`
- **test_rule_ss02.py** - 测试SS02规则：SQL关键字必须大写
- **test_rules_functionality.py** - 综合规则功能测试，验证规则触发的准确性
- **test_rules_integration.py** - 规则集成测试，测试多个规则的交互

### 2. 按规则测试功能
为了方便开发和维护，测试已经按照规则拆分为独立的文件：

#### 每个规则测试文件包含：
- 规则的基本功能测试
- 边界情况测试
- 详细的结果输出
- 独立的运行能力

#### 优势：
- **隔离性**：每个规则的测试独立，互不影响
- **可维护性**：修改规则时只需更新对应的测试文件
- **快速反馈**：可以快速运行单个规则的测试
- **增量测试**：新增规则时只需添加新的测试文件

#### 使用场景：
1. **开发新规则时**：只需创建对应的测试文件
2. **修改现有规则时**：只需运行该规则的测试
3. **调试规则问题时**：可以快速定位到具体规则的测试
4. **持续集成**：可以并行运行不同规则的测试

### 2. 热加载测试 (test_hot_reload.py)
- 测试文件监控功能
- 测试规则动态加载
- 测试自动重新加载
- 测试手动触发重新加载

### 3. API测试 (test_api.py)
- 测试 `/rules` 端点：获取规则列表
- 测试 `/lint` 端点：执行SQL lint
- 测试 `/rules/reload` 端点：手动重新加载规则
- 测试 `/rules/create` 端点：创建新规则文件
- 测试API性能

## 测试数据

测试会创建临时规则文件进行测试，测试完成后会自动清理。

**注意**: 测试过程中可能会在 `app/rules/` 目录下创建临时文件，测试完成后会自动删除。

## 测试输出

测试输出包括：
- 测试描述和步骤
- SQL语句和预期结果
- 实际lint结果
- 测试通过/失败状态
- 性能统计（API测试）

## 故障排除

### 1. 导入错误
如果出现导入错误，请确保在项目根目录或tests目录下运行测试。

### 2. API连接失败
如果API测试失败，请检查：
- 服务是否正在运行 (`http://localhost:5000`)
- 防火墙或网络设置
- 服务日志中的错误信息

### 3. 规则加载失败
如果规则加载失败，请检查：
- 规则文件格式是否正确
- 规则类是否有docstring
- 规则代码是否唯一

### 4. 热加载不工作
如果热加载测试失败，请检查：
- 文件权限是否足够
- 监控线程是否正常启动
- 日志中的错误信息

## 添加新测试

### 1. 添加新规则测试
要添加新规则测试，请遵循以下步骤：

1. 复制模板文件：
   ```bash
   cp test_rule_template.py test_rule_<规则代码>.py
   ```
   例如：`cp test_rule_template.py test_rule_ss03.py`

2. 修改模板中的占位符：
   - 将 `<RULE_CODE>` 替换为规则代码（如 `SS03`）
   - 将 `<规则描述>` 替换为规则描述
   - 添加测试用例和边界情况

3. 测试文件会自动被 `run_rule_test.py` 检测到，无需额外配置

### 2. 添加其他类型测试
要添加其他类型测试，请遵循以下步骤：

1. 在 `tests/` 目录下创建新的测试文件
2. 使用现有的测试文件作为模板
3. 在 `run_all_tests.py` 中添加测试配置
4. 确保测试完成后清理临时文件

## 测试覆盖率

当前测试覆盖：
- [x] 基础lint功能
- [x] 自定义规则功能
- [x] 热加载功能
- [x] REST API功能
- [x] 性能测试

## 持续集成

建议在CI/CD流水线中包含这些测试：
```yaml
# GitHub Actions示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run tests
        run: |
          cd tests
          python run_all_tests.py
```