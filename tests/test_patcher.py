from typing import Optional, Union

import pytest
from pydantic import BaseModel

from pydantic_json_patch import models
from pydantic_json_patch.patcher import TestFailed, apply_single_patch


class Confectionary(BaseModel):
    name: str


class Confectioneries(BaseModel):
    biscuits: Optional[list[Confectionary]]
    cookies: list[Confectionary]
    best_biscuit: Optional[Confectionary]
    another_field: Optional[list[Union[int, float]]]


@pytest.fixture
def confectioneries():
    yield Confectioneries(
        biscuits=[
            Confectionary(name="Choco Leibniz"),
            Confectionary(name="Another biscuit"),
        ],
        cookies=[],
        best_biscuit=None,
    )


def test_add_to_list(confectioneries):
    patch = models.JsonPatchAdd(
        op="add", path="/biscuits/1", value={"name": "Ginger Nut"}
    )
    result = apply_single_patch(patch, model=confectioneries)
    print(result)
    assert result == Confectioneries(
        biscuits=[
            Confectionary(name="Choco Leibniz"),
            Confectionary(name="Ginger Nut"),
            Confectionary(name="Another biscuit"),
        ],
        cookies=[],
        best_biscuit=None,
    )


def test_remove_field(confectioneries):
    patch = models.JsonPatchRemove(op="remove", path="/biscuits")
    result = apply_single_patch(patch, model=confectioneries)
    assert result == Confectioneries(
        biscuits=None,
        cookies=[],
        best_biscuit=None,
    )


def test_remove_from_list(confectioneries):
    patch = models.JsonPatchRemove(op="remove", path="/biscuits/0")
    result = apply_single_patch(patch, model=confectioneries)
    assert result == Confectioneries(
        biscuits=[
            Confectionary(name="Another biscuit"),
        ],
        cookies=[],
        best_biscuit=None,
    )


def test_replace_field_in_list(confectioneries):
    patch = models.JsonPatchReplace(
        op="replace", path="/biscuits/0/name", value="Chocolate Digestive"
    )
    result = apply_single_patch(patch, model=confectioneries)
    assert result == Confectioneries(
        biscuits=[
            Confectionary(name="Chocolate Digestive"),
            Confectionary(name="Another biscuit"),
        ],
        cookies=[],
        best_biscuit=None,
    )


def test_add_to_list_primitive_type():
    confectioneries = Confectioneries(
        biscuits=None, cookies=[], best_biscuit=None, another_field=[1, 2]
    )
    patch = models.JsonPatchAdd(op="add", path="/another_field/1", value="3")
    result = apply_single_patch(patch, model=confectioneries)
    assert result == Confectioneries(
        biscuits=None, cookies=[], best_biscuit=None, another_field=[1, 3, 2]
    )


def test_test_list_item(confectioneries):
    patch = models.JsonPatchTest(
        op="test", path="/biscuits/0", value={"name": "Choco Leibniz"}
    )
    result = apply_single_patch(patch, model=confectioneries)
    assert result == confectioneries

    patch = models.JsonPatchTest(
        op="test", path="/biscuits/1", value={"name": "Choco Leibniz"}
    )
    with pytest.raises(TestFailed):
        apply_single_patch(patch, model=confectioneries)


def test_test_field(confectioneries):
    patch = models.JsonPatchTest(
        op="test", path="/biscuits/1/name", value="Another biscuit"
    )
    result = apply_single_patch(patch, model=confectioneries)
    assert result == confectioneries


def test_copy_from_list_to_field(confectioneries):
    patch = models.JsonPatchCopy(
        op="copy", from_path="/biscuits/0", path="/best_biscuit"
    )
    expected_result = confectioneries.copy(deep=True)
    expected_result.best_biscuit = Confectionary(name="Choco Leibniz")
    result = apply_single_patch(patch, model=confectioneries)
    assert expected_result == result


def test_copy_field_to_field(confectioneries):
    patch = models.JsonPatchCopy(op="copy", from_path="/biscuits", path="/cookies")
    expected_result = confectioneries.copy(deep=True)
    expected_result.cookies = [
        Confectionary(name="Choco Leibniz"),
        Confectionary(name="Another biscuit"),
    ]
    result = apply_single_patch(patch, model=confectioneries)
    assert expected_result == result


def test_move_from_list_to_list(confectioneries):
    patch = models.JsonPatchMove(op="move", from_path="/biscuits/0", path="/cookies/0")
    expected_result = Confectioneries(
        biscuits=[
            Confectionary(name="Another biscuit"),
        ],
        cookies=[
            Confectionary(name="Choco Leibniz"),
        ],
    )
    result = apply_single_patch(patch, model=confectioneries)
    assert expected_result == result


def test_move_from_list_to_field(confectioneries):
    patch = models.JsonPatchMove(
        op="move", from_path="/biscuits/0", path="/best_biscuit"
    )
    expected_result = Confectioneries(
        biscuits=[
            Confectionary(name="Another biscuit"),
        ],
        cookies=[],
        best_biscuit=Confectionary(name="Choco Leibniz"),
    )
    result = apply_single_patch(patch, model=confectioneries)
    assert expected_result == result


def test_move_from_field_to_field(confectioneries):
    patch = models.JsonPatchMove(op="move", from_path="/biscuits", path="/cookies")
    expected_result = Confectioneries(
        biscuits=None,
        cookies=[
            Confectionary(name="Choco Leibniz"),
            Confectionary(name="Another biscuit"),
        ],
    )
    result = apply_single_patch(patch, model=confectioneries)
    assert expected_result == result


def test_replace_full_model(confectioneries):
    patch = models.JsonPatchReplace(
        op="replace", path="", value={"biscuits": None, "cookies": [{"name": "Cookie"}]}
    )
    expected_result = Confectioneries(
        biscuits=None, cookies=[Confectionary(name="Cookie")]
    )
    result = apply_single_patch(patch, model=confectioneries)
    assert expected_result == result
