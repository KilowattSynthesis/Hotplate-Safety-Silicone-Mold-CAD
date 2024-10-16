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
silicone_vertical_wall_t = 3.5  # Thickness in X/Y.
silicone_horizontal_wall_t = 3  # Thickness in Z, on top of plate.

# Other silicone dimensions.
silicone_dist_on_top = 25
silicone_dist_on_bottom = 10
silicone_dist_on_top_radius = 5
silicone_dist_on_bottom_radius = 15
silicone_box_outer_radius = 2

# Thicknesses of Molds.
mold_general_t = 3


def validate():
    """Raise if variables are not valid."""
    pass


def make_plate_model() -> bd.Part:
    """A model of the literal hot plate."""
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


def make_silicone_cast_positive() -> bd.Part:
    """Create the silicone cast positive."""

    total_mold_outside_length = (2 * silicone_vertical_wall_t) + max(
        hot_level_width, top_level_width
    )
    total_mold_outside_height = (2 * silicone_horizontal_wall_t) + (
        hot_level_height + top_level_height
    )

    p = bd.Part()

    p += bd.Box(
        total_mold_outside_length,
        total_mold_outside_length,
        total_mold_outside_height,
    )

    # Fillet the outside of the mold.
    p = p.fillet(radius=silicone_box_outer_radius, edge_list=p.edges())

    # Remove the actual hot plate.
    plate_model = make_plate_model()
    p -= plate_model.translate(
        (0, 0, -plate_model.center().Z),
    )

    # Remove top-side box to access the hotplate.
    p -= (
        top_box := bd.Part()
        + bd.Box(
            hot_level_width - 2 * silicone_dist_on_top,
            hot_level_width - 2 * silicone_dist_on_top,
            100,
            align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
        )
    ).fillet(
        radius=silicone_dist_on_top_radius,
        edge_list=top_box.edges().filter_by(bd.Axis.Z),
    )

    # Remove bottom-side clearance.
    p -= (
        bottom_box := bd.Part()
        + bd.Box(
            top_level_width - 2 * silicone_dist_on_bottom,
            top_level_width - 2 * silicone_dist_on_bottom,
            100,
            align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX),
        )
    ).fillet(
        radius=silicone_dist_on_bottom_radius,
        edge_list=bottom_box.edges().filter_by(bd.Axis.Z),
    )

    # Keep only the positive X side.
    if 0:
        p = p & bd.Box(
            1000,
            1000,
            1000,
            align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.CENTER),
        )

    # TODO: Add a test rendering of the bar that hold the plate, to ensure the
    # fillets are set well.

    return p


if __name__ == "__main__":
    validate()

    parts = {
        "plate_model": (make_plate_model()),
        "silicone_cast_positive": show(make_silicone_cast_positive()),
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
