# JsonPatch implementation for Pydantic


## TODO:

* [ ] Make the issue in the pydantic repo about empty string as a json key
* [ ] Check how it works with `__root__`-models
* [ ] Check how it works with path = "" or path = "/"
* [ ] Check how it works with discriminated unions
* [x] Implement "test", "copy" and "move" operations
* [ ] Rework exceptions
* [ ] Test negative scenarios
* [ ] Tests with `~` and `/` in the keys
