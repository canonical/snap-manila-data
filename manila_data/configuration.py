# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configuration module for the manila-data snap.

This module holds the definition of all configuration options the snap
takes as input from `snap set`.
"""

import ipaddress

import pydantic
import pydantic.alias_generators


def to_kebab(value: str) -> str:
    return pydantic.alias_generators.to_snake(value).replace("_", "-")


class ParentConfig(pydantic.BaseModel):
    """Set common model configuration for all models."""

    model_config = pydantic.ConfigDict(
        alias_generator=pydantic.AliasGenerator(
            validation_alias=to_kebab,
            serialization_alias=pydantic.alias_generators.to_snake,
        ),
    )


class DatabaseConfiguration(ParentConfig):
    url: str


class RabbitMQConfiguration(ParentConfig):
    url: str


class Settings(ParentConfig):
    debug: bool = False
    enable_telemetry_notifications: bool = False

    # Comma-separated IPs of this node granted access to shares for
    # host-assisted migration (manila data_node_access_ips).
    data_node_access_ips: str | None = None

    @pydantic.field_validator("data_node_access_ips")
    @classmethod
    def _validate_ips(cls, value: str | None) -> str | None:
        if value is None:
            return None
        ips = [ip.strip() for ip in value.split(",") if ip.strip()]
        for ip in ips:
            ipaddress.ip_address(ip)
        return ",".join(ips) or None


class Configuration(ParentConfig):
    """Configuration class."""

    settings: Settings = Settings()
    database: DatabaseConfiguration
    rabbitmq: RabbitMQConfiguration
