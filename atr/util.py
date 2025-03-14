# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import dataclasses
import functools
import hashlib
import pathlib
from collections.abc import Mapping
from typing import Annotated, Any, TypeVar

import aiofiles
import pydantic
import pydantic_core
import quart_wtf
import quart_wtf.typing

import atr.config as config

F = TypeVar("F", bound="QuartFormTyped")
T = TypeVar("T")


# from https://github.com/pydantic/pydantic/discussions/8755#discussioncomment-8417979
@dataclasses.dataclass
class DictToList:
    key: str

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: pydantic.GetCoreSchemaHandler,
    ) -> pydantic_core.CoreSchema:
        adapter = _get_dict_to_list_inner_type_adapter(source_type, self.key)

        return pydantic_core.core_schema.no_info_before_validator_function(
            _get_dict_to_list_validator(adapter, self.key),
            handler(source_type),
        )


class QuartFormTyped(quart_wtf.QuartForm):
    """Quart form with type annotations."""

    @classmethod
    async def create_form(
        cls: type[F],
        formdata: object | quart_wtf.typing.FormData = quart_wtf.form._Auto,
        obj: Any | None = None,
        prefix: str = "",
        data: dict | None = None,
        meta: dict | None = None,
        **kwargs: dict[str, Any],
    ) -> F:
        """Create a form instance with typing."""
        form = await super().create_form(formdata, obj, prefix, data, meta, **kwargs)
        if not isinstance(form, cls):
            raise TypeError(f"Form is not of type {cls.__name__}")
        return form


def compute_sha3_256(file_data: bytes) -> str:
    """Compute SHA3-256 hash of file data."""
    return hashlib.sha3_256(file_data).hexdigest()


async def compute_sha512(file_path: pathlib.Path) -> str:
    """Compute SHA-512 hash of a file."""
    sha512 = hashlib.sha512()
    async with aiofiles.open(file_path, "rb") as f:
        chunk = await f.read(4096)
        while chunk:
            sha512.update(chunk)
            chunk = await f.read(4096)
    return sha512.hexdigest()


@functools.cache
def get_admin_users() -> set[str]:
    return set(config.get().ADMIN_USERS)


def get_release_storage_dir() -> str:
    return str(config.get().RELEASE_STORAGE_DIR)


def is_admin(user_id: str | None) -> bool:
    """Check whether a user is an admin."""
    if user_id is None:
        return False
    return user_id in get_admin_users()


def unwrap(value: T | None, error_message: str = "unexpected None when unwrapping value") -> T:
    """
    Will unwrap the given value or raise a ValueError if it is None

    :param value: the optional value to unwrap
    :param error_message: the error message when failing to unwrap
    :return: the value or a ValueError if it is None
    """
    if value is None:
        raise ValueError(error_message)
    else:
        return value


def validate_as_type(value: Any, t: type[T]) -> T:
    """Validate the given value as the given type."""
    if not isinstance(value, t):
        raise ValueError(f"Expected {t}, got {type(value)}")
    return value


def _get_dict_to_list_inner_type_adapter(source_type: Any, key: str) -> pydantic.TypeAdapter[dict[Any, Any]]:
    root_adapter = pydantic.TypeAdapter(source_type)
    schema = root_adapter.core_schema

    # support further nesting of model classes
    if schema["type"] == "definitions":
        schema = schema["schema"]

    assert schema["type"] == "list"
    assert (item_schema := schema["items_schema"])
    assert item_schema["type"] == "model"
    assert (cls := item_schema["cls"])  # noqa: RUF018

    fields = cls.model_fields

    assert (key_field := fields.get(key))  # noqa: RUF018
    assert (other_fields := {k: v for k, v in fields.items() if k != key})  # noqa: RUF018

    model_name = f"{cls.__name__}Inner"

    # Create proper field definitions for create_model
    inner_model = pydantic.create_model(model_name, **{k: (v.annotation, v) for k, v in other_fields.items()})  # type: ignore
    return pydantic.TypeAdapter(dict[Annotated[str, key_field], inner_model])  # type: ignore


def _get_dict_to_list_validator(inner_adapter: pydantic.TypeAdapter[dict[Any, Any]], key: str) -> Any:
    def validator(val: Any) -> Any:
        from pydantic.fields import FieldInfo

        if isinstance(val, dict):
            validated = inner_adapter.validate_python(val)

            # need to get the alias of the field in the nested model
            # as this will be fed into the actual model class
            def get_alias(field_name: str, field_infos: Mapping[str, FieldInfo]) -> Any:
                field = field_infos[field_name]
                return field.alias if field.alias else field_name

            return [
                {key: k, **{get_alias(f, v.model_fields): getattr(v, f) for f in v.model_fields}}
                for k, v in validated.items()
            ]

        return val

    return validator
