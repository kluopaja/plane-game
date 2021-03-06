import math
from pygame import Vector2
from graphics.graphics import ImageGraphic
from game.shapes import Rectangle, Circle
from game.physics import BasePhysics, BodyPhysics, WingPhysics
from game.physics import PhysicsController
from utils.timing import Timer


def damage_score_generator(damage_score, destroying_score):
    """A closure for a score generator.

    Creates a function that can be used to parametrize how
    a GameObject rewards the Player that damaged it.

    Arguments:
        `damage_score`: a float
            The amount of score generated per unit of damage
        `destroying_score`: a float
            The amount of score generated if the GameObject is destroyed

    """
    def _inner(damage, destroyed):
        """A score generator function.

        Arguments:
            `damage`: a float
                The amount of damage done to the caller.
            `destroyed`: a boolean
                True if the caller GameObject was destroyed
                False otherwise.
        """
        return damage * damage_score + destroyed * destroying_score
    return _inner


class PlaneFactory:
    """A factory class for Plane.

    Attributes:
        start_position: pygame.Vector2
            The starting position of planes generated by the factory.
    """

    def __init__(self, plane_config):
        """Initializes a PlaneFactory class.

        NOTE: currently only a reference to `plane_config` is stored
        in the PlaneFactory.

        Arguments:
            `plane_config`: A PlaneConfig class
                The class defining the properties of the generated planes.
        """
        self._config = plane_config
        self.start_position = Vector2(0, 0)

    def plane(self, player_input, owner):
        """Factory method for Plane.

        Arguments:
            `player_input`: A PlayerInput
                The PlayerInput that will control the newly created Plane.
            `owner`: A Player
                The owner of the newly created Plane.
        """
        rectangle = self._plane_rectangle(self._config.size)
        image_graphic = ImageGraphic.from_image_path(self._config.image_file_path,
                                                     Vector2(0, 0), self._config.size)
        gravity = self._config.gravity

        def gravity_callback(position):
            return Vector2(0, 1) * gravity

        tmp = BasePhysics(Vector2(self.start_position),
                          Vector2(0, 0), Vector2(1, 0))
        tmp = BodyPhysics(tmp, self._config.body_drag, gravity_callback)
        tmp = WingPhysics(tmp, self._config.wing_size)
        plane_physics = PhysicsController(
            tmp, self._config.acceleration, self._config.rotation)

        gun = Gun.from_config(self._config.gun_config)


        _score_generator = damage_score_generator(self._config.score_per_damage,
                                                  self._config.score_when_destroyed)
        plane = Plane(rectangle, image_graphic, plane_physics, gun,
                      _score_generator, owner, health=self._config.health,
                      collision_damage=self._config.collision_damage)
        player_input.bind_plane(plane)

        return plane

    def get_plane_cost(self):
        """Returns:
            A float:
                Thecost of making a single plane."""
        return self._config.cost

    def _plane_rectangle(self, size):
        return Rectangle(Vector2(-size[0]/2, -size[1]/2),
                         Vector2(size[0]/2, -size[1]/2),
                         Vector2(-size[0]/2, size[1]/2))


class BulletFactory:
    """A factory class for Bullet objects"""
    def __init__(self, bullet_config):
        """Initializes a BulletFactory.

        Arguments:
            `bullet_config`: A BulletConfig
        """
        self._config = bullet_config

    def bullet(self, location, velocity, front, owner):
        """Factory method for Bullet.

        Arguments:
            `location`: A pygame.Vector2
            `velocity`: A pygame.Vector2
            `front`: A pygame.Vector2
                The vector pointing to the front of the bullet.
                Should have the length of 1.
            `owner`: A Player
                The owner of the Bullet
        """
        image_graphic = ImageGraphic.from_image_path(self._config.image_file_path,
                                                     Vector2(0, 0),
                                                     Vector2(self._config.diameter))
        circle = Circle(Vector2(0), self._config.diameter)
        gravity = self._config.gravity
        def gravity_callback(position):
            return Vector2(0, 1) * gravity
        tmp = BasePhysics(location, velocity, front)
        physics = BodyPhysics(tmp, self._config.body_drag, gravity_callback)
        return Bullet(circle, image_graphic, physics, owner,
                      Timer(self._config.timeout), self._config.health,
                      self._config.collision_damage)

class Gun:
    """A class representing a Gun"""
    def __init__(self, bullet_factory, timer, spawn_offset, speed):
        """Initializes a Gun.

        Arguments:
            `bullet_factory`: BulletFactory
                The factory used to make the Bullet objects fired
                by the Gun.
            `timer`: A Timer
                The timer defining the minimum time between consecutive shots.
            `spawn_offset`: A float
                The Bullet is spawned this much away from the Plane
                position to the direction of the Plane's front.

                Important to set this correctly as too small `spawn_offset`
                causes the Bullet to hit the Plane that fired the bullet.
            `speed`: A float
                The initial speed of the bullet
        """
        self._bullet_factory = bullet_factory
        self._timer = timer
        self._spawn_offset = spawn_offset
        self._speed = speed

    @classmethod
    def from_config(cls, gun_config):
        """Initializes Gun from a config file.

        Arguments:
            `gun_config`: A GunConfig
        """
        bullet_factory = BulletFactory(gun_config.bullet_config)
        return cls(bullet_factory, Timer(gun_config.bullet_spawn_time),
                   gun_config.bullet_spawn_offset, gun_config.bullet_speed)

    def update(self, delta_time):
        """Updates the Gun's timer.

        Arguments:
            `delta_time`: A float
                The amount of time passed
        """
        self._timer.update(delta_time)

    def shoot(self, location, velocity, front, owner):
        """Creates a Bullet if enough time has passed since last successful shot.

        Arguments:
            `location`: A pygame.Vector2
                The location of the Gun.
            `velocity`: A pygame.Vector2
                The velocity of the Gun.
            `front`: A pygame.Vector2
                The direction of the Gun.
                Should be normalized to the length of 1.
            `owner`: A Player
                The owner of the Bullet
        Returns:
            A list of GameObjects:
                Returns an empty list if the shooting was not successful.
                Otherwise returns a list containing the fired Bullet.
        """
        if self._timer.expired():
            owner.add_shot_fired()
            self._timer.start()
            bullet_location = location + self._spawn_offset * front
            bullet_velocity = velocity + self._speed * front
            bullet_front = Vector2(front)
            return [self._bullet_factory.bullet(
                bullet_location, bullet_velocity, bullet_front, owner)]
        return []


class GameObject:
    """Base class for game objects.

    All game objects should implement the interface defined by this

    Attributes:
        shape: a Shape class object
        graphic: a Graphic class object
        owner: a Player class object or None
        collision_damage: A non-negative scalar
            The damage done by `self` to other GameObject when colliding
        """

    def __init__(self, shape, graphic, owner, collision_damage):
        """Initializes a new GameObject"""
        self.shape = shape
        self.graphic = graphic
        self.owner = owner
        self.collision_damage = collision_damage

    def alive(self):
        """Returns True if `self` is alive"""
        return True

    def collide(self, other):
        """Collides `other` to `self`.

        Arguments:
            other: a GameObject class object

        Does not modify the state of `other`"""
        pass

    def update(self, delta_time):
        """Updates the state of `self`.

        Arguments:
            delta_time: a non-negative scalar
        """

        pass

    def new_objects(self):
        """Returns the new GameObjects created by `self`.

        Only returns the objects created since last `new_objects` call.

        Returns: A list of GameObjects

        NOTE: also returns `self` if `self` should still exist in the game
        object pool"""
        return [self]


class Plane(GameObject):
    """Class for Planes.

    Attributes:
        plane_physics: A PhysicsController class object
            The object responsible for moving the plane
        gun: A Gun class object
        score_generator: A function (damage, destroyed) -> float
            A function returning the score given to the owner of some
            other game object when the other game object damages `self`
            with `damage`. If `destroyed` == True, assumes `self` was
            destroyed and stayed alive otherwise.
        health: A scalar
            The remaining health of the plane

    """

    def __init__(self, shape, graphic, plane_physics, gun, score_generator,
                 owner, health, collision_damage):
        """Initializes Plane


        Arguments:
            shape: A Shape class object
                The object responsible for calculating the collisions
            graphic: A Graphic class object
                The object responsible for drawing the plane
            plane_physics: A PhysicsController class object
                The object responsible for moving the plane
            gun: A Gun class object
            score_generator: A function (damage, destroyed) -> float
                A function returning the score given to the owner of some
                other game object when the other game object damages `self`
                with `damage`. If `destroyed` == True, assumes `self` was
                destroyed and stayed alive otherwise.
            owner: A Player class object or None
                The owner of the plane
            health: A positive scalar
                The initial health of the plane
            collision_damage: A non-negative scalar
                The damage that the plane does to other game objects
                when colliding
            """
        super().__init__(shape, graphic, owner, collision_damage)

        self.plane_physics = plane_physics
        self.gun = gun
        self.score_generator = score_generator
        self.health = health

        self._new_objects = []
        self._update_locations()

    def up(self):
        """Turns plane upwards"""
        self.plane_physics.up()

    def down(self):
        """Turns plane downwards"""
        self.plane_physics.down()

    def accelerate(self):
        """Accelerates the plane to the direction it is facing"""
        self.plane_physics.accelerate()

    def shoot(self):
        """Shoots a bullet

        Requests self.gun to shoot a bullet."""
        self._new_objects.extend(
            self.gun.shoot(self.plane_physics.location, self.plane_physics.velocity,
                           self.plane_physics.front, self.owner))

    def alive(self):
        return self.health > 0

    def collide(self, other):
        """Collides `other` to `self`.

        Damages `self` but doesn't modify `other`.
        Gives the owner of `other` the appropriate reward."""
        if not self.alive():
            return

        damage_taken, destroyed = self._damage(other.collision_damage)
        if other.owner is not None:
            other.owner.process_reward(self.score_generator(
                damage_taken, destroyed), self.owner)

            if destroyed:
                other.owner.add_kill(self.owner)

    def _damage(self, amount):
        if not self.alive():
            return (0, False)

        damage_taken = min(amount, self.health)
        self.health -= damage_taken
        destroyed = False
        if not self.alive():
            destroyed = True

        return damage_taken, destroyed

    def update(self, delta_time):
        """See base class"""
        if not self.alive():
            return

        self.gun.update(delta_time)
        self.plane_physics.update(delta_time)

        self._update_locations()

    def _update_locations(self):
        self.graphic.location = Vector2(self.plane_physics.location)
        self.graphic.rotation = - \
            math.radians(self.plane_physics.front.as_polar()[1])

        self.shape.location = Vector2(self.plane_physics.location)
        self.shape.rotation = - \
            math.radians(self.plane_physics.front.as_polar()[1])

    def new_objects(self):
        """See base class"""
        if not self.alive():
            return []
        tmp = self._new_objects
        self._new_objects = []
        tmp.append(self)

        return tmp


class Bullet(GameObject):
    """Class for Bullets.

    Attributes:
        physics: An object implementing BasePhysics interface
            The object responsible for moving the bullet
        health: A scalar
            The remaining health of the bullet
    """

    def __init__(self, shape, graphic, physics, owner, timer, health=100,
                 collision_damage=100):
        """Initializes the bullet.

        Arguments:
            shape: A Shape class object
                The object responsible for calculating the collisions
            graphic: A Graphic class object
                The object responsible for drawing the bullet
            physics: A PhysicsController class object
                The object responsible for moving the bullet
            owner: A Player class object or None
                The owner of the bullet
            health: A positive scalar
                The initial health of the bullet
            collision_damage: A non-negative scalar
                The damage that the bullet does to other game objects
                when colliding
            timer: A Timer class object
                The bullet will disappear when the timer expires.
        """

        super().__init__(shape, graphic, owner, collision_damage)
        self.physics = physics
        self.timer = timer
        self.health = health

        self._update_locations()

    def alive(self):
        return self.health > 0

    def collide(self, other):
        """Collides `other` to `self`.

        Damages `self` but doesn't modify `other`."""
        if not self.alive:
            return

        damage_taken = min(other.collision_damage, self.health)
        self.health -= damage_taken

    def update(self, delta_time):
        """See base class"""

        if not self.alive():
            return

        self.timer.update(delta_time)
        if self.timer.expired():
            self.health = 0

        self.physics.update(delta_time)
        self._update_locations()

    def new_objects(self):
        """See base class"""
        if not self.alive():
            return []

        return [self]

    def _update_locations(self):
        self.graphic.location = Vector2(self.physics.location)
        self.graphic.rotation = -math.radians(self.physics.front.as_polar()[1])

        self.shape.location = Vector2(self.physics.location)
        self.shape.rotation = -math.radians(self.physics.front.as_polar()[1])


class Ground(GameObject):
    """A class for ground"""

    def __init__(self, shape, graphic, owner=None, collision_damage=100):
        """See base class"""
        super().__init__(shape, graphic, owner, collision_damage)
