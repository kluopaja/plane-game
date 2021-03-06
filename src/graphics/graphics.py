import logging
import sys
import math
from abc import ABC, abstractmethod
from game.shapes import Rectangle
from graphics.image import Image
from utils.float_rect import FloatRect


class Graphic(ABC):
    """A base class for movable and rotatable graphics.

    Attributes:
        `location`: A pygame.Vector2
            The location of the Graphic
        `rotation`: Radians
            Positive rotation mean counter-clockwise
            (in coordinates where x grows right and y grows down)

        NOTE: See Shape class for more detailed descriptions.

    """
    @abstractmethod
    def draw(self, camera):
        pass

    @property
    @abstractmethod
    def location(self):
        pass

    @location.setter
    @abstractmethod
    def location(self, value):
        pass

    @property
    @abstractmethod
    def rotation(self):
        pass

    @rotation.setter
    @abstractmethod
    def rotation(self, value):
        pass


class PolylineGraphic(Graphic):
    """A class for drawing a polyline"""
    def __init__(self, polyline, color, width):
        """Initializes PolylineGraphic.

        Arguments:
            `polyline`: A Polyline
                The polyline to be drawn.
            `color`: A tuple of 3
                The color of the polyline
            `width`: A positive float
                The width of the line in game world coordinates
        """
        self._polyline = polyline
        self.color = color
        self.width = width

    def draw(self, camera):
        """Draws image on `camera`.

        Arguments:
            `camera`: Camera
                The target of drawing
        """
        for line in self._polyline.lines:
            camera.draw_line(line.begin, line.end, self.color, self.width)

    @property
    def location(self):
        return self._polyline.location

    @location.setter
    def location(self, value):
        self._polyline.location = value

    @property
    def rotation(self):
        return self._polyline.rotation

    @rotation.setter
    def rotation(self, value):
        self._polyline.rotation = value


class ImageGraphic(Graphic):
    """Class for movable and rotatable images."""

    def __init__(self, rectangle, image):
        """Initializes ImageGraphic.

        Arguments:
            `rectangle`: A Rectangle
                Defines the area to which the image is drawn.
                NOTE: Should really be unrotated (i.e. topleft at topleft, etc)
                when the `rectangle.rotation` == 0. This is because
                `rectangle.rotation` is used to determine the rotation
                of the drawn `image`.
            `image`: An Image

        NOTE: The drawing of the image is done by setting its height to
        match that of the `rectangle`. Therefore `rectangle` and `image`
        should have (approximately) the same aspect ratio!
        """

        rectangle_size = rectangle.size()
        rectangle_aspect_ratio = rectangle_size[0] / rectangle_size[1]
        image_aspect_ratio = image.get_width_pixels() / image.get_height_pixels()

        if abs(rectangle_aspect_ratio - image_aspect_ratio) > 0.1:
            raise ValueError("`rectangle` and `image` should have approximately \
                              the same aspect ratio!")

        self._rectangle = rectangle
        self._image = image

    @classmethod
    def from_image_path(cls, image_path, center_offset, size):
        """Creates ImageGraphic from an image file.

        Scales image to match the `size` aspect ratio.

        Arguments:
            `image_path`: pathlib.Path object
                Denotes the path to the image.
            `center_offset`: Vector2
                The position of the center of the image relative to the
                `location` of the ImageGraphic
            `size`: Vector2
                The dimensions of the image

        Returns:
            An ImageGraphic object
        """

        helper_rect = FloatRect(0, 0, size[0], size[1])
        helper_rect.center = (math.floor(
            center_offset[0]), math.floor(center_offset[1]))
        rectangle = Rectangle.from_rect(helper_rect)
        try:
            image = Image(image_path)
        except Exception:
            logging.critical(f"Failed loading image from {image_path}.")
            logging.critical(f"Are the configuration files OK?")
            sys.exit()
        image.set_aspect_ratio(helper_rect.width, helper_rect.height)
        return ImageGraphic(rectangle, image)

    def draw(self, camera):
        """Draws image on `camera`.

        Arguments:
            `camera`: A Camera
        """
        camera.draw_image(self._image, self._rectangle.center(),
                    self._rectangle.rotation, self._rectangle.size()[1])

    @property
    def location(self):
        return self._rectangle.location

    @location.setter
    def location(self, value):
        self._rectangle.location = value

    @property
    def rotation(self):
        return self._rectangle.rotation

    @rotation.setter
    def rotation(self, value):
        self._rectangle.rotation = value
