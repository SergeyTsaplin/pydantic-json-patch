from copy import deepcopy
from importlib.resources import path
from statistics import mode
from typing import Any, TypeVar, Union

from pydantic import BaseModel, Field, validate_model

from . import models

T = TypeVar("T", bound=BaseModel)


class TestFailed(Exception):
    ...


def try_apply_for_model(model, patch, from_value):
    if patch.op == "add":
        if "__root__" in model.__fields__:
            value = model.__class__(__root__=patch.value)
        else:
            value = model.__class__(**patch.value)
        return value
    elif patch.op == "remove":
        return model
    elif patch.op == "replace":
        if "__root__" in model.__fields__:
            value = model.__class__(__root__=patch.value)
        else:
            value = model.__class__(**patch.value)
        return value
    elif patch.op in ("copy", "move"):
        if "__root__" in model.__fields__:
            value = model.__class__(__root__=from_value)
        else:
            value = model.__class__(**from_value)
        return value
    elif patch.op == "test":
        if "__root__" in model.__fields__:
            value = model.__class__(__root__=patch.value)
        else:
            value = model.__class__(**patch.value)
        if value != model:
            raise TestFailed


def try_apply(target, target_field, patch, p: str, from_value: Any):
    if p.isdecimal():
        if isinstance(target, BaseModel) and isinstance(target.__root__, list):
            target = target.__root__
        if isinstance(target, list):
            index = int(p)
            try:
                if patch.op == "add":
                    value = patch.value
                    if target_field.sub_fields:
                        value, error = target_field.sub_fields[0].validate(
                            value, {}, loc=f"{target_field.alias}/{index}"
                        )
                        if error:
                            raise ValueError("Value is invalid")
                    target.insert(index, value)
                elif patch.op == "remove":
                    target.pop(index)
                elif patch.op == "replace":
                    value = target_field.type_.validate(patch.value)
                    target[index] = value
                elif patch.op in ("copy", "move"):
                    value = target_field.type_.validate(from_value)
                    target.insert(index, value)
                elif patch.op == "test":
                    value = target_field.type_.validate(patch.value)
                    if value != target[index]:
                        raise TestFailed(f"Value does not match to {from_value}")
                return
            except IndexError as exc:
                raise ValueError(f"Index {index} is out of range") from exc
    if not hasattr(target, "__fields__"):
        raise ValueError(f"{target} has no attribute {p}")

    # RFC6901
    p = p.replace("~1", "/").replace("~0", "~")
    field_ = None
    target_attr = None
    for name, field in target.__fields__.items():
        if field.alias == p:
            field_ = field
            target_attr = name
    if patch.op == "add":
        value, errors = field_.validate(patch.value, target.dict(), loc=p)
        if errors:
            raise ValueError(f"Value is invalid for {patch.path}")
        setattr(target, target_attr, value)
    elif patch.op == "remove":
        if not field_.allow_none:
            raise ValueError(f"{patch.path} is not nullable")
        setattr(target, target_attr, None)
    elif patch.op == "replace":
        if p == "":
            value = target.validate(patch.value)
            target = value
        else:
            value, errors = field_.validate(patch.value, target.dict(), loc=p)
            if errors:
                raise ValueError(f"Value is invalid for {patch.path}")
            setattr(target, target_attr, value)
    elif patch.op in ("copy", "move"):
        value, errors = field_.validate(from_value, target.dict(), loc=p)
        if errors:
            raise ValueError(f"Value is invalid for {patch.path}")
        setattr(target, target_attr, value)
    elif patch.op == ("test"):
        value, errors = field_.validate(patch.value, target.dict(), loc=p)
        if errors:
            raise ValueError(f"Value is invalid for {patch.path}")
        if getattr(target, target_attr) != value:
            raise TestFailed(f"Value does not match to {from_value}")
    return target


def get_last(
    path: models.JsonPointer, model: T
) -> tuple[Any, Union[Field, BaseModel], models.JsonPointer]:
    parts = path.split("/")
    parts_count = len(parts) - 1
    target_field = None
    target = model
    for i, p in enumerate(parts):
        is_last = i == parts_count
        if is_last:
            if target_field is None and "__root__" in target.__fields__:
                target_field = target.__fields__["__root__"]
            return target, target_field, p
        if p == "":
            continue
        if p.isdecimal():
            if isinstance(target, list):
                index = int(p)
                try:
                    target = target[index]
                    continue
                except IndexError as exc:
                    raise ValueError(f"Index {index} is out of range") from exc

        if not hasattr(target, "__fields__"):
            raise ValueError(f"Object {target} has no attribute __fields__")
        # RFC6901
        p = p.replace("~1", "/").replace("~0", "~")
        fields = target.__fields__
        target_attr = None
        for attr_name, field in fields.items():
            if field.alias == p:
                target_field = field
                target_attr = attr_name
                break
        if target_attr is None:
            raise ValueError(f"{target} has no attribute {p}")
        target = getattr(target, p)
    return model


def apply_single_patch(patch: models.JsonPatchElement, model: T) -> T:
    """Applies single patch item to the model"""
    path = patch.path
    op = patch.op
    value_to_apply = None
    if op in (
        models.JsonPatchOperation.COPY.value,
        models.JsonPatchOperation.MOVE.value,
    ):
        from_value, from_field, last_path = get_last(patch.from_path, model)
        if last_path.isdecimal() and isinstance(from_value, list):
            index = int(last_path)
            try:
                if patch.op == models.JsonPatchOperation.COPY.value:
                    value_to_apply = deepcopy(from_value[index])
                elif patch.op == models.JsonPatchOperation.MOVE.value:
                    value_to_apply = from_value.pop(index)
            except IndexError as exc:
                raise ValueError(f"Index {index} is out of range") from exc
        else:
            if not hasattr(from_value, "__fields__"):
                raise ValueError(f"{from_value} has no attribute {last_path}")

            # RFC6901
            last_path = last_path.replace("~1", "/").replace("~0", "~")
            field_ = None
            target_attr = None
            for name, field in from_value.__fields__.items():
                if field.alias == last_path:
                    field_ = field
                    target_attr = name
                    break
            if target_attr is None:
                raise ValueError(f"{from_value} has no attribute {last_path}")
            value_to_apply = deepcopy(getattr(from_value, target_attr))
            if patch.op == "move":
                if not field_.allow_none:
                    raise ValueError(f"{patch.path} is not nullable")
                setattr(from_value, target_attr, None)
    # We don't need to look for a field, just work with the whole model
    if patch.path == "":
        return try_apply_for_model(model, patch, value_to_apply)

    target, target_field, p = get_last(patch.path, model)

    try_apply(target, target_field, patch, p, value_to_apply)
    return model


def apply_patch(patch: models.JsonPatch, model: T) -> T:
    for element in patch.__root__:
        model = apply_single_patch(element.__root__, model)
    return model
