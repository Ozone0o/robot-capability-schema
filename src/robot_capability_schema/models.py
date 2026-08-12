"""机器人能力描述模型。

使用 Pydantic BaseModel 定义数据结构，保证类型安全和清晰的校验错误。
选择 Pydantic v2 的原因：
1. 错误信息可读，自带字段路径
2. 无需额外依赖即可做类型校验
3. 比手动写 dataclass 校验更简洁
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RobotMeta(BaseModel):
    """机器人元信息。"""

    name: str = Field(..., min_length=1, description="机器人名称")
    description: str = Field("", description="机器人简要描述")
    manufacturer: str = Field("", description="制造商")
    model: str = Field("", description="型号")


class Constraint(BaseModel):
    """单一约束条件。"""

    pass


class PanTiltConstraint(Constraint):
    """云台约束。"""

    yaw_min: float = Field(-360.0, description=" yaw 最小值（度）")
    yaw_max: float = Field(360.0, description="yaw 最大值（度）")
    pitch_min: float = Field(-90.0, description="pitch 最小值（度）")
    pitch_max: float = Field(90.0, description="pitch 最大值（度）")

    def validate_range(self, errors: list[str]) -> None:
        """校验角度范围。"""
        if self.yaw_max <= self.yaw_min:
            errors.append("constraints.yaw_max must be greater than yaw_min")
        if self.pitch_max <= self.pitch_min:
            errors.append("constraints.pitch_max must be greater than pitch_min")


class CameraConstraint(Constraint):
    """相机约束。"""

    width_min: int = Field(1, description="最小宽度")
    width_max: int = Field(1920, description="最大宽度")
    height_min: int = Field(1, description="最小高度")
    height_max: int = Field(1080, description="最大高度")
    fps_min: int = Field(1, description="最小帧率")
    fps_max: int = Field(120, description="最大帧率")

    def validate_range(self, errors: list[str]) -> None:
        """校验分辨率和帧率范围。"""
        if self.width_max <= self.width_min:
            errors.append("constraints.width_max must be greater than width_min")
        if self.height_max <= self.height_min:
            errors.append("constraints.height_max must be greater than height_min")
        if self.fps_max <= self.fps_min:
            errors.append("constraints.fps_max must be greater than fps_min")


class NumericConstraint(Constraint):
    """通用数值约束。"""

    min_value: float | None = Field(None, description="最小值")
    max_value: float | None = Field(None, description="最大值")
    unit: str = Field("", description="单位")

    def validate_range(self, errors: list[str]) -> None:
        """校验数值范围。"""
        if self.min_value is not None and self.max_value is not None:
            if self.max_value <= self.min_value:
                errors.append("constraints.max_value must be greater than min_value")


class Property(BaseModel):
    """能力属性键值对。"""

    name: str = Field(..., min_length=1, description="属性名")
    value: float | int | str = Field(..., description="属性值")
    unit: str = Field("", description="单位（可选）")


class InputParam(BaseModel):
    """输入参数。"""

    name: str = Field(..., min_length=1, description="参数名")
    type: str = Field(description="参数类型，如 float、int、string")
    description: str = Field("", description="参数描述")
    required: bool = Field(True, description="是否必填")


class OutputParam(BaseModel):
    """输出参数。"""

    name: str = Field(..., min_length=1, description="参数名")
    type: str = Field(description="参数类型")
    description: str = Field("", description="参数描述")


class Capability(BaseModel):
    """单个能力定义。"""

    kind: str = Field(..., min_length=1, description="能力类型，如 pan_tilt、rgb_camera")
    description: str = Field("", description="能力描述")
    properties: list[Property] = Field(default_factory=list, description="属性列表")
    constraints: dict[str, Any] = Field(default_factory=dict, description="约束条件")
    actions: list[str] = Field(default_factory=list, description="可执行动作列表")
    inputs: list[InputParam] = Field(default_factory=list, description="输入参数")
    outputs: list[OutputParam] = Field(default_factory=list, description="输出参数")
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元信息")
