from dataclasses import fields
from typing import Any, TypeVar

T = TypeVar("T")


def has_contract_been_implemented(instance: T, cls: type) -> bool:
    instance_methods = {item for item in set(dir(instance)) if not item.startswith("__")}
    cls_methods = {item for item in set(dir(cls)) if not item.startswith("__")}

    return cls_methods.issubset(instance_methods)


def has_dict_contract_been_implemented(raw_data: dict[str, Any], cls: type) -> bool:
    cls_keys = {field.name for field in fields(cls)}
    dict_keys = set(raw_data.keys())

    return cls_keys == dict_keys
