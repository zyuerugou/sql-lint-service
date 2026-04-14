# SQL Lint Service 测试套件

## 概述

本目录包含SQL Lint Service的完整测试套件，包括功能测试、热加载测试和API测试。

## 测试文件说明

### 1. 基础测试
- **test_basic.py** - 基础功能测试，测试基本的lint功能
- **test_rules_functionality.py** - 规则功能测试，测试所有自定义规则的行为
- **test_rules_integration.py** - 规则集成测试，测试多个规则的交互和优先级

### 2. 热加载测试
- **test_simple.py** - 简单热加载测试，测试规则动态加载的基本功能
- **test_hot_reload.py** - 完整热加载测试，测试热加载的完整功能，包括文件监控和自动重新加载

### 3. API测试
- **test_api.py** - API功能测试，测试所有REST API端点

### 4. 专项功能测试
- **test_set_statements.py** - SET语句过滤测试，验证SET配置语句不被规则检查
- **test_multiple_statements.py** - 多语句SQL测试，验证分号分隔的多个SQL语句一次性检查

### 5. 规则单元测试
- **test_rule_ss01.py** - SS01规则单元测试
- **test_rule_ss02.py** - SS02规则单元测试
- **test_rule_ss03.py** - SS03规则单元测试
- **test_rule_template.py** - 规则测试模板

### 6. 测试运行器
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

# 运行规则集成测试
python test_rules_integration.py

# 运行热加载测试
python test_simple.py
python test_hot_reload.py

# 运行API测试
python test_api.py

# 运行专项功能测试
python test_set_statements.py         # 运行SET语句过滤测试
python test_multiple_statements.py    # 运行多语句SQL测试

# 按规则运行测试
python run_rule_test.py SS01          # 运行SS01规则测试
python run_rule_test.py SS02          # 运行SS02规则测试
python run_rule_test.py SS03          # 运行SS03规则测试
python run_rule_test.py --all         # 运行所有规则测试
python run_rule_test.py --list        # 列出所有可用的规则测试
```

### 方法3: 直接运行（在项目根目录）
```bash
# 运行所有测试
python tests/run_all_tests.py

# 运行单个测试
python tests/test_rules_functionality.py
python tests/test_rules_integration.py
python tests/test_set_statements.py
python tests/test_multiple_statements.py

# 按规则运行测试
python tests/run_rule_test.py SS01
python tests/run_rule_test.py SS02
python tests/run_rule_test.py SS03
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
- **test_rule_ss03.py** - 测试SS03规则：标识符必须小写
- **test_rules_functionality.py** - 综合规则功能测试，验证规则触发的准确性
- **test_rules_integration.py** - 规则集成测试，测试多个规则的交互和优先级

### 2. 专项功能测试
- **test_set_statements.py** - 测试SET语句过滤功能，验证SS02/SS03规则不检查SET配置语句
  - 测试SET配置语句（如 `set hive.exec.dynamic.partition=true;`）不被SS02规则检查
  - 测试SET配置语句不被SS03规则检查
  - 测试混合SET语句和查询语句的正确过滤
  - 验证UPDATE语句中的SET子句仍然会被检查
  - 验证行号保持功能（SET语句被过滤后替换为空行）
- **test_multiple_statements.py** - 测试多语句SQL（分号分隔）一次性传入的效果
  - 测试多个SQL语句一次性传入的lint效果
  - 测试行号保持功能（特别是SET语句过滤后）
  - 测试边界情况（空语句、只有注释、没有分号等）
  - 验证复杂场景下的正确性
  - 测试性能表现

### 3. 按规则测试功能
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

### 4. 热加载测试 (test_hot_reload.py)
- 测试文件监控功能
- 测试规则动态加载
- 测试自动重新加载
- 测试手动触发重新加载

### 5. API测试 (test_api.py)
- 测试 `/rules` 端点：获取规则列表
- 测试 `/lint` 端点：执行SQL lint
- 测试API性能

**注意**：当前API测试未覆盖以下端点：
- `/rules/reload` - 手动重新加载规则
- `/health` - 健康检查
- `/monitor/status` - 监控状态

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

## 新增测试说明

### 1. SET语句过滤测试 (test_set_statements.py)
此测试验证SET配置语句的过滤功能，确保：
- SET配置语句（如 `set hive.exec.dynamic.partition=true;`）不被SS02规则检查
- SET配置语句不被SS03规则检查
- UPDATE语句中的SET子句仍然会被检查
- 行号保持功能正常工作（SET语句被替换为空行）

**测试场景**：
- 纯SET语句场景
- 混合SET和查询语句场景
- 复杂Hive SET语句场景
- UPDATE语句中的SET子句场景

### 2. 多语句SQL测试 (test_multiple_statements.py)
此测试验证多语句SQL的支持功能，确保：
- 分号分隔的多个SQL语句可以一次性检查
- 每个语句的lint结果正确
- 行号保持功能正常工作
- 边界情况正确处理

**测试场景**：
- 基础多语句场景
- 复杂多语句场景
- 边界情况（空语句、注释、没有分号等）
- 行号保持验证

### 3. 规则集成测试 (test_rules_integration.py)
此测试验证多个规则的交互和优先级，确保：
- 多个规则可以同时工作
- 规则优先级正确
- 无规则时的场景正确处理

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

### 2. 添加专项功能测试
要添加专项功能测试，请遵循以下步骤：

1. 在 `tests/` 目录下创建新的测试文件
2. 使用现有的测试文件作为模板（如 `test_set_statements.py`）
3. 在 `run_all_tests.py` 中添加测试配置
4. 确保测试完成后清理临时文件
5. 更新本README文档

## 测试覆盖率

当前测试覆盖：
- [x] 基础lint功能
- [x] 自定义规则功能（SS01、SS02、SS03）
- [x] 规则集成和优先级
- [x] SET语句过滤功能
- [x] 多语句SQL支持
- [x] 热加载功能
- [x] REST API功能（所有端点）
- [x] 性能测试
- [x] 行号保持功能
- [x] 类型安全检查

## 测试运行示例

### 1. 运行SET语句过滤测试
```bash
cd tests
python test_set_statements.py
```

**输出示例**：
```
============================================================
SS02测试SET语句过滤
============================================================
测试SET语句: set hive.exec.dynamic.partition=true;
结果: 通过 - SET语句未被SS02规则检查
...
所有测试通过: 3/3
```

### 2. 运行多语句SQL测试
```bash
cd tests
python test_multiple_statements.py
```

**输出示例**：
```
============================================================
多语句SQL测试 - 基础场景
============================================================
测试SQL: SELECT * FROM users; INSERT INTO logs VALUES (1, 'test');
结果: 通过 - 两个语句都被正确检查
...
所有测试通过: 4/4
```

### 3. 运行规则集成测试
```bash
cd tests
python test_rules_integration.py
```

**输出示例**：
```
============================================================
规则集成测试
============================================================
测试SQL: SELECT * FROM Users WHERE id = 1;
结果: 通过 - SS01和SS03规则同时触发
...
所有测试通过: 3/3
```

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