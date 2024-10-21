import itertools
from typing import Literal
from pathlib import Path

import build123d as bd

from loguru import logger

import build123d_ease as bde
from build123d_ease import show


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
mold_general_t = 1.8

# Bolt specs.
bolt_diameter = 3.2
bolt_standoff_od = 7
bolt_standoff_length = silicone_vertical_wall_t
bolt_hole_signs = list(itertools.product([20, 85, -20, -85], [10, -10]))

# Pouring hole.
pouring_hole_diameter = 28

top_filament_saver_box = (125, 125, 100)
bottom_filament_saver_box = (170, 192, 100)

# region Calculated dimensions
total_cast_outside_length = (2 * silicone_vertical_wall_t) + max(
    hot_level_width, top_level_width
)
total_cast_outside_height = (2 * silicone_horizontal_wall_t) + (
    hot_level_height + top_level_height
)

total_mold_outside_length = (2 * mold_general_t) + total_cast_outside_length
total_mold_outside_height = (2 * mold_general_t) + total_cast_outside_height
# end region


def validate() -> None:
    """Raise if variables are not valid."""

    logger.info(
        "Volume of silicone cast: "
        f"{make_silicone_cast_positive().volume / 1e3:.2f} mL"
    )


def make_plate_model() -> bd.Part:
    """A model of the literal hot plate."""
    p = bd.Part()

    # Stack it up from the bottom.
    # Wide base plate.
    p += bd.Box(
        top_level_width,
        top_level_width,
        top_level_height,
        align=bde.align.TOP,
    )

    # Hot part
    p += bd.Box(
        hot_level_width,
        hot_level_width,
        hot_level_height,
        align=bde.align.BOTTOM,
    )

    return p


def _make_silicone_cast_positive_outline() -> bd.Part:
    p = (
        cast_outside := bd.Part()
        + bd.Box(
            total_cast_outside_length,
            total_cast_outside_length,
            total_cast_outside_height,
        )
    ).fillet(radius=silicone_box_outer_radius, edge_list=cast_outside.edges())

    return p


def make_silicone_cast_positive(
    *, remove_real_hot_plate: bool = True
) -> bd.Part:
    """Create the silicone cast positive.

    This will be roughly equivalent to the final output of this project,
    after casting.
    """
    p = bd.Part()

    p += _make_silicone_cast_positive_outline()

    # Remove the actual hot plate.
    if remove_real_hot_plate:
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
            align=bde.align.BOTTOM,
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
            align=bde.align.TOP,
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
            align=bde.align.LEFT,
        )

    return p


def make_silicone_mold_outer(*, with_pour_hole: bool) -> bd.Part:
    """Makes the outer portion of the silicone mold."""

    p = bd.Part()

    p += bd.Box(
        total_mold_outside_length,
        total_mold_outside_length,
        total_mold_outside_height,
    )

    # Remove the silicone cast.
    cast = _make_silicone_cast_positive_outline()
    p -= cast.translate(
        (
            0,
            0,
            cast.bounding_box().center().Z,
        )
    )

    # Remove pouring hole (+X face).
    if with_pour_hole:
        p -= bd.Cylinder(
            radius=pouring_hole_diameter / 2,
            height=1000,
            rotation=bde.rotation.POS_X,
            align=bde.align.BOTTOM,  # "Normal" for rotation.
        )

    # Remove a big filament saver hole.
    p -= bd.Box(*[dim - 8 for dim in top_filament_saver_box])
    p -= bd.Box(
        *[dim - 8 for dim in bottom_filament_saver_box], align=bde.align.TOP
    )

    # Add the standoffs.
    # Remove the bolt holes.
    for y_pos, z_pos in bolt_hole_signs:
        # Standoff.
        p += bd.Cylinder(
            radius=bolt_standoff_od / 2,
            height=bolt_standoff_length,
            rotation=bde.rotation.NEG_X,
            align=bde.align.BOTTOM,  # Make it "normal" for rotation.
        ).translate(
            (
                # X: To the inside of the wall.
                total_cast_outside_length / 2,
                y_pos,
                z_pos,
            ),
        )

        # Bolt holes.
        p -= bd.Cylinder(
            radius=bolt_diameter / 2,
            height=1000,
            rotation=bde.rotation.POS_X,
            align=bde.align.BOTTOM,  # Make it "normal" for rotation.
        ).translate(
            (0, y_pos, z_pos),
        )

    # Keep only the positive X side.
    if 1:
        p = p & bd.Box(
            1000,
            1000,
            1000,
            align=bde.align.LEFT,
        )

    return p


def make_silicone_mold_inner() -> bd.Part:
    """Make the inner portion of the silicone mold."""

    p = bd.Part()

    p += _make_silicone_cast_positive_outline()

    p -= make_silicone_cast_positive()

    # Remove the bolt holes.
    for y_pos, z_pos in bolt_hole_signs:
        # Bolt holes.
        p -= bd.Cylinder(
            radius=bolt_diameter / 2,
            height=1000,
            rotation=bde.rotation.POS_X,
        ).translate(
            (0, y_pos, z_pos),
        )

    # Remove filament saver hole (which also provides nut access).
    p -= bd.Box(*top_filament_saver_box)

    # Remove more aggressive filament saver hole.
    p -= bd.Box(*bottom_filament_saver_box, align=bde.align.TOP).translate(
        (
            0,
            0,
            p.faces().sort_by(bd.Axis.Z)[-1].center().Z
            - hot_level_height
            - silicone_horizontal_wall_t
            - mold_general_t,
        )
    )

    return p


def make_silicone_mold_inner_half(side: Literal["left", "right"]) -> bd.Part:
    """Make a half of the inner portion of the silicone mold."""

    p = make_silicone_mold_inner()

    if side == "left":
        p = p & bd.Box(
            1000,
            1000,
            1000,
            align=bde.align.FRONT,
        )
    elif side == "right":
        p = p & bd.Box(
            1000,
            1000,
            1000,
            align=bde.align.BACK,
        )
    else:
        raise ValueError(f"Invalid side: {side}")

    return p


def make_mold_assembly() -> bd.Part:
    """Makes an assembly of the silicone mold inner and outer parts."""

    p = bd.Part()

    p += make_silicone_mold_outer(with_pour_hole=False)

    # Scale is mostly so we can clearly see the separation.
    p += make_silicone_mold_inner().scale(0.995)

    return p


if __name__ == "__main__":
    validate()

    # zz indicates that it's a demo/preview part only.
    # Quantity prefix is the nominal quantity of the part to make.
    parts = {
        "1x_silicone_mold_outer_with_hole": show(
            make_silicone_mold_outer(with_pour_hole=True)
        ),
        "1x_silicone_mold_outer_without_hole": show(
            make_silicone_mold_outer(with_pour_hole=False)
        ),
        "1x_silicone_mold_inner_half_left": (
            make_silicone_mold_inner_half("left")
        ),
        "1x_silicone_mold_inner_half_right": (
            make_silicone_mold_inner_half("right")
        ),
        "zz_plate_model": (make_plate_model()),
        "zz_silicone_cast_positive": (make_silicone_cast_positive()),
        "zz_silicone_mold_inner": (make_silicone_mold_inner()),
        "zz_mold_assembly": (make_mold_assembly()),
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
