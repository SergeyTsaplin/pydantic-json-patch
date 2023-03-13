import json
import os
from collections import namedtuple
from typing import Any

import pytest
from pydantic import BaseModel

from pydantic_json_patch import JsonPatch, apply_patch

TestEntity = namedtuple("TestEntity", ["doc", "patch", "expected", "comment", "error"])


class Doc(BaseModel):
    __root__: Any


def get_test_cases(file: str):
    with open(file, "r") as f:
        raw = f.read()
    tests = json.loads(raw)
    test_cases = []
    for test in tests:
        if test.get("disabled", False):
            continue
        doc = Doc(__root__=test["doc"])
        try:
            patch = JsonPatch(__root__=test["patch"])
        except Exception as ex:
            print(ex)
            continue
        raw_expected = test.get("expected")
        expected = None
        if raw_expected is not None:
            expected = Doc(__root__=raw_expected)
        comment = test.get("comment")
        error = test.get("error")
        test_cases.append(
            TestEntity(
                doc=doc, patch=patch, expected=expected, comment=comment, error=error
            )
        )
    return test_cases


MAIN_SPEC = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "specs", "test.json"
)
ADDITIONAL_SPEC = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "specs", "spec_tests.json"
)


@pytest.mark.parametrize("test_case", get_test_cases(MAIN_SPEC))
def test_main_spec(test_case: TestEntity):
    if test_case.error is not None:
        with pytest.raises(Exception) as exc:
            apply_patch(test_case.patch, test_case.doc)
    else:
        res = apply_patch(test_case.patch, test_case.doc)
        assert res == test_case.expected, test_case.comment


@pytest.mark.parametrize("test_case", get_test_cases(ADDITIONAL_SPEC))
def test_additional_spec(test_case: TestEntity):
    if test_case.error is not None:
        with pytest.raises(Exception) as exc:
            apply_patch(test_case.patch, test_case.doc)
    else:
        res = apply_patch(test_case.patch, test_case.doc)
        assert res == test_case.expected, test_case.comment
