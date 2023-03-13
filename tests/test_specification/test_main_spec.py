import json
import os
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from pydantic_json_patch import JsonPatch, apply_patch


def _parse_patch(raw_patch: str) -> JsonPatch:
    return JsonPatch.parse_raw(raw_patch)


def _apply_raw_path(raw_patch: list, doc):
    return apply_patch(JsonPatch(__root__=raw_patch), doc)


def test_empty_patch_with_empty_doc():
    class Doc(BaseModel):
        ...

    doc = Doc()
    expected = Doc()
    patch = []
    assert _apply_raw_path(patch, doc) == expected


def test_empty_patch_list():
    class Doc(BaseModel):
        foo: int

    doc = Doc(foo=1)
    expected = Doc(foo=1)
    patch = []
    assert _apply_raw_path(patch, doc) == expected


def test_add_replaces_any_existing_field():
    class Doc(BaseModel):
        foo: Optional[int]

    doc = Doc(foo=None)
    patch = [{"op": "add", "path": "/foo", "value": 1}]
    expected = Doc(foo=1)
    assert _apply_raw_path(patch, doc) == expected


def test_toplevel_array():
    class Doc(BaseModel):
        __root__: list[str]

    doc = Doc(__root__=[])
    patch = [{"op": "add", "path": "/0", "value": "foo"}]
    expected = Doc(__root__=["foo"])
    assert _apply_raw_path(patch, doc) == expected


def test_toplevel_array_no_change():
    class Doc(BaseModel):
        __root__: list[str]

    doc = Doc(__root__=["foo"])
    patch = []
    expected = Doc(__root__=["foo"])
    assert _apply_raw_path(patch, doc) == expected


def test_toplevel_object_numeric_string():
    class Doc(BaseModel):
        foo: Optional[str]

    doc = Doc()
    patch = [{"op": "add", "path": "/foo", "value": "1"}]
    expected = Doc(foo="1")
    assert _apply_raw_path(patch, doc) == expected


def test_toplevel_object_integer():
    class Doc(BaseModel):
        foo: Optional[int]

    doc = Doc()
    patch = [{"op": "add", "path": "/foo", "value": 1}]
    expected = Doc(foo=1)
    assert _apply_raw_path(patch, doc) == expected


def test_replace_object_document_with_array_document():
    class Doc(BaseModel):
        __root__: Union[dict[str, str], list[str]]

    doc = Doc(__root__={})
    patch = [{"op": "add", "path": "", "value": []}]
    expected = Doc(__root__=[])
    assert _apply_raw_path(patch, doc) == expected


def test_replace_array_document_with_object_document():
    class Doc(BaseModel):
        __root__: Any

    doc = Doc(__root__=[])
    patch = [{"op": "add", "path": "", "value": {}}]
    expected = Doc(__root__={})
    assert _apply_raw_path(patch, doc) == expected
