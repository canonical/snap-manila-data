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

import abc
import inspect
import logging
import typing
from pathlib import Path

import jinja2
import pydantic
from snaphelpers import Snap

from . import configuration, context, error, log, services, template

ETC_MANILA = Path("etc/manila")


CONF = typing.TypeVar("CONF", bound=configuration.Configuration)


class ManilaData(typing.Generic[CONF], abc.ABC):
    def __init__(self) -> None:
        self._contexts: typing.Sequence[context.Context] | None = None

    @classmethod
    def install_hook(cls, snap: Snap) -> None:
        log.setup_logging(snap.paths.common / "hooks.log")
        cls().install(snap)

    @classmethod
    def configure_hook(cls, snap: Snap) -> None:
        log.setup_logging(snap.paths.common / "hooks.log")
        try:
            cls().configure(snap)
        except error.ManilaError:
            logging.warning("Configuration not complete", exc_info=True)

    def install(self, snap: Snap) -> None:
        self.setup_dirs(snap)
        self.template(snap)

    def configure(self, snap: Snap) -> None:
        self.setup_dirs(snap)
        modified = self.template(snap)
        self.start_services(snap, modified)

    def start_services(
        self,
        snap: Snap,
        modified_tpl: typing.Sequence[template.Template],
    ) -> None:
        snap_services = snap.services.list()
        for name, snap_service in snap_services.items():
            logging.debug("Restarting service %s", name)
            if modified_tpl:
                snap_service.restart()
            else:
                snap_service.start()

    @abc.abstractmethod
    def config_type(self) -> typing.Type[CONF]:
        raise NotImplementedError

    def get_config(self, snap: Snap) -> CONF:
        keys = self.config_type().model_fields.keys()
        try:
            return self.config_type().model_validate(
                snap.config.get_options(*keys).as_dict()
            )
        except pydantic.ValidationError as e:
            raise error.ManilaError("Invalid configuration") from e

    def directories(self) -> list[template.Directory]:
        """Directories to be created on the common path."""
        return [
            template.CommonDirectory("etc/manila"),
            template.CommonDirectory("lib/manila"),
        ]

    def template_files(self) -> list[template.Template]:
        """Files to be templated."""
        return [
            template.CommonTemplate("manila.conf", ETC_MANILA),
            template.CommonTemplate("rootwrap.conf", ETC_MANILA),
        ]

    def contexts(self, snap: Snap) -> typing.Sequence[context.Context]:
        """Contexts to be used in the templates."""
        if self._contexts is None:
            self._contexts = [
                context.SnapPathContext(snap),
                *(
                    context.ConfigContext(k, v)
                    for k, v in self.get_config(snap).model_dump().items()
                ),
            ]
        return self._contexts

    def render_context(
        self, snap: Snap
    ) -> typing.MutableMapping[str, typing.Mapping[str, str]]:
        context = {}
        for ctx in self.contexts(snap):
            logging.debug("Adding context: %s", ctx.namespace)
            context[ctx.namespace] = ctx.context()
        return context

    def setup_dirs(self, snap: Snap) -> None:
        directories = self.directories()

        for d in directories:
            path: Path = getattr(snap.paths, d.location).joinpath(d.path)
            logging.debug("Creating directory: %s", path)
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(d.mode)

    def templates_search_path(self, snap: Snap) -> list[Path]:
        try:
            extra = [Path(inspect.getfile(self.__class__)).parent / "templates"]
        except Exception:
            logging.error("Failed to get templates path from class", exc_info=True)
            extra = []
        return [
            snap.paths.common / "templates",
            *extra,
            Path(__file__).parent / "templates",
        ]

    def _process_template(
        self,
        snap: Snap,
        env: jinja2.Environment,
        template: template.Template,
        context: typing.Mapping[str, typing.Mapping[str, str]],
    ) -> bool:
        file_name = template.filename
        dest_dir: Path = getattr(snap.paths, template.location) / template.dest
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / file_name.removesuffix(".j2")

        original_hash = None
        if dest_file.exists():
            original_hash = hash(dest_file.read_text())
            return False

        logging.debug("File %s has changed, writing new content", dest_file)

        tpl = None
        template_file = template.template()
        try:
            tpl = env.get_template(template_file)
        except jinja2.exceptions.TemplateNotFound:
            logging.debug("Template %s not found, trying with .j2", template_file)
            tpl = env.get_template(template_file + ".j2")

        rendered = tpl.render(**context)
        if len(rendered) > 0 and rendered[-1] != "\n":
            # ensure trailing new line
            rendered += "\n"

        new_hash = hash(rendered)

        if original_hash == new_hash:
            logging.debug("File %s has not changed, skipping", dest_file)

        dest_file.write_text(rendered)
        dest_file.chmod(template.mode)
        return True

    def template(self, snap: Snap) -> list[template.Template]:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath=self.templates_search_path(snap)),
            keep_trailing_newline=True,
        )
        modified_templates: list[template.Template] = []
        try:
            context = self.render_context(snap)
        except Exception as e:
            logging.error("Failed to render context: %s", e)
            return modified_templates
        # process general templates
        for tpl in self.template_files():
            if self._process_template(snap, env, tpl, context):
                modified_templates.append(tpl)

        return modified_templates


class GenericManilaData(ManilaData[configuration.Configuration]):
    def config_type(self) -> typing.Type[configuration.Configuration]:
        return configuration.Configuration
