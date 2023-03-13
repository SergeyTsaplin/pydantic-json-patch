import json

from pydantic_json_patch import models


def test_models() -> None:
    """Test parsing positive case"""
    raw_patch = [
        {"op": "add", "path": "/biscuits/1", "value": {"name": "Ginger Nut"}},
        {"op": "remove", "path": "/biscuits"},
        {"op": "remove", "path": "/biscuits/0"},
        {"op": "replace", "path": "/biscuits/0/name", "value": "Chocolate Digestive"},
        {"op": "copy", "from": "/biscuits/0", "path": "/best_biscuit"},
        {"op": "move", "from": "/biscuits", "path": "/cookies"},
        {"op": "test", "path": "/best_biscuit/name", "value": "Choco Leibniz"},
    ]
    patch = models.JsonPatch.parse_raw(json.dumps(raw_patch))
    expected = models.JsonPatch(
        __root__=[
            models.JsonPatchAdd(
                op="add", path="/biscuits/1", value={"name": "Ginger Nut"}
            ),
            models.JsonPatchRemove(op="remove", path="/biscuits"),
            models.JsonPatchRemove(op="remove", path="/biscuits/0"),
            models.JsonPatchReplace(
                op="replace", path="/biscuits/0/name", value="Chocolate Digestive"
            ),
            models.JsonPatchCopy(
                op="copy", from_path="/biscuits/0", path="/best_biscuit"
            ),
            models.JsonPatchMove(op="move", from_path="/biscuits", path="/cookies"),
            models.JsonPatchTest(
                op="test", path="/best_biscuit/name", value="Choco Leibniz"
            ),
        ]
    )
    assert patch == expected
