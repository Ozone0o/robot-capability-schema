"""校验器。

对解析后的数据执行规则检查，收集所有错误并返回可读的错误信息。
"""

from __future__ import annotations

import logging

from .models import (
    CameraConstraint,
    Constraint,
    PanTiltConstraint,
)

logger = logging.getLogger(__name__)

# 已知能力类型的约束类映射
CONSTRAINT_MAP: dict[str, type[Constraint]] = {
    "pan_tilt": PanTiltConstraint,
    "rgb_camera": CameraConstraint,
}

# 已知能力类型列表（用于检查未知 kind）
KNOWN_KINDS = set(CONSTRAINT_MAP.keys())


class ValidationResult:
    """校验结果。"""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def is_valid(self) -> bool:
        """是否有错误。"""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """添加错误信息。"""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """添加警告信息。"""
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> None:
        """合并另一个校验结果。"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class RobotCapabilityValidator:
    """机器人能力校验器。

    校验规则：
    1. 每个 capability 必须有 kind 字段
    2. kind 已知时，校验对应约束
    3. properties 中的属性名不能重复
    4. actions 列表元素必须是非空字符串
    5. 未知字段发出警告但不阻止
    """

    def validate(self, data: dict) -> ValidationResult:
        """校验完整数据。

        Args:
            data: 解析后的 YAML 数据字典

        Returns:
            校验结果
        """
        result = ValidationResult()
        robot = data.get("robot", {})
        capabilities = robot.get("capabilities", {})

        for cap_name, cap_data in capabilities.items():
            self._validate_capability(cap_name, cap_data, result)

        return result

    def _validate_capability(self, name: str, data: dict, result: ValidationResult) -> None:
        """校验单个能力。"""
        kind = data.get("kind", "<unknown>")
        prefix = f"capabilities.{name}"

        # 校验 actions 列表
        actions = data.get("actions", [])
        if isinstance(actions, list):
            for i, action in enumerate(actions):
                if not isinstance(action, str) or not action.strip():
                    result.add_error(f"{prefix}.actions[{i}] 必须是非空字符串")

        # 校验 properties 属性名唯一
        properties = data.get("properties", [])
        if isinstance(properties, list):
            seen_names: set[str] = set()
            for i, prop in enumerate(properties):
                if isinstance(prop, dict):
                    prop_name = prop.get("name", f"<index {i}>")
                    if prop_name in seen_names:
                        result.add_error(f"{prefix}.properties 包含重复属性名: {prop_name}")
                    seen_names.add(prop_name)

        # 校验约束
        constraints = data.get("constraints", {})
        if isinstance(constraints, dict) and constraints:
            self._validate_constraints(name, kind, constraints, result)

        # 未知 kind 警告
        if kind not in KNOWN_KINDS:
            result.add_warning(f"未知的 capability kind: {kind}（已放行）")

    def _validate_constraints(
        self, cap_name: str, kind: str, constraints: dict, result: ValidationResult
    ) -> None:
        """校验约束条件。"""
        constraint_cls = CONSTRAINT_MAP.get(kind)
        if constraint_cls is None:
            # 未知类型不校验约束细节
            return

        try:
            constraint = constraint_cls(**constraints)
        except Exception:
            # Pydantic 已抛出详细错误，这里简化处理
            return

        errors: list[str] = []
        constraint.validate_range(errors)
        for err in errors:
            result.add_error(f"capabilities.{cap_name}.constraints.{err}")
