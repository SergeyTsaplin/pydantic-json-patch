"""The module contains the basic models for parsing JsonPatch specification."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Generator, Literal, Union

from pydantic import BaseModel, Field, fields


class JsonPatchOperation(Enum):
    """Json Patch available operations"""

    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    COPY = "copy"
    MOVE = "move"
    TEST = "test"


class JsonPointer(str):
    """Field type for Json Pointer (RFC6901)
    https://datatracker.ietf.org/doc/html/rfc6901/
    """

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], Any], None, None]:
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(
            # some example postcodes
            examples=["/", "/foo/0", "/bar/baz"],
        )

    @classmethod
    def validate(cls, value: Any) -> JsonPointer:
        """Validates the Json pointer"""
        if not isinstance(value, str):
            raise TypeError("string required")
        if not (value.startswith("/") or value == ""):
            raise ValueError("invalid JSON pointer")
        return cls(value)

    def __repr__(self) -> str:
        return f"JsonPointer({super().__repr__()})"


class BaseJsonPatchElement(BaseModel):
    op: Literal["add", "remove", "replace", "copy", "move", "test"]
    path: JsonPointer


class JsonPatchAdd(BaseJsonPatchElement):
    """Model for JsonPatch's add operation element"""

    op: Literal["add"]
    value: Any


class JsonPatchRemove(BaseJsonPatchElement):
    """Model for JsonPatch's remove operation element"""

    op: Literal["remove"]


class JsonPatchReplace(BaseJsonPatchElement):
    """Model for JsonPatch's replace operation element"""

    op: Literal["replace"]
    value: Any


class JsonPatchCopy(BaseJsonPatchElement):
    """Model for JsonPatch's copy operation element"""

    op: Literal["copy"]
    from_path: JsonPointer = Field(alias="from")

    class Config:
        """Custom model config"""

        allow_population_by_field_name = True


class JsonPatchMove(BaseJsonPatchElement):
    """Model for JsonPatch's move operation element"""

    op: Literal["move"]
    from_path: JsonPointer = Field(alias="from")

    class Config:
        """Custom model config"""

        allow_population_by_field_name = True


class JsonPatchTest(BaseJsonPatchElement):
    """Model for JsonPatch's test operation element"""

    op: Literal["test"]
    value: Any


class JsonPatchElement(BaseModel):
    """Model for a JsonPatch single item"""

    __root__: Union[
        JsonPatchAdd,
        JsonPatchRemove,
        JsonPatchReplace,
        JsonPatchCopy,
        JsonPatchMove,
        JsonPatchTest,
    ] = Field(discriminator="op")


class JsonPatch(BaseModel):
    """Model for a list of JsonPatch items"""

    __root__: list[JsonPatchElement]
