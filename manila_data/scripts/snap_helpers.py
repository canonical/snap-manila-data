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

import importlib
import importlib.metadata
import os
import pathlib

from snaphelpers.scripts import snap_helpers as sh

CRAFT_PART_BUILD = os.environ["CRAFT_PART_BUILD"]

original_get_hooks = sh.get_hooks

paths = list(pathlib.Path(CRAFT_PART_BUILD).glob("*.egg-info"))

if len(paths) == 0:
    raise Exception(f"No egg-info found at {CRAFT_PART_BUILD}")

if len(paths) > 1:
    raise Exception(f"Multiple egg-info found at {CRAFT_PART_BUILD}")

dist_info_path = paths[0]

dist_info = importlib.metadata.Distribution.at(dist_info_path)

if dist_info.name is None:
    raise Exception(f"Could not determine project name from {dist_info_path}")


def filtered_hooks(*args, **kwargs):
    """Filtered hooks by build project."""
    hooks = original_get_hooks(*args, **kwargs)
    hooks_ = []
    for hook in hooks:
        if hook.project != dist_info.name:
            print("Filtering out ", hook.name, "from", hook.project)
            continue
        hooks_.append(hook)
    return hooks_


sh.get_hooks = filtered_hooks

script = sh.SnapHelpersScript()
