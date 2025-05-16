import random
from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function, object_type

@object_type
class App:
    @function
    def container_echo(self, string_arg: str) -> dagger.Container:
        """Returns a container that echoes whatever string argument is provided"""
        return dag.container().from_("dtcooper/raspberrypi-os:python").with_exec(["echo", string_arg])
    
    @function
    async def publish(
        self,
        source: Annotated[dagger.Directory, DefaultPath("/")],
    ) -> str:
        """Publish the application container after building and testing it on-the-fly"""
        await self.test(source)
        return await self.build(source).publish(
            "docker.io/johnhkchen/water-bot"
        )

    @function
    def build(
        self,
        source: Annotated[dagger.Directory, DefaultPath("/")],
    ) -> dagger.Container:
        """Build a Python application image that runs your FastHTML server via uv"""
        # reuse your venv+deps from build_env
        app = self.build_env(source)

        return (
            app
            .with_env_variable("HOST", "0.0.0.0")
            .with_env_variable("PORT", "5001")
            .with_exposed_port(5001)
            .with_entrypoint(["uv", "run", "src/app/main.py"])
        )
        
    @function
    async def test(
        self,
        source: Annotated[dagger.Directory, DefaultPath("/")],
    ) -> str:
        """Return the result of running unit tests via uv’s venv"""
        return await (
            self.build_env(source)
            .with_exec(
                ["uv", "run", "pytest", "--maxfail=1", "--disable-warnings"]
            )
            .stdout()
        )

    @function
    def build_env(
        self,
        source: Annotated[dagger.Directory, DefaultPath("/")],
    ) -> dagger.Container:
        """Build a ready-to-use development environment with uv-managed venv"""
        return (
            dag.container()
            .from_("python:3.13-slim")
            .with_directory("/src", source)
            .with_workdir("/src")
            # cache pip downloads for speed
            .with_mounted_cache(
                "/root/.cache/pip",
                dag.cache_volume("pip_cache"),
            )
            # get newest pip + uv
            .with_exec(["pip", "install", "--upgrade", "pip"])
            .with_exec(["pip", "install", "uv"])
            # uv will read pyproject.toml + uv.lock and create .venv/
            .with_exec(["uv", "sync"])
        )


import os
from fasthtml.common import *

app, rt = fast_app()

@rt("/")
def get():
    return Titled("FastHTML", P("Let's do this!"))

if __name__ == "__main__":
    # explicitly read HOST/PORT
    serve(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5001")),
    )
    
