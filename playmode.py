"""Stage 1 튜토리얼과 Stage 2~4의 기본 모드 구조."""

import os

from pico2d import (
    SDLK_e,
    SDLK_ESCAPE,
    SDLK_r,
    SDL_KEYDOWN,
    SDL_KEYUP,
    draw_rectangle,
    load_image,
)

import game_framework
from player import Player, PlayerState


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
        elif (
            self.part == self.PART_ACTION
            and self.player.collision_box[2] >= game_framework.SCREEN_WIDTH
        ):
            from playmode import Stage2

            game_framework.change_mode(Stage2())

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


class Platform:
    def __init__(self, left, right, top, image=None, width=0, height=0, center_x=0):
        self.left = left
        self.right = right
        self.top = top
        self.image = image
        self.width = width
        self.height = height
        self.center_x = center_x or (left + right) / 2

    def draw(self):
        if self.image is not None:
            self.image.draw(self.center_x, self.top - self.height / 2, self.width, self.height)

    def supports(self, x):
        return self.left - 26 < x < self.right + 26


class FlowerPlatform(Platform):
    """꽃 발판 리소스가 추가되면 image를 연결할 수 있는 개폐 발판."""

    PERIOD = 1.6
    OPEN_TIME = 0.8

    def __init__(self, left, right, top):
        super().__init__(left, right, top)
        self.time = 0.0

    @property
    def opened(self):
        return self.time % self.PERIOD < self.OPEN_TIME

    def update(self, dt):
        self.time += dt


class MushroomPlatform(Platform):
    COLUMNS = 4
    ROWS = 2

    def __init__(self, image, center_x, top):
        super().__init__(center_x - 75, center_x + 75, top, image, 170, 100, center_x)
        self.frame = 0
        self.frame_time = 0.0
        self.bouncing = False

    def update(self, dt):
        if not self.bouncing:
            return
        self.frame_time += dt
        if self.frame_time >= 0.1:
            self.frame = (self.frame + 1) % (self.COLUMNS * self.ROWS)
            self.frame_time = 0.0
            if self.frame == 0:
                self.bouncing = False

    def bounce(self):
        self.bouncing = True
        self.frame = 4
        self.frame_time = 0.0

    def draw(self):
        column = self.frame % self.COLUMNS
        row = self.frame // self.COLUMNS
        left = round(column * self.image.w / self.COLUMNS)
        right = round((column + 1) * self.image.w / self.COLUMNS)
        top = self.image.h - round(row * self.image.h / self.ROWS)
        bottom = self.image.h - round((row + 1) * self.image.h / self.ROWS)
        self.image.clip_composite_draw(
            left,
            bottom,
            right - left,
            top - bottom,
            0,
            "",
            self.center_x,
            self.top - self.height / 2,
            self.width,
            self.height,
        )


class FlowerBeast:
    COLUMNS = 8
    ROWS = 3
    FRAME_INTERVAL = 0.1

    def __init__(self, image, x, ground_y):
        self.image = image
        self.x = x
        self.y = ground_y
        self.ground_y = ground_y
        self.state = "dormant"
        self.frame = 0
        self.frame_time = 0.0
        self.speed = 250.0

    @property
    def active_animation(self):
        return self.state in ("transforming", "attacking")

    def trigger(self):
        if self.state == "dormant":
            self.state = "transforming"
            self.frame = 0
            self.frame_time = 0.0

    def update(self, dt, player_x):
        if self.state == "dormant":
            return
        if self.state == "chasing":
            direction = 1 if player_x > self.x else -1
            self.x += direction * self.speed * dt
            self._animate(dt, 1)
        elif self.state == "transforming":
            self._animate(dt, 0)
            if self.state == "transforming" and self.frame == 7:
                self.state = "chasing"
                self.frame = 0
                self.frame_time = 0.0
        elif self.state == "attacking":
            self._animate(dt, 2)

    def attack(self):
        if self.state == "chasing":
            self.state = "attacking"
            self.frame = 0
            self.frame_time = 0.0

    def _animate(self, dt, row):
        self.frame_time += dt
        if self.frame_time < self.FRAME_INTERVAL:
            return
        self.frame = (self.frame + 1) % self.COLUMNS
        self.frame_time = 0.0
        if row == 2 and self.frame == 0:
            self.state = "dead"

    def draw(self):
        row = 0 if self.state == "dormant" else 1 if self.state == "chasing" else 2 if self.state in ("attacking", "dead") else 0
        frame = 0 if self.state == "dormant" else self.frame
        left = round(frame * self.image.w / self.COLUMNS)
        right = round((frame + 1) * self.image.w / self.COLUMNS)
        top = self.image.h - round(row * self.image.h / self.ROWS)
        bottom = self.image.h - round((row + 1) * self.image.h / self.ROWS)
        self.image.clip_composite_draw(
            left,
            bottom,
            right - left,
            top - bottom,
            0,
            "",
            self.x,
            self.y + 90,
            180,
            180,
        )


class HangingVine:
    def __init__(self, image, x, ground_y):
        self.image = image
        self.x = x
        self.ground_y = ground_y
        self.width = 120
        self.height = 180

    def blocks(self, player):
        return abs(player.x - self.x) < 70 and player.on_ground and player.state != PlayerState.SLIDE

    def draw(self):
        self.image.draw(self.x, self.ground_y + self.height / 2 + 70, self.width, self.height)


class VineBarrier:
    COLUMNS = 4
    ROWS = 2

    def __init__(self, original, cut_sheet, x, ground_y):
        self.original = original
        self.cut_sheet = cut_sheet
        self.x = x
        self.center_x = x
        self.ground_y = ground_y
        self.width = 150
        self.height = 150
        self.cut = False
        self.cutting = False
        self.frame = 0
        self.frame_time = 0.0

    def can_interact(self, player_x):
        return abs(player_x - self.x) < 150

    def start_cut(self):
        if not self.cut and not self.cutting:
            self.cutting = True
            self.frame = 0
            self.frame_time = 0.0

    def update(self, dt):
        if not self.cutting:
            return
        self.frame_time += dt
        if self.frame_time >= 0.1:
            self.frame += 1
            self.frame_time = 0.0
            if self.frame >= self.COLUMNS * self.ROWS:
                self.cutting = False
                self.cut = True

    def blocks(self, player_x):
        return not self.cut and not self.cutting and abs(player_x - self.x) < 90

    def draw(self):
        if self.cut:
            return
        if not self.cutting:
            self.original.draw(self.x, self.ground_y + 110, self.width, 220)
            return
        column = self.frame % self.COLUMNS
        row = self.frame // self.COLUMNS
        left = round(column * self.cut_sheet.w / self.COLUMNS)
        right = round((column + 1) * self.cut_sheet.w / self.COLUMNS)
        top = self.cut_sheet.h - round(row * self.cut_sheet.h / self.ROWS)
        bottom = self.cut_sheet.h - round((row + 1) * self.cut_sheet.h / self.ROWS)
        self.cut_sheet.clip_composite_draw(
            left, bottom, right - left, top - bottom, 0, "",
            self.x, self.ground_y + 80, 220, 160
        )


class Stage2(StageBase):
    """Stage 2-1 탐험과 Stage 2-2 꽃 괴수 추격."""

    EXPLORE_FLOWER = 1
    EXPLORE_MUSHROOM = 2
    CHASE = 3
    BACKGROUND_1 = "stage2-1.png"
    BACKGROUND_2 = "stage2-2.png"

    def __init__(self):
        super().__init__()
        self.section = self.EXPLORE_FLOWER
        self.background = None
        self.flower = None
        self.mushroom = None
        self.beast = None
        self.vine = None
        self.barrier = None
        self.e_icon = None
        self.high_rock = None
        self.checkpoint_x = 80
        self.dead = False
        self.retry_requested = False
        self.interaction_requested = False
        self.caught = False
        self.stage_transitioned = False

    def init(self):
        self._load_background("stage2-1.png")
        root = os.path.dirname(__file__)
        self.e_icon = load_image(os.path.join(root, "e_icon_no_yellow_no_sword.png"))
        mushroom_image = load_image(os.path.join(root, "mushroom.png"))
        self.mushroom = MushroomPlatform(mushroom_image, 720, self.ground_y + 100)
        self.flower = FlowerPlatform(620, 820, self.ground_y + 80)
        self.player = Player(80, self.ground_y)

    def _load_background(self, filename):
        root = os.path.dirname(__file__)
        self.background = load_image(os.path.join(root, filename))
        self.background_scale = min(
            game_framework.SCREEN_WIDTH / self.background.w,
            game_framework.SCREEN_HEIGHT / self.background.h,
        )
        self.background_left = (game_framework.SCREEN_WIDTH - self.background.w * self.background_scale) / 2
        self.background_bottom = (game_framework.SCREEN_HEIGHT - self.background.h * self.background_scale) / 2

    def _load_chase(self):
        root = os.path.dirname(__file__)
        self._load_background(self.BACKGROUND_2)
        self.beast = FlowerBeast(load_image(os.path.join(root, "flower_beast_animation.png")), 190, self.ground_y)
        self.vine = HangingVine(load_image(os.path.join(root, "long_hanging_vines.png")), 650, self.ground_y)
        self.barrier = VineBarrier(
            load_image(os.path.join(root, "vine_barrier_original.png")),
            load_image(os.path.join(root, "vine_cut_4x2_640px.png")),
            1160,
            self.ground_y,
        )
        self.mushroom = MushroomPlatform(load_image(os.path.join(root, "mushroom.png")), 780, self.ground_y + 100)
        self.flower = FlowerPlatform(930, 1080, self.ground_y + 80)
        self.player.x = 80
        self.player.y = self.ground_y
        self.player.ground_y = self.ground_y
        self.player.on_ground = True
        self.checkpoint_x = 80
        self.held_keys.clear()

    def handle_events(self, events):
        for event in events:
            if event.type == SDL_KEYDOWN:
                if event.key == SDLK_ESCAPE:
                    game_framework.quit()
                if self.dead or self.caught:
                    if event.key == SDLK_r:
                        self.retry_requested = True
                    continue
                self.held_keys.add(event.key)
                self.player.handle_key_down(event.key)
            elif event.type == SDL_KEYUP:
                self.held_keys.discard(event.key)
                self.player.handle_key_up(event.key)
        if self.player.consume_interaction():
            self.interaction_requested = True

    def update(self):
        dt = 1.0 / 60.0
        if self.dead:
            if self.retry_requested:
                self._retry()
            return
        if self.caught:
            self.beast.update(dt, self.player.x)
            if self.beast.state == "dead":
                self.caught = False
                self.dead = True
            return
        if self.section in (self.EXPLORE_FLOWER, self.EXPLORE_MUSHROOM):
            self._update_exploration(dt)
        else:
            self._update_chase(dt)

    def _update_exploration(self, dt):
        self.flower.update(dt)
        self.mushroom.update(dt)
        platforms = [self.flower] if self.section == self.EXPLORE_FLOWER else [self.mushroom]
        self._update_player_on_platforms(dt, platforms)
        if self.section == self.EXPLORE_FLOWER and self.player.x >= 1240:
            self.section = self.EXPLORE_MUSHROOM
            self.player.x = 80
            self.held_keys.clear()
        elif self.section == self.EXPLORE_MUSHROOM and self.player.x >= 1240:
            self.section = self.CHASE
            self._load_chase()

    def _update_chase(self, dt):
        self.flower.update(dt)
        self.mushroom.update(dt)
        self.barrier.update(dt)
        self.beast.update(dt, self.player.x)
        self._update_player_on_platforms(dt, [self.flower, self.mushroom])
        if self.beast.state == "dormant" and self.player.x >= 300:
            self.beast.trigger()
        if self.beast.state == "chasing" and abs(self.beast.x - self.player.x) < 55:
            self.beast.attack()
            self.caught = True
        if self.interaction_requested:
            if self.barrier.can_interact(self.player.x):
                self.barrier.start_cut()
            self.interaction_requested = False
        if self.barrier.blocks(self.player.x):
            self.player.x = self.barrier.x - 95
        if self.player.x >= 1260 and self.barrier.cut and not self.stage_transitioned:
            self.stage_transitioned = True
            game_framework.change_mode(Stage3())

    def _update_player_on_platforms(self, dt, platforms):
        if self.barrier is not None and self.barrier.cutting:
            return
        previous_y = self.player.y
        for platform in platforms:
            if isinstance(platform, FlowerPlatform) and not platform.opened:
                continue
            if self.player.on_ground and platform.supports(self.player.x) and self.player.y >= platform.top - 1:
                self.player.ground_y = platform.top
                break
        else:
            self.player.ground_y = self.ground_y
            if self.player.on_ground and self._in_gap(self.player.x):
                self.player.on_ground = False
        self.player.update(dt, self.held_keys, min_x=35, max_x=1270)
        for platform in platforms:
            if isinstance(platform, FlowerPlatform) and not platform.opened:
                continue
            if (
                not self.player.on_ground
                and self.player.velocity_y <= 0
                and previous_y >= platform.top
                and self.player.y <= platform.top
                and platform.supports(self.player.x)
            ):
                self.player.y = platform.top
                self.player.ground_y = platform.top
                self.player.velocity_y = 0.0
                self.player.on_ground = True
                if isinstance(platform, MushroomPlatform):
                    platform.bounce()
                    self.player.velocity_y = 900.0
                break
        if self.player.on_ground and self.player.ground_y != self.ground_y:
            if not any(platform.supports(self.player.x) for platform in platforms):
                self.player.ground_y = self.ground_y
                self.player.y = self.ground_y
        if self.player.y < self.ground_y - 80:
            self._retry()

    def _in_gap(self, x):
        return 560 < x < 850

    def _retry(self):
        self.dead = False
        self.caught = False
        self.retry_requested = False
        self.beast = None if self.section != self.CHASE else self.beast
        self.player.x = self.checkpoint_x
        self.player.y = self.ground_y
        self.player.ground_y = self.ground_y
        self.player.velocity_y = 0.0
        self.player.on_ground = True
        self.held_keys.clear()
        if self.beast is not None:
            self.beast.state = "dormant"
            self.beast.x = 190
            self.beast.frame = 0

    def _draw_background(self):
        self.background.draw(
            self.background_left + self.background.w * self.background_scale / 2,
            self.background_bottom + self.background.h * self.background_scale / 2,
            self.background.w * self.background_scale,
            self.background.h * self.background_scale,
        )

    def draw(self):
        self._draw_background()
        if self.section in (self.EXPLORE_FLOWER, self.CHASE):
            self.flower.draw()
        if self.section in (self.EXPLORE_MUSHROOM, self.CHASE):
            self.mushroom.draw()
        if self.section == self.CHASE:
            self.vine.draw()
            self.barrier.draw()
            self.beast.draw()
        if not self.caught and not (self.barrier is not None and self.barrier.cutting):
            self.player.draw()
        if self.section != self.CHASE:
            self._draw_e_hint(self.flower if self.section == self.EXPLORE_FLOWER else self.mushroom)
        elif self.barrier.can_interact(self.player.x) and not self.barrier.cut:
            self._draw_e_hint(self.barrier)
        if self.dead:
            draw_rectangle(430, 335, 850, 405, 255, 255, 255, 220, True)
            draw_rectangle(430, 335, 850, 405, 255, 255, 255, 255, False)

    def _draw_e_hint(self, target):
        if self.e_icon is not None and abs(self.player.x - target.center_x) < 220:
            self.e_icon.draw(target.center_x, 350, 42, 42)


class Stage3(StageBase):
    pass


class Stage4(StageBase):
    pass
