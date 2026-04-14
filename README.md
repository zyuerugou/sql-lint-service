# SQL Lint Service

一个基于SQLFluff的SQL语法检查和规则验证服务，支持自定义规则和热加载功能。

## 功能特性

### 核心功能
- SQL语法检查和格式化
- 自定义linting规则
- REST API接口
- **多语句SQL支持**：支持分号分隔的多个SQL语句一次性检查
- **SET语句过滤**：自动过滤Hive SET配置语句，避免规则误判

### 高级功能
- **规则热加载**：无需重启服务即可动态添加、修改、删除规则
- **文件监控**：使用watchdog自动检测规则文件变化并重新加载
- **线程安全**：确保lint操作和重新加载操作的安全性
- **完整API**：提供规则管理和lint操作的完整REST API
- **代码组织优化**：模块化设计，服务类与事件处理器分离

## 快速开始

### 1. 安装依赖
```bash
# 使用poetry（推荐）
poetry install

# 或使用pip
pip install -r requirements.txt
```

### 2. 启动服务
```bash
python -m app.main
```

服务将在 `http://localhost:5000` 启动。

### 3. 基本使用
```bash
# 检查SQL语法
curl -X POST http://localhost:5000/lint \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users"}'
```

## 项目结构

```
sql-lint-service/
├── app/                          # 应用代码
│   ├── main.py                   # FastAPI应用入口
│   ├── services/
│   │   ├── lint_service.py       # Lint服务核心逻辑
│   │   └── event_handlers.py     # 文件监控事件处理器
│   └── rules/                    # 自定义规则目录
│       ├── __init__.py           # 规则插件入口
│       ├── rule_ss01.py          # 规则1：禁止SELECT *
│       ├── rule_ss02.py          # 规则2：SQL关键字必须大写
│       └── rule_ss03.py          # 规则3：标识符必须小写
├── tests/                        # 测试套件
│   ├── run_all_tests.py          # 测试运行器
│   ├── test_set_statements.py    # SET语句过滤测试
│   ├── test_multiple_statements.py # 多语句SQL测试
│   ├── test_rules_integration.py # 规则集成测试
│   ├── test_rules_functionality.py # 规则功能测试
│   ├── test_simple.py            # 简单热加载测试
│   ├── test_hot_reload.py        # 完整热加载测试
│   ├── test_api.py               # API功能测试
│   └── README.md                 # 测试文档
├── pyproject.toml                # 项目配置
├── poetry.lock                   # 依赖锁文件
├── HOT_RELOAD_README.md          # 热加载详细文档
└── README.md                     # 本文档
```

## API文档

### 基础端点

#### 1. SQL Lint检查
```
POST /lint
```

请求体：
```json
{
  "sql": "SELECT * FROM users"
}
```

响应示例：
```json
{
  "status": "success",
  "result": [
    {
      "rule_id": "SS01",
      "message": "禁止使用 SELECT *，请明确列出所有字段。",
      "severity": "False",
      "line": 1,
      "column": 8
    }
  ]
}
```

#### 2. 获取规则列表
```
GET /rules
```

响应示例：
```json
{
  "status": "success",
  "rules": ["SS01", "SS02"],
  "hot_reload_enabled": true
}
```

### 规则管理端点

#### 3. 手动重新加载规则
```
POST /rules/reload
```

响应示例：
```json
{
  "status": "success",
  "message": "规则重新加载成功"
}
```

#### 4. 健康检查
```
GET /health
```

响应示例：
```json
{
  "status": "healthy",
  "service": "sql-lint-service",
  "rules_loaded": 3,
  "hot_reload_enabled": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

#### 5. 监控状态
```
GET /monitor/status
```

响应示例：
```json
{
  "status": "success",
  "monitor": {
    "hot_reload_enabled": true,
    "watchdog_available": true,
    "rules_dir": "/path/to/rules",
    "debounce_seconds": 0.5
  }
}
```

## 热加载功能

### 启用/禁用热加载
```bash
# 启用（默认）
export ENABLE_HOT_RELOAD=true

# 禁用
export ENABLE_HOT_RELOAD=false
```

或在代码中：
```python
from app.services.lint_service import LintService

# 启用热加载
service = LintService(enable_hot_reload=True)

# 禁用热加载
service = LintService(enable_hot_reload=False)
```

### 热加载特性
- **自动监控**：监控 `app/rules/` 目录的文件变化
- **自动重载**：检测到变化后自动重新加载规则
- **手动触发**：支持API手动触发重新加载
- **错误恢复**：重新加载失败不影响服务运行

## 自定义规则开发

### 规则文件格式
```python
from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

class Rule_SS01(BaseRule):
    """禁止使用 SELECT *。"""
    
    groups = ("all", "customer")  # 必须包含"customer"规则组
    code = "SS01"  # 规则代码，必须唯一
    description = "禁止使用 SELECT *，请明确列出所有字段。"
    crawl_behaviour = SegmentSeekerCrawler({"select_clause"})
    config_keywords = []
    
    def _eval(self, context: RuleContext):
        """规则检查逻辑"""
        segment = context.segment
        
        if segment.is_type("select_clause"):
            for child in segment.raw_segments:
                if hasattr(child, 'raw') and child.raw == '*':
                    return LintResult(
                        anchor=child,
                        description=self.description
                    )
        return None
```

### 规则开发指南
1. **类名规范**：`Rule_` + 规则代码（如 `Rule_SS01`）
2. **代码唯一**：不同规则的 `code` 属性不能重复
3. **必须有docstring**：类必须有文档字符串
4. **文件命名**：`rule_` + 规则代码小写 + `.py`（如 `rule_ss01.py`）
5. **规则组**：必须包含 `"customer"` 规则组（如 `groups = ("all", "customer")`）

## 测试

### 运行所有测试
```bash
cd tests
python run_all_tests.py
```

### 测试套件说明
- **基础测试**：测试基本lint功能
- **规则测试**：测试所有自定义规则的行为
- **热加载测试**：测试规则动态加载功能
- **API测试**：测试所有REST API端点
- **SET语句测试**：验证SET配置语句过滤功能
- **多语句测试**：验证多个SQL语句一次性检查功能
- **规则集成测试**：验证规则优先级和集成功能

详细测试文档见 [tests/README.md](tests/README.md)

## 新特性说明

### 1. SET语句自动过滤
服务会自动过滤Hive SET配置语句（如 `set hive.exec.dynamic.partition=true;`），这些语句：
- 不会触发SS02（关键字大写）规则
- 不会触发SS03（标识符小写）规则  
- 被替换为空行以保持原始行号
- 避免SQLFluff解析错误

### 2. 多语句SQL支持
支持一次性检查多个分号分隔的SQL语句：
```sql
SELECT * FROM users;
INSERT INTO logs VALUES (1, 'test');
UPDATE config SET value = 'new' WHERE id = 1;
```

### 3. 代码架构优化
- **模块分离**：将`RuleFileEventHandler`和`PollingFileMonitor`类拆分到`event_handlers.py`
- **简化配置**：移除从pyproject.toml读取配置的逻辑，使用硬编码最小配置
- **类型安全**：修复PyCharm/Idea类型检查问题，简化导入逻辑

### 4. 监控优化
- **移除轮询模式**：只使用watchdog进行文件监控（必需依赖）
- **错误处理**：增强事件处理器中的路径类型转换
- **性能优化**：简化配置初始化过程

## 内置规则

所有自定义规则都属于 `customer` 规则组，服务默认只启用此规则组，关闭了所有SQLFluff默认规则。

### SS01：禁止使用 SELECT *
- **规则组**：`customer`
- **描述**：禁止使用 `SELECT *`，要求明确列出所有字段
- **触发条件**：SQL语句中包含 `*`
- **修复建议**：明确列出需要的字段名

### SS02：SQL关键字必须大写
- **规则组**：`customer`
- **描述**：SQL关键字必须使用大写形式
- **触发条件**：SQL关键字不是全大写（如 `select`, `from`, `where`）
- **修复建议**：使用大写关键字（如 `SELECT`, `FROM`, `WHERE`）
- **特殊处理**：自动排除SET配置语句中的关键字

### SS03：标识符必须小写
- **规则组**：`customer`
- **描述**：数据库表名、列名等标识符必须使用小写形式
- **触发条件**：标识符包含大写字母
- **修复建议**：使用小写标识符
- **特殊处理**：自动排除SET配置语句中的标识符

## 配置

### 环境变量
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_HOT_RELOAD` | `true` | 是否启用热加载 |

### SQLFluff配置
服务已配置为只启用自定义规则（customer规则组），使用Hive SQL方言，关闭所有SQLFluff默认规则。

在代码中的配置（`app/services/lint_service.py`）：
```python
self.config = FluffConfig(
    overrides = {
        "dialect": "hive",    # 使用Hive SQL方言
        "rules": "customer",  # 只启用customer规则组
    }
)
```

自定义规则需要添加到 `customer` 规则组：
```python
class Rule_SS01(BaseRule):
    groups = ("all", "customer")  # 添加到customer规则组
    code = "SS01"
    description = "禁止使用 SELECT *，请明确列出所有字段。"
```

如果需要启用SQLFluff默认规则，可以修改配置：
```python
# 启用所有规则（包括SQLFluff默认规则和自定义规则）
rules = "all"

# 或启用特定规则组
rules = "customer,core"  # customer规则组 + SQLFluff核心规则
```

## 部署

### 生产环境建议
1. **禁用热加载**：生产环境建议禁用热加载
2. **使用进程管理**：使用gunicorn或uvicorn with workers
3. **配置日志**：配置适当的日志级别和输出
4. **监控**：添加健康检查端点

### Docker部署
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY . .

CMD ["poetry", "run", "python", "app/main.py"]
```

## 故障排除

### 常见问题

#### 1. 规则未加载
- 检查规则文件格式是否正确
- 检查规则类是否有docstring
- 查看服务日志获取详细错误信息

#### 2. 热加载不工作
- 检查 `ENABLE_HOT_RELOAD` 环境变量
- 检查文件权限
- 查看监控线程是否正常启动
- 确认watchdog依赖已正确安装

#### 3. API调用失败
- 检查服务是否运行
- 检查端口是否正确
- 查看请求格式是否符合要求

#### 4. SET语句被误判
- 确认SET语句格式正确（如 `set hive.exec.dynamic.partition=true;`）
- 检查预处理逻辑是否正常工作
- 查看服务日志了解过滤详情

#### 5. 多语句SQL处理异常
- 确认SQL语句以分号正确分隔
- 检查行号保持功能是否正常
- 验证每个语句的lint结果是否正确

### 日志查看
```bash
# 查看服务日志
cd app
python main.py 2>&1 | tee service.log

# 查看详细日志（调试模式）
export LOG_LEVEL=DEBUG
cd app
python main.py
```

## 使用示例

### 1. 检查包含SET语句的SQL
```sql
-- SET配置语句会被自动过滤
set hive.exec.dynamic.partition=true;
set hive.exec.dynamic.partition.mode=nonstrict;

-- 实际查询语句会被检查
SELECT user_id, user_name FROM users WHERE status = 'active';
```

### 2. 检查多个SQL语句
```sql
-- 一次性检查多个语句
CREATE TABLE users (id INT, name STRING);
INSERT INTO users VALUES (1, 'Alice');
SELECT * FROM users WHERE id = 1;
```

### 3. 混合场景
```sql
-- SET语句 + 多个查询
set tez.queue.name=default;
SELECT COUNT(*) FROM logs WHERE date = '2024-01-01';

set hive.vectorized.execution.enabled=true;
INSERT INTO results SELECT * FROM temp_table;
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

### 开发要求
- 所有新功能必须包含测试
- 遵循现有代码风格
- 更新相关文档
- 处理类型检查问题（PyCharm/Idea兼容性）

## 许可证

MIT License

## 相关链接

- [SQLFluff文档](https://docs.sqlfluff.com/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [项目Issues](https://github.com/your-repo/sql-lint-service/issues)