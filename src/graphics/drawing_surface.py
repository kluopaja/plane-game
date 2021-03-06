import math
import pygame
from pygame import Rect, Vector2
from utils.float_rect import FloatRect

# NOTE the window resizing hasn't been implemented yet
# but should work as long as we always create a new DrawingSurface
# at each rendering
class DrawingSurface:
    """A drawing surface with own coordinate space.

    The purpose of DrawingSurface is to separate drawing graphics
    from the pixel coordinates and allow splitting the window
    into multiple subwindows.


    The DrawingSurface relative coordinates:
        The origo is at the top left corner.
        x axis grows right and y grows down.
        The height of the DrawingSurface is 1 and the width depends
        on the aspect ratio.
    """
    def __init__(self, surface, screen, absolute_topleft):
        """Initializes a DrawingSurface.

        Arguments:
            `surface`: A pygame.Surface
                The Surface used for drawing.
            `screen`: A Screen object
                The Screen containing the `surface` (maybe as a subsurface)
            `absolute_topleft`: Vector2
                The absolute pixel coordinates of the top left corner
        """

        self._surface = surface
        self._screen = screen
        self._absolute_topleft = absolute_topleft

    def subsurface(self, area):
        """Returns a new DrawingSurface corresponding to `area`.

        Arguments:
            `area`: A FloatRect (Relative DrawingSurface coordinates)
                The area corresponding to the new subsurface.
                Should have pixel area larger than 0!
                Should be fully inside `self`
        """

        rect_topleft = self._to_pixel_coordinates(area.topleft)
        size = self._to_pixel_coordinates(area.size)
        _area = Rect(rect_topleft[0], rect_topleft[1], size[0], size[1])
        new_absolute_topleft = rect_topleft + self._absolute_topleft
        if size[0] <= 0 or size[1] <= 0:
            raise ValueError("Cannot make a subsurface with pixel area 0")
        return DrawingSurface(self._surface.subsurface(_area), self._screen,
                              new_absolute_topleft)

    def aspect_ratio_subsurface(self, aspect_ratio):
        """Returns the maximal subsurface with width/height = `aspect_ratio`.

        Arguments:
            `aspect_ratio`: A positive float
        """
        area = self.get_rect()
        width = area.width
        if width > aspect_ratio:
            area.width = aspect_ratio
        else:
            area.height = width / aspect_ratio
        area.center = Vector2(width / 2, 0.5)
        return self.subsurface(area)

    def get_relative_width(self):
        """The width of the DrawingSurface relative to the height.

        i.e. the width in DrawingSurface relative coordinates."""
        return self._surface.get_width() / self._surface.get_height()

    def blur(self, n_pixels):
        """Blurs `self`.

        Blurs `self` by performing consecutive downscale and upscale operations.

        NOTE: This is very slow!

        Arguments:
            `n_pixels`: A positive integer
                The number of horizontal and vertical pixels in the downscaled
                image.
        """
        size = self._surface.get_size()
        tmp = pygame.transform.smoothscale(
            self._surface, (size[0]//n_pixels, size[1]//n_pixels))
        dirty_rect = self._surface.blit(
            pygame.transform.scale(tmp, self._surface.get_size()),
            (0, 0)
        )
        self._add_dirty_rect(dirty_rect)

    def draw_line(self, begin, end, color, width=1, scaled=True):
        """Draws a line to `self`.

        Arguments:
            `color` a tuple of length 3 or 4
            `begin` a Vector2 (relative DrawingSurface coordinates)
            `end` a Vector2 (relative DrawingSurface coordinates)
            `width` a positive number
                If scaled == False:
                    the fraction of the self._screen's height
                If scaled == True:
                    the fraction of the self's height
        """

        _begin = self._to_pixel_coordinates(begin)
        _end = self._to_pixel_coordinates(end)
        if not scaled:
            _width = max(1, int(self._screen.get_height() * width))
        else:
            _width = max(1, int(self._surface.get_height() * width))

        dirty_rect = pygame.draw.line(self._surface, color, _begin, _end, _width)
        self._add_dirty_rect(dirty_rect)

    def draw_image(self, image, position, rotation, height):
        """Draws image to `self`

        Arguments:
            `image`: Image
            `position` Vector2 (relative DrawingSurface coordinates)
                The position of the center of the image
            `rotation`: radians
                The rotation, positive is to the ccw
            `height`: a positive number
                height of the image as the fraction of self's height
        """
        _position = self._to_pixel_coordinates(position)
        _height = height * self._surface.get_height()
        degrees_rotation = math.degrees(rotation)
        zoom_factor = _height / image.get_height_pixels()
        final_image = pygame.transform.rotozoom(image.image, degrees_rotation,
                                                zoom_factor)
        area = final_image.get_rect()
        area.center = _position
        dirty_rect = self._surface.blit(final_image, area.topleft)
        self._add_dirty_rect(dirty_rect)

    def draw_image_from_array(self, array, position, height):
        """Draws image from a numpy array.

        NOTE: SLOW!

        Arguments:
            `array` a numpy array of shape (?, ?, 4) (ARGB)
            `position` Vector2 (relative DrawingSurface coordinates)
                The position of the top left corner.
            `height`: a positive number
                height of the image as the fraction of self's height

        """
        _position = self._to_pixel_coordinates(position)
        _height = height * self._surface.get_height()
        image_surface = pygame.surfarray.make_surface(array[:, :, 1:]).convert_alpha()
        _width = _height * image_surface.get_width() / image_surface.get_height()
        _height = int(_height)
        _width = int(_width)
        pygame.surfarray.pixels_alpha(image_surface)[:, :] = array[:, :, 0]
        final_surface = pygame.transform.smoothscale(image_surface, (_width, _height))
        dirty_rect = self._surface.blit(final_surface, _position)
        self._add_dirty_rect(dirty_rect)

    def fill(self, color, update=False):
        """Fills `self._surface` with `color`

        Arguments:
            `color` a tuple of length 3 or 4
            `update` a boolean
                True: the screen will be forced to update
                False: Only the previous location of drawn elements will
                be updated
        """
        if update:
            self._screen.add_dirty_rect(self._surface.fill(color))
        else:
            self._surface.fill(color)


    def get_rect(self):
        """Returns a FloatRect of the relative screen area"""

        return FloatRect(0, 0, self.get_relative_width(), 1)

    def get_size(self):
        """Returns a Vector2 of the screen relative area"""

        return Vector2(self.get_relative_width(), 1)

    def get_font_height(self):
        """Returns the font height in relative DrawingSurface coordinates.

        NOTE: Use this as spacing between consecutive lines."""
        return self._screen.font.get_linesize() / self._surface.get_size()[1]

    def centered_text(self, text, position, color):
        """Draws `text` centered at `position`

        Arguments:
            `text`: A string
            `position`: pygame.Vector2
            `color`: A tuple of 3
        """
        _position = self._to_pixel_coordinates(position)
        text_surface = self._screen.font.render(text, True, color)
        dest = text_surface.get_rect()
        dest.center = (_position[0], _position[1])
        dirty_rect = self._surface.blit(text_surface, dest.topleft)
        self._add_dirty_rect(dirty_rect)

    def midtop_text(self, text, position, color):
        """Draws `text` with top middle at `position`
        """
        _position = self._to_pixel_coordinates(position)
        text_surface = self._screen.font.render(text, True, color)
        dest = text_surface.get_rect()
        dest.midtop = (_position[0], _position[1])
        dirty_rect = self._surface.blit(text_surface, dest.topleft)
        self._add_dirty_rect(dirty_rect)

    def topleft_text(self, text, position, color):
        """Draws `text` with top left edge at `position`
        """
        _position = self._to_pixel_coordinates(position)
        text_surface = self._screen.font.render(text, True, color)
        dest = text_surface.get_rect()
        dest.topleft = (_position[0], _position[1])
        dirty_rect = self._surface.blit(text_surface, dest.topleft)
        self._add_dirty_rect(dirty_rect)

    def _to_pixel_coordinates(self, relative_coords):
        tmp = Vector2(relative_coords) * self._surface.get_size()[1]
        # reduces jitter in the rendering
        tmp[0] = round(tmp[0])
        tmp[1] = round(tmp[1])
        return tmp

    def _add_dirty_rect(self, dirty_rect):
        """Add `dirty_rect` to `self._screen`.

        Transforms coordinates from `self._surface` space to
        the absolute screen coordinates and adds the transformed
        rect to `self._screen`.

        NOTE: modifies `dirty_rect`!

        Arguments:
            `dirty_rect`: A pygame.Rect
                The pixel coordinates of the rect with respect to
                `self._surface`
        """
        dirty_rect.topleft += self._absolute_topleft
        self._screen.add_dirty_rect(dirty_rect)
