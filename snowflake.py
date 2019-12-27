'''
Draw mirrored snowflakes!
'''
from __future__ import annotations

# === IMPORTS ===
import math
import sys
from typing import Tuple, Dict
import pygame

# === CONSTANTS ===
# Program constants
FRAME_RATE = 60
CAPTION = "Snowflake Mirror Generator"
SCREEN_WIDTH = 800 
SCREEN_HEIGHT = 650
# Maths constants
RADIANS_IN_CIRCLE = 2 * math.pi
CARTESIAN_ORIGIN = (0, SCREEN_HEIGHT)
CARTESIAN_SIGNS = (1, -1)
# Visual constants:
# - General
BACKGROUND_COLOR = (124, 124, 154)
SNOWFLAKE_COLOR = (64, 64, 255)
LINE_THICKNESS = 4
ALTERNATE_THICKNESS = 2
# - Snowflake segment
SNOWFLAKE_SEGMENT_RADIUS = 200
SNOWFLAKE_SEGMENT_POSITION = (210, 325)
ALTERNATE_SNOWFLAKE_COLOR = (24, 24, 100)
VALID_SIZES = (2, 4, 6, 8, 10, 12)
# - Snowflake
SNOWFLAKE_RADIUS = 150
SNOWFLAKE_POSITION = (600, 325)
ROTATION_SPEED = -0.008
# - UI
FONT_SIZE = 30
ANTIALIAS_FONT = True
UI_BASIC = "Draw within the bounds of the slice. Press Delete to clear the snowflake."
UI_MIRROR = "Mirror mode: {} (Press M to toggle)"
UI_ROTATE = "Rotation: {} (Press R to toggle)"
UI_SLICE = "Slices per snowflake: {} (Press Tab to change)"
UI_BASIC_POSITION = (40,40)
UI_MIRROR_POSITION = (0,0)
UI_ROTATE_POSITION = (0,0)
UI_SLICE_POSITION = (40, SCREEN_HEIGHT - 70)
UI_Y_0 = 0
UI_Y_1 = 550
# Defaults
DEFAULT_SIZE = 6
DEFAULT_MIRROR = True

# === METHODS ===
def to_rectangular(
    theta: int, 
    radius: int, 
    *, 
    polar_origin: Tuple[int, int]=(0,0), 
    cartesian_origin: Tuple[int,int]=CARTESIAN_ORIGIN,
    cartesian_signs: Tuple[int,int]=CARTESIAN_SIGNS) -> Tuple[int, int]:
    '''
    Returns the rectangular coordinate associated with the polar coordinate.
    '''
    # Convert polar to rectangular
    relative_x = radius * math.cos(theta)
    relative_y = radius * math.sin(theta)
    # Shift according to polar origin
    polar_x, polar_y = polar_origin
    relative_x = polar_x + relative_x
    relative_y = polar_y + relative_y
    # Shift according to cartesian origin & signs
    cartesian_x, cartesian_y = cartesian_origin
    sign_x, sign_y = cartesian_signs
    relative_x = sign_x * relative_x + cartesian_x
    relative_y = sign_y * relative_y + cartesian_y
    # Convert to int
    x, y = int(relative_x), int(relative_y)
    # Return value
    return (x, y)

# === CLASSES ===
class PolarPoint:
    '''
    A point representing a polar coordinate.

    Angles are stored in radians in the interval [0, 2 * pi).
    '''
    theta: float
    radius: float

    @classmethod
    def from_rectangular(
            cls,
            point: Tuple[int, int],
            *,
            origin: Tuple[int, int] = (0, 0)
        ) -> PolarPoint:
        '''
        Converts the given rectangular coordinate into polar form.

        The optional origin parameter can be used to determine the zero position.

        Returns the polar coordinate.
        '''
        # Get rectangular coordinates relative to the origin
        raw_x, raw_y = point
        origin_x, origin_y = origin
        relative_x = raw_x - origin_x
        relative_y = raw_y - origin_y

        # Convert from rectangular to polar coordinates:
        # Calculate the radius
        # r = \sqrt{ x^2 + y^2 }
        radius = math.hypot(relative_x, relative_y)
        # Calculate the angle, in radians
        # \theta = atan2(\frac{y}{x})
        theta_radians = math.atan2(relative_y, relative_x)
        # Convert from the interval [-pi, pi) into the interval [0,2 * pi)
        theta = theta_radians % RADIANS_IN_CIRCLE

        # Return a polar point
        return PolarPoint(radius, theta)

    def __init__(self, radius: float, theta: float) -> PolarPoint:
        '''
        Initializes a point in polar geometry, with coordinate (theta, radius).
        '''
        self.radius = radius
        self.theta = theta

    def __hash__(self) -> int:
        '''
        Hashing is equivalent to hashing tuple([theta, radius]).
        '''
        return hash((self.theta, self.radius))

    def __str__(self) -> str:
        '''
        Returns (theta, radius).
        '''
        return f"({self.theta}, {self.radius})"

class SnowflakeSegment:
    '''
    A segment of a snowflake. Used for drawing a snowflake.
    '''
    origin: Tuple[int, int]
    x: int
    y: int
    radius: float
    size: int
    centered_angle: float

    def __init__(
            self,
            *,
            radius: float = 1,
            size: int = DEFAULT_SIZE,
            origin: Tuple[int, int] = (0, 0),
            centered_angle: float = 0
        ) -> SnowflakeSegment:
        '''
        Initializes the snowflake input segment.
        '''
        self.radius = radius
        self.size = size
        self.origin = origin
        self.x, self.y = origin
        self.centered_angle = centered_angle

    def contains_point(self, point: PolarPoint) -> bool:
        '''
        Determines whether the given rectangular point is within the area encompassed by the segment.

        Points on the edge of the segment are considered inside the segment.

        Returns True if true, False otherwise.
        '''
        # What angled points are stored within the segment?
        angle_arc = RADIANS_IN_CIRCLE / self.size
        angle_begin = RADIANS_IN_CIRCLE - (angle_arc / 2)
        angle_end = angle_arc / 2

        # If the angle is not within the arc of the segment
        if point.theta < angle_begin and point.theta > angle_end:
            return False

        # If the radius is outside the radius of our segment
        if point.radius > self.radius or point.radius < 0:
            return False

        # Otherwise, return True
        return True

    def get_region(self, *, update: bool = True) -> pygame.Rect:
        '''
        Returns the dirty region that encompasses the segment.
        
        This is used for screen updates and background drawing.
        '''
        # The bounds of the box
        x_1, origin_y = self.origin

        # Largest size of the updating ones
        current_size = VALID_SIZES.index(self.size)
        current_size -= 1
        current_size %= len(VALID_SIZES)
        min_size = min(self.size, VALID_SIZES[current_size])

        # Height of the box
        arc = RADIANS_IN_CIRCLE / (min_size)
        height = math.sin(arc / 2) * self.radius
        y_1 = origin_y - height
        
        # Positions if updating
        if update:
            x_2 = x_1 + self.radius
            y_2 = origin_y + height
        # Distances if drawing
        else:
            x_2 = self.radius
            y_2 = height * 2

        # Avoid pixel-wide lines
        x_1 -= LINE_THICKNESS
        y_1 -= LINE_THICKNESS
        x_2 += LINE_THICKNESS * 2 # Double to account for what we've already adjusted in the opposite direction
        y_2 += LINE_THICKNESS * 2

        # The box
        return pygame.Rect(x_1, y_1, x_2, y_2)

    def draw_outline(self, surface:pygame.surface) -> None:
        '''
        Draws the snowflake segment onto the given pygame surface.

        Returns the area changed.

        Position, size, etc. are controlled by constants.
        '''
        # Used to calculate circular sections
        x,y,radius = self.x, self.y, self.radius
        half_arc = RADIANS_IN_CIRCLE / self.size / 2
        # The error margin
        epsilon = 0.01
        # The greyed out circle outline
        pygame.draw.circle(
            surface,
            ALTERNATE_SNOWFLAKE_COLOR,
            (x,y),
            radius,
            ALTERNATE_THICKNESS
        )
        # The arc of the outline
        pygame.draw.arc(
            surface, 
            ALTERNATE_SNOWFLAKE_COLOR,
            (x - radius, y - radius, 2 * radius, 2 * radius), 
            self.centered_angle - half_arc - epsilon,
            self.centered_angle + half_arc + epsilon, 
            LINE_THICKNESS
        )
        # The lines of the outline
        pygame.draw.line(
            surface,
            ALTERNATE_SNOWFLAKE_COLOR,
            self.origin,
            to_rectangular(
                self.centered_angle - half_arc,
                self.radius,
                polar_origin=self.origin,
            ),
            LINE_THICKNESS
        )
        pygame.draw.line(
            surface,
            ALTERNATE_SNOWFLAKE_COLOR,
            self.origin,
            to_rectangular(
                self.centered_angle + half_arc,
                self.radius,
                polar_origin=self.origin
            ),
            LINE_THICKNESS
        )

class Snowflake:
    '''
    A complete snowflake.
    '''
    origin: Tuple[int, int]
    x: int
    y: int
    radius: float
    size: int
    mirror: bool # True if you wish to mirror each segment instead of just cloning
    pixels: Dict[PolarPoint, int]

    _current_angle: float

    def __init__(
            self,
            *,
            radius: float = 1,
            size: int = 2,
            origin: Tuple[int, int] = (0, 0),
            mirror: bool = False,
        ) -> Snowflake:
        '''
        Initializes the animated snowflake.

        If mirror is False, segments will be cloned instead of mirrored
        '''
        self.radius = radius
        self.size = size
        self.origin = origin
        self.x, self.y = origin
        self.mirror = mirror
        # Data
        self.pixels = {}
        # Internals
        self._current_angle = 0
    
    def set_pixel(self, point: PolarPoint, value: int) -> None:
        '''
        Sets a pixel value. 

        A value of 0 is blank, while 1 is light blue.
        '''
        self.pixels[point] = value

    def clear_pixels(self) -> None:
        '''
        Clears all pixel data.
        '''
        self.pixels = {}

    def clear_pixels_outside(self, segment:SnowflakeSegment) -> None:
        '''
        Clears all pixels not inside the bounds of the given segment.
        '''
        # Pixels to discard
        to_delete = []
        # Check through each pixel
        for pixel in self.pixels:
            # Adjust radii
            real_radius = pixel.radius * segment.radius / self.radius
            point = PolarPoint(real_radius, pixel.theta)
            # Everything outside the segment
            if not segment.contains_point(point):
                to_delete.append(pixel)
        # Shave off the outside pixels
        for pixel in to_delete:
            self.pixels.pop(pixel)

    def rotate(self, angle: float) -> None:
        '''
        Rotates the snowflake by the given amount, in radians.

        Positive input rotates counterclockwise, and negative input rotates clockwise.
        '''
        self._current_angle += angle 
        self._current_angle %= RADIANS_IN_CIRCLE

    def get_region(self, *, update: bool = True) -> pygame.Rect:
        '''
        Returns the dirty region that encompasses the snowflake.
        
        This is used for screen updates and background drawing.
        '''
        # The bounds of the box
        origin_x, origin_y = self.origin
        x_1, y_1 = origin_x - self.radius, origin_y - self.radius
        # The second pair is coordinates if updating regions,
        if update:
            x_2, y_2 = origin_x + self.radius, origin_y + self.radius
        # and distances if drawing.
        else:
            x_2 = y_2 = self.radius * 2

        # Avoid pixel-wide lines
        x_1 -= LINE_THICKNESS
        y_1 -= LINE_THICKNESS
        x_2 += LINE_THICKNESS * 2
        y_2 += LINE_THICKNESS * 2
        
        # The box
        return pygame.Rect(x_1, y_1, x_2, y_2)
    
    def draw_outline(self, surface:pygame.surface) -> None:
        '''
        Draws the snowflake onto the given pygame surface.

        Visual paramaters (color, etc.) are controlled by constants.
        '''
        # Draw the snowflake outline
        pygame.draw.circle(
            surface,
            SNOWFLAKE_COLOR,
            self.origin,
            self.radius,
            ALTERNATE_THICKNESS
        )
    
    def draw_segment(self, surface: pygame.Surface, segment:SnowflakeSegment) -> pygame.Rect:
        '''
        Draw the pixel data on the given snowflake segment.
        '''
        # Draw the pixels
        for pixel,value in self.pixels.items():
            # Account for different radii
            real_radius = \
                pixel.radius * segment.radius / self.radius
            # Get the rectangular pixel value, in ints according to our origin
            x,y = to_rectangular(
                pixel.theta,
                real_radius, 
                polar_origin=segment.origin
            )
            
            # Set the color
            color = SNOWFLAKE_COLOR if value == 1 else BACKGROUND_COLOR

            # Draw the pixel on the surface
            pygame.draw.circle(
                surface,
                color,
                (x, y),
                LINE_THICKNESS
            )
    
    def draw_pixels(self, surface: pygame.Surface) -> None:
        '''
        Draws the pixel data of the snowflake.
        '''
        # Draw the pixels
        for pixel,value in self.pixels.items():
            # Radius from the origin
            radius = pixel.radius
            # The angle of a single slice
            arc = RADIANS_IN_CIRCLE / self.size
            # For each segment:
            for i in range(self.size):
                # Determine where to place the segment
                # If we're set to mirroring mode
                if self.mirror:
                    if i % 2 == 0:
                        real_theta = i * arc + pixel.theta
                    else:
                        real_theta = (i) * arc - pixel.theta
                # If we're set to cloning mode
                else:
                    # Rotate by one segment's worth per segment
                    real_theta = i * arc + pixel.theta
                # Rotate the point by the current angle
                real_theta += self._current_angle
                
                # Get the rectangular pixel value, in ints according to our origin
                x,y = to_rectangular(real_theta, radius, polar_origin=self.origin)
                
                # Set the color
                color = SNOWFLAKE_COLOR if value == 1 else BACKGROUND_COLOR

                # Draw the pixel on the surface
                pygame.draw.circle(
                    surface,
                    color,
                    (x, y),
                    LINE_THICKNESS
                )

# === MAIN PROGRAM ===
def main() -> int:
    '''
    The main program
    '''
    pygame.init()

    # Set program caption
    pygame.display.set_caption(CAPTION)

    # Set the screen size
    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Control the main loop
    running = True
    clock = pygame.time.Clock()

    # Control the behavior of the snowflakes
    rotate = True
    
    # Control screen updates
    update_cursor = False
    update_flake = False
    update_segment = False
    update_UI = True

    # Get the default system font
    font = pygame.font.SysFont(
        pygame.font.get_default_font(),
        FONT_SIZE
    )

    # Our "snowflakes"
    segment = SnowflakeSegment(
        radius=SNOWFLAKE_SEGMENT_RADIUS,
        size=DEFAULT_SIZE,
        origin=SNOWFLAKE_SEGMENT_POSITION
    )
    snowflake = Snowflake(
        radius=SNOWFLAKE_RADIUS,
        size=DEFAULT_SIZE,
        origin=SNOWFLAKE_POSITION,
        mirror=DEFAULT_MIRROR
    )

    # Draw the initial state
    surface.fill(BACKGROUND_COLOR)
    segment.draw_outline(surface)
    snowflake.draw_outline(surface)
    # Update the display with this
    pygame.display.flip()

    # Main loop
    while running:
        # === EVENT HANDLER ===
        # Get everything from the event queue
        for event in pygame.event.get():
            # If the event tells the program to quit
            if event.type == pygame.QUIT:
                # This exits the main loop naturally
                running = False
            # Key presses:
            elif event.type == pygame.KEYDOWN:
                # R key
                if event.key == pygame.K_r:
                    # Toggle rotation
                    rotate = not rotate
                # M key
                if event.key == pygame.K_m:
                    # Toggle mirroring
                    snowflake.mirror = not snowflake.mirror
                    update_flake = True
                # Tab key
                elif event.key == pygame.K_TAB:
                    # Cycle between valid sizes
                    current_size = VALID_SIZES.index(snowflake.size)
                    current_size += 1
                    current_size %= len(VALID_SIZES)
                    # Set the segment size
                    snowflake.size = VALID_SIZES[current_size]
                    segment.size = VALID_SIZES[current_size]
                    # Delete any pixels outside the new segment
                    snowflake.clear_pixels_outside(segment)
                    # Schedule to update
                    update_segment = True
                    update_flake = True
                    update_UI = True
                # Any delete key
                elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                    # Clear the snowflake
                    snowflake.clear_pixels()
                    update_segment = True
                    update_flake = True
        
        # === CURSOR LOGIC ===
        # Get mouse state
        MB1,_MB2,_MB3 = pygame.mouse.get_pressed()
        # If mouse button 1 (left click) is down:
        if MB1:
            # Get mouse position
            mouse_x,mouse_y = pygame.mouse.get_pos()
            # Flip the Y position, to set the origin to the bottom left
            # corner instead of the top left corner
            mouse_y = SCREEN_HEIGHT - mouse_y
            # Convert to polar coordinates
            polar_position = PolarPoint.from_rectangular(
                (mouse_x, mouse_y),
                origin=segment.origin
            )
            # Check if we are in our "drawing zone"
            if segment.contains_point(polar_position):
                # Adjust the radius to fit inside the output snowflake
                polar_position.radius *= \
                    snowflake.radius / segment.radius
                # Add the point to our snowflake
                snowflake.set_pixel(polar_position, 1)
                # Schedule these for updating
                update_flake = True
                cursor_position = (mouse_x, SCREEN_HEIGHT - mouse_y)
                update_cursor = True

        # === UI ===
        # Draw each of the texts
        if update_UI:
            # Background
            bottom_UI = pygame.Rect(
                0, 
                UI_Y_1, 
                SCREEN_WIDTH, 
                SCREEN_HEIGHT - UI_Y_1
            )
            pygame.draw.rect(
                surface,
                BACKGROUND_COLOR,
                bottom_UI
            )
            # Basic text
            basic_surface = font.render(
                UI_BASIC,
                ANTIALIAS_FONT,
                ALTERNATE_SNOWFLAKE_COLOR,
                BACKGROUND_COLOR
            )
            surface.blit(
                basic_surface,
                UI_BASIC_POSITION
            )
            # Slice text
            slice_surface = font.render(
                UI_SLICE.format(snowflake.size),
                ANTIALIAS_FONT,
                ALTERNATE_SNOWFLAKE_COLOR,
                BACKGROUND_COLOR
            )
            surface.blit(
                slice_surface,
                UI_SLICE_POSITION
            )

        # === OUTPUT LOGIC ===
        # Rotate our final snowflake
        if rotate:
            snowflake.rotate(ROTATION_SPEED)
            # Schedule the whole flake region for a screen update
            update_flake = True
        
        # === DRAW ===
        # If the whole flake needs to be redrawn
        if update_flake:
            # Draw the background
            flake_region = snowflake.get_region(update=False)
            pygame.draw.rect(
                surface,
                BACKGROUND_COLOR,
                flake_region
            )
            # Draw the full snowflake
            snowflake.draw_outline(surface)
            snowflake.draw_pixels(surface)
        # If the whole segment needs to be redrawn
        if update_segment:
            # Draw the background
            segment_region = segment.get_region(update=False)
            pygame.draw.rect(
                surface,
                BACKGROUND_COLOR,
                segment_region
            )
            # Draw the snowflake input slice
            segment.draw_outline(surface)
            snowflake.draw_segment(surface, segment)
        # If only the cursor needs to be redrawn
        if update_cursor:
            # Draw the cursor and get its dirty region
            cursor_region = pygame.draw.circle(
                surface,
                SNOWFLAKE_COLOR,
                cursor_position,
                LINE_THICKNESS
            )

        # === CLEANUP ===
        # Update the dirty sections
        if update_flake:
            # Toggle
            update_flake = False
            # Update the flake region
            flake_region = snowflake.get_region()
            pygame.display.update(flake_region)
        if update_segment:
            # Toggle
            update_segment = False
            # Update the segment region
            segment_region = segment.get_region()
            pygame.display.update(segment_region)
        if update_cursor:
            # Toggle
            update_cursor = False
            # Update the cursor region
            pygame.display.update(cursor_region)
        if update_UI:
            # Toggle
            update_UI = False
            pygame.display.flip()
        
        # Tick our clock 
        clock.tick(FRAME_RATE)

    # Exit out of pygame, so we do not leave behind unresponsive tasks
    pygame.quit()
    # We return with a code of 0: we did not encounter an error
    return 0

# Runs only in the main thread
if __name__ == "__main__":
    # Returns once pygame exits
    RETURN_CODE = main()
    sys.exit(RETURN_CODE)
