# robot-capability-schema

不同机器人提供的能力不一样。这个项目让你用一个 YAML 文件告诉其他程序：这台机器人有哪些能力、参数范围是多少。

比如：这台机器人有一个云台，yaw 范围是 -90 到 90 度；有一个相机，分辨率 1280x720，30 帧。其他程序读了这个 YAML 就知道怎么和这台机器人交互。

## 安装

```bash
pip install robot-capability-schema
```

或使用开发模式安装：

```bash
pip install -e ".[dev]"
```

## 第一个 YAML

创建一个 `robot.yaml`：

```yaml
schema_version: "0.1"
robot:
  name: demo_robot
  capabilities:
    head:
      kind: pan_tilt
      description: 头部云台
      constraints:
        yaw_min: -90
        yaw_max: 90
        pitch_min: -30
        pitch_max: 60

    camera:
      kind: rgb_camera
      properties:
        - name: width
          value: 1280
          unit: px
        - name: fps
          value: 30
          unit: Hz
```

## 命令

### validate - 校验配置

```bash
robot-cap validate robot.yaml
```

合法输出：

```
校验通过: 配置合法
```

非法输出：

```
校验失败: 发现 2 个错误

  1. capabilities.head.constraints.yaw_max must be greater than yaw_min
  2. capabilities.camera.properties 包含重复属性名: fps
```

### list - 列出能力

```bash
robot-cap list robot.yaml
```

输出：

```
能力列表 (共 2 个):

  head
    kind: pan_tilt
    描述: 头部云台
    约束: yaw_min=-90, yaw_max=90, pitch_min=-30, pitch_max=60

  camera
    kind: rgb_camera
    描述: <空>
    属性: width=1280, fps=30
```

### docs - 生成 Markdown 文档

```bash
robot-cap docs robot.yaml                    # 输出到终端
robot-cap docs robot.yaml -o docs.md         # 输出到文件
```

### generate-python - 生成 Python 接口骨架

```bash
robot-cap generate-python robot.yaml                   # 输出到终端
robot-cap generate-python robot.yaml -o interfaces.py  # 输出到文件
```

生成类似代码：

```python
class RobotCapabilities(Protocol):
    """demo_robot 的能力协议。"""

    def set_head(self, yaw: float, pitch: float) -> None:
        """设置云台角度。"""
        ...

    def capture_camera(self, width: int = 1280, height: int = 720, fps: int = 30) -> bytes:
        """拍摄一张 RGB 图片。"""
        ...
```

## Schema 字段说明

### 顶层字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `schema_version` | 是 | Schema 版本号，当前支持 `"0.1"` |
| `robot` | 是 | 机器人元信息和能力定义 |

### robot 字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `name` | 是 | 机器人名称 |
| `description` | 否 | 简要描述 |
| `manufacturer` | 否 | 制造商 |
| `model` | 否 | 型号 |
| `capabilities` | 是 | 能力字典，不能为空 |

### capability 字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `kind` | 是 | 能力类型，如 `pan_tilt`、`rgb_camera`、`discrete_action` |
| `description` | 否 | 能力描述 |
| `properties` | 否 | 属性列表，每项含 `name`、`value`、`unit` |
| `constraints` | 否 | 约束条件，格式依赖 `kind` |
| `actions` | 否 | 可执行动作列表（仅 `discrete_action`） |
| `inputs` | 否 | 输入参数列表 |
| `outputs` | 否 | 输出参数列表 |
| `metadata` | 否 | 额外元信息，任意键值对 |

## 定义新的 capability kind

`kind` 可以是任意非空字符串。已知的 `kind` 有：

- `pan_tilt` - 云台，约束含 `yaw_min/max`、`pitch_min/max`
- `rgb_camera` - RGB 相机，约束含 `width_min/max`、`height_min/max`、`fps_min/max`

未知的 `kind` 不会报错，只会产生一条警告。约束校验只在已知 `kind` 时执行。

## 扩展 Validator

增加新的约束类型：

1. 在 `models.py` 中添加新的 Constraint 子类
2. 在 `validator.py` 的 `CONSTRAINT_MAP` 中注册新的 kind 映射
3. 在 `examples/` 中添加示例
4. 在 `tests/test_validator.py` 中添加测试

## 修改输出格式

- 文本输出在 `formatter.py`
- Markdown 输出在 `docs_generator.py`
- Python 代码在 `python_generator.py`

## 升级 schema_version

当需要引入不兼容变更时，递增版本号：

1. 修改 `parser.py` 中的 `SUPPORTED_VERSIONS`
2. 在 `models.py` 中适配新版本的字段
3. 更新所有示例和测试
4. 保持旧版本解析兼容（如需要）

## 开发者指南

修改代码时注意以下文件职责：

| 文件 | 职责 |
| --- | --- |
| `models.py` | 数据结构定义（Pydantic Model） |
| `parser.py` | YAML 解析和基础检查 |
| `validator.py` | 规则检查和错误收集 |
| `formatter.py` | CLI 文本输出格式化 |
| `docs_generator.py` | Markdown 文档生成 |
| `python_generator.py` | Python 接口骨架生成 |
| `cli.py` | 命令行入口和子命令 |

> 增加字段时不要只修改 parser，要同时更新 model、validator、schema example 和 tests。

## 运行测试

```bash
pytest tests/ -v
```

## 代码检查

```bash
ruff check src/ tests/
```
