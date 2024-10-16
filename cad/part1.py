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

# Thicknesses of Silicone parts.
silicone_vertical_wall_t = 2  # Thickness in X/Y.
silicone_horizontal_wall_t = 3  # Thickness in Z, on top of plate.

# Other silicone dimensions.
silicone_dist_on_top = 10
silicone_dist_on_bottom = 5

# Thicknesses of Molds.
mold_general_t = 3


def validate():
    """Raise if variables are not valid."""
    pass


def make_plate_model() -> bd.Part:
    p = bd.Part()

    # Stack it up from the bottom.
    # Wide base plate.
    p += bd.Box(
        top_level_width,
        top_level_width,
        top_level_height,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX),
    )

    # Hot part
    p += bd.Box(
        hot_level_width,
        hot_level_width,
        hot_level_height,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    )

    return p


if __name__ == "__main__":
    validate()

    parts = {
        "plate_model": show(make_plate_model()),
    }

    logger.info("Showing CAD model(s)")

    (export_folder := Path(__file__).parent.with_name("build")).mkdir(
        exist_ok=True
    )
    for name, part in parts.items():
        assert isinstance(part, bd.Part), f"{name} is not a Part"
        # assert part.is_manifold is True, f"{name} is not manifold"

        bd.export_stl(part, str(export_folder / f"{name}.stl"))
        bd.export_step(part, str(export_folder / f"{name}.step"))
