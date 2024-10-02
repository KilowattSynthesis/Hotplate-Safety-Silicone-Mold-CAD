import os
from pathlib import Path

import build123d as bd

from loguru import logger


if os.getenv("CI"):

    def show(*args: object) -> bd.Part:
        """Do nothing (dummy function) to skip showing the CAD model in CI."""
        logger.info(f"Skipping show({args}) in CI")
        return args[0]
else:
    import ocp_vscode

    def show(*args: object) -> bd.Part:
        """Show the CAD model in the CAD viewer."""
        ocp_vscode.show(*args)
        return args[0]


# Constants
top_level_width = 218
top_level_height = 39

hot_level_width = 200
hot_level_height = 3.5


def validate():
    """Raise if variables are not valid."""
    pass


def make_part1():
    # Orientation: ...
    with bd.BuildPart() as part1:
        bd.Cylinder(radius=20, height=20)

    return part1.part


if __name__ == "__main__":
    validate()

    parts = {
        "part1": make_part1(),
    }

    logger.info("Showing CAD model(s)")
    show(parts["part1"])

    (export_folder := Path(__file__).parent.with_name("build")).mkdir(
        exist_ok=True
    )
    for name, part in parts.items():
        assert isinstance(part, bd.Part), f"{name} is not a Part"
        # assert part.is_manifold is True, f"{name} is not manifold"

        bd.export_stl(part, str(export_folder / f"{name}.stl"))
        bd.export_step(part, str(export_folder / f"{name}.step"))
