import numpy as np
import pygame
from pygame import draw


def draw_arrow(
    canvas: pygame.Surface,
    origin: tuple[int, int],
    length_arrow: int,
    width_head: int,
    length_head: int,
    rotate_deg: float,
    color: tuple[int, int, int],
    width_line: int,
) -> None:
    """
    Draw an arrow on the given canvas.

    Parameters:
        canvas: The pygame.Surface object on which to draw the arrow.
        origin: The origin of the arrow, as two integers (coordinates on surface).
        length_arrow: The length of the arrow from origin to the tip (in pixel).
        width_head: How far the arrow head extends to the sides (in pixel).
        length_head: How far the arrow head extends back (from the tip) (in pixel).
        rotate_deg: The angle by which to rotate the arrow head counterclockwise (in degrees).
            0 means pointing downwards. NOTE: Because of the screen coordinate system,
            it will LOOK LIKE a clockwise rotation on the screen.
        color: The color of the arrow, as a tuple of three integers (RGB).
        width_line: The width of the arrow (in pixel).
    """
    origin_x, origin_y = origin
    arrow_head_x = origin_x
    arrow_head_y = origin_y + length_arrow  # Pointing downwards initially
    points = [
        origin,
        (arrow_head_x, arrow_head_y),
        (
            arrow_head_x - width_head,
            arrow_head_y - length_head,
        ),
        (arrow_head_x, arrow_head_y),
        (
            arrow_head_x + width_head,
            arrow_head_y - length_head,
        ),
        (arrow_head_x, arrow_head_y),
    ]
    origin_vec = pygame.math.Vector2(origin_x, origin_y)
    if rotate_deg != 0:
        rotated_points = [
            (pygame.math.Vector2(x, y) - origin_vec).rotate(rotate_deg) + origin_vec
            for x, y in points
        ]
    else:
        rotated_points = points
    draw.polygon(
        canvas,
        color,
        rotated_points,
        width=width_line,
    )


def draw_ellipse_from_eigen(
    canvas: pygame.Surface,
    center: tuple[int, int],
    radius_minor: float,
    Q: np.ndarray,
):
    """Draw an ellipse from the given matrix (the ellipse representing its curvature).

    Parameters:
        canvas: The pygame.Surface object on which to draw the ellipse
        center: The center of the ellipse as a tuple of two integers (coordinates on surface).
        radius_minor: The radius of the ellipse minor axis,
            (the other axis will be stretched according to the eigenvalues).
    """
    # Calculate eigenvalues and eigenvectors
    vals, vecs = np.linalg.eig(Q)

    # angle of rotation
    angle = np.arctan2(vecs[1, 0], vecs[0, 0])

    # Scale the radius of the axes such that the bigger axis is equal to radius_major
    if vals[0] > vals[1]:
        width = 2 * radius_minor
        height = 2 * radius_minor / np.sqrt(vals[1]) * np.sqrt(vals[0])
    else:
        width = 2 * radius_minor / np.sqrt(vals[0]) * np.sqrt(vals[1])
        height = 2 * radius_minor

    # Create a surface to draw the ellipse
    ellipse_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    ellipse_surface.fill((0, 0, 0, 0))

    pygame.draw.ellipse(ellipse_surface, (0, 0, 0), ellipse_surface.get_rect(), 2)

    ellipse_surface = pygame.transform.rotate(ellipse_surface, np.degrees(angle))

    rect = ellipse_surface.get_rect(center=center)

    canvas.blit(ellipse_surface, rect.topleft)
