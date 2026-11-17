"""Stage 1 튜토리얼과 Stage 2~4의 기본 모드 구조."""

import os

from pico2d import SDLK_ESCAPE, SDL_KEYDOWN, SDL_KEYUP, draw_rectangle, load_image

import game_framework
from player import Player


class StageBase:
    ground_y = 105

    def __init__(self):
        self.player = None
        self.held_keys = set()

    def init(self):
        self.player = Player(150, self.ground_y)

    def finish(self):
        self.player = None

    def handle_events(self, events):
        for event in events:
            if event.type == SDL_KEYDOWN:
                if event.key == SDLK_ESCAPE:
                    game_framework.quit()
                self.held_keys.add(event.key)
                self.player.handle_key_down(event.key)
            elif event.type == SDL_KEYUP:
                self.held_keys.discard(event.key)
                self.player.handle_key_up(event.key)

    def update(self):
        self.player.update(1.0 / 60.0, self.held_keys, min_x=35, max_x=1245)

    def draw(self):
        draw_rectangle(0, 0, game_framework.SCREEN_WIDTH, self.ground_y)
        draw_rectangle(0, self.ground_y, game_framework.SCREEN_WIDTH, game_framework.SCREEN_HEIGHT)
        self.player.draw()


class Rock:
    """Stage 1 PART 2의 평평한 바위 플랫폼."""

    # 원본 바위의 16:9 비율을 유지하면서 현재 점프 높이로 착지 가능하게 조정한다.
    WIDTH = 196
    HEIGHT = 110
    COLLISION_HEIGHT = 84
    DRAW_BOTTOM_OFFSET = 5

    def __init__(self, image, center_x, ground_y):
        self.image = image
        self.left = center_x - self.WIDTH / 2
        self.right = center_x + self.WIDTH / 2
        self.top = ground_y + self.COLLISION_HEIGHT
        self.bottom = ground_y

    def draw(self):
        draw_bottom = self.bottom - self.DRAW_BOTTOM_OFFSET
        self.image.draw(
            (self.left + self.right) / 2,
            draw_bottom + self.HEIGHT / 2,
            self.WIDTH,
            self.HEIGHT,
        )

    def contains_x(self, x, half_width=26):
        return self.left - half_width < x < self.right + half_width


class Bush:
    """PART 2에서 E키로 숨기 애니메이션을 재생하는 덤불."""

    WIDTH = 330
    HEIGHT = 160
    COLUMNS = 4
    ROWS = 2
    FRAME_INTERVAL = 0.1

    def __init__(self, static_image, animation_image, center_x, ground_y):
        self.static_image = static_image
        self.animation_image = animation_image
        self.x = center_x
        self.ground_y = ground_y
        self.frame = 0
        self.frame_time = 0.0
        self.direction = 1
        self.animating = False
        self.hidden = False

    def can_interact(self, player_x):
        return abs(player_x - self.x) <= 150

    def toggle_visibility(self):
        if self.animating:
            return
        if self.hidden:
            self.animating = True
            self.frame = self.COLUMNS * self.ROWS - 1
            self.frame_time = 0.0
            self.direction = -1
        else:
            self.animating = True
            self.frame = 0
            self.frame_time = 0.0
            self.direction = 1

    def update(self, dt):
        if not self.animating:
            return
        self.frame_time += dt
        if self.frame_time < self.FRAME_INTERVAL:
            return
        self.frame_time -= self.FRAME_INTERVAL
        self.frame += self.direction
        if self.frame >= self.COLUMNS * self.ROWS:
            self.frame = self.COLUMNS * self.ROWS - 1
            self.animating = False
            self.hidden = True
        elif self.frame < 0:
            self.frame = 0
            self.animating = False
            self.hidden = False

    def draw(self):
        if not self.animating:
            self.static_image.draw(self.x, self.ground_y + self.HEIGHT / 2, self.WIDTH, self.HEIGHT)
            return
        column = self.frame % self.COLUMNS
        row = self.frame // self.COLUMNS
        left = column * self.animation_image.w // self.COLUMNS
        right = (column + 1) * self.animation_image.w // self.COLUMNS
        top = self.animation_image.h - row * self.animation_image.h // self.ROWS
        bottom = self.animation_image.h - (row + 1) * self.animation_image.h // self.ROWS
        self.animation_image.clip_composite_draw(
            left,
            bottom,
            right - left,
            top - bottom,
            0,
            "",
            self.x,
            self.ground_y + self.HEIGHT / 2,
            self.WIDTH,
            self.HEIGHT,
        )


class Stage1(StageBase):
    """공용 숲 배경을 사용하는 Movement/Action 튜토리얼."""

    PART_MOVEMENT = 1
    PART_ACTION = 2
    BACKGROUND_NAME = "stage1_forest_color_matched.png"
    MOVEMENT_UI_NAME = "ui_movement_compact.png"
    ACTION_UI_NAME = "ui_actions_compact.png"
    ROCK_NAME = "tutorial_flat_top_rock.png"
    BUSH_NAME = "bush_compact_fixed_330x160.png"
    BUSH_ANIMATION_NAME = "bush_hide_bright_8frames_4x2_330x160.png"

    def __init__(self):
        super().__init__()
        self.part = self.PART_MOVEMENT
        self.part_transitioned = False
        self.background = None
        self.movement_ui = None
        self.action_ui = None
        self.rock = None
        self.bush = None
        self.scale = 1.0
        self.background_left = 0.0
        self.background_bottom = 0.0
        self.interaction_requested = False

    def init(self):
        root = os.path.dirname(__file__)
        self.background = load_image(os.path.join(root, self.BACKGROUND_NAME))
        self.movement_ui = load_image(os.path.join(root, self.MOVEMENT_UI_NAME))
        self.action_ui = load_image(os.path.join(root, self.ACTION_UI_NAME))
        rock_image = load_image(os.path.join(root, self.ROCK_NAME))
        bush_image = load_image(os.path.join(root, self.BUSH_NAME))
        bush_animation_image = load_image(os.path.join(root, self.BUSH_ANIMATION_NAME))
        self.scale = min(
            game_framework.SCREEN_WIDTH / self.background.w,
            game_framework.SCREEN_HEIGHT / self.background.h,
        )
        self.background_left = (
            game_framework.SCREEN_WIDTH - self.background.w * self.scale
        ) / 2
        self.background_bottom = (
            game_framework.SCREEN_HEIGHT - self.background.h * self.scale
        ) / 2
        self.player = Player(150, self.ground_y)
        self.rock = Rock(rock_image, 720, self.ground_y)
        self.bush = Bush(bush_image, bush_animation_image, 1010, self.ground_y)

    def handle_events(self, events):
        super().handle_events(events)
        if self.player.consume_interaction():
            self.interaction_requested = True

    def update(self):
        self.bush.update(1.0 / 60.0)
        if self.interaction_requested:
            if self.part == self.PART_ACTION and self.bush.can_interact(self.player.x):
                self.bush.toggle_visibility()
            self.interaction_requested = False
        previous_y = self.player.y
        self._prepare_support_surface()
        if not self.bush.animating:
            self.player.update(1.0 / 60.0, self.held_keys, min_x=35, max_x=1270)
        self._resolve_rock_collision(previous_y)
        if (
            self.part == self.PART_MOVEMENT
            and self.player.collision_box[2] >= game_framework.SCREEN_WIDTH
            and not self.part_transitioned
        ):
            self._enter_action_part()

    def _prepare_support_surface(self):
        if self.part != self.PART_ACTION or self.rock is None:
            self.player.ground_y = self.ground_y
            return
        on_rock = self.rock.contains_x(self.player.x)
        if self.player.on_ground and on_rock and self.player.y >= self.rock.top - 1:
            self.player.ground_y = self.rock.top
        elif self.player.on_ground and self.player.y > self.ground_y:
            self.player.on_ground = False
            self.player.ground_y = self.ground_y
        else:
            self.player.ground_y = self.ground_y

    def _resolve_rock_collision(self, previous_y):
        if self.part != self.PART_ACTION or self.rock is None:
            return
        rock = self.rock
        player = self.player
        if (
            not player.on_ground
            and player.velocity_y <= 0
            and previous_y >= rock.top
            and player.y <= rock.top
            and rock.contains_x(player.x)
        ):
            player.y = rock.top
            player.ground_y = rock.top
            player.velocity_y = 0.0
            player.on_ground = True
            return

        box_left, box_bottom, box_right, box_top = player.collision_box
        overlaps_height = box_top > rock.bottom and box_bottom < rock.top
        overlaps_width = box_right > rock.left and box_left < rock.right
        if overlaps_height and overlaps_width:
            if player.x < (rock.left + rock.right) / 2:
                player.x = rock.left - 26
            else:
                player.x = rock.right + 26

    def _enter_action_part(self):
        self.part_transitioned = True
        self.part = self.PART_ACTION
        self.player.x = 80
        self.player.y = self.ground_y
        self.player.ground_y = self.ground_y
        self.player.on_ground = True
        self.player.velocity_y = 0.0
        self.held_keys.clear()

    def draw(self):
        self.background.draw(
            self.background_left + self.background.w * self.scale / 2,
            self.background_bottom + self.background.h * self.scale / 2,
            self.background.w * self.scale,
            self.background.h * self.scale,
        )
        if self.part == self.PART_ACTION and self.rock is not None:
            self.rock.draw()
        if self.part == self.PART_ACTION and self.bush is not None:
            self.bush.draw()
        if self.bush is None or (not self.bush.animating and not self.bush.hidden):
            self.player.draw()
        if self.part == self.PART_MOVEMENT:
            self.movement_ui.draw(1100, 535, 260, 310)
        else:
            self.action_ui.draw(1100, 535, 273, 242)


class Stage2(StageBase):
    pass


class Stage3(StageBase):
    pass


class Stage4(StageBase):
    pass
