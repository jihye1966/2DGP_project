"""캐릭터 입력, 물리, 충돌 박스와 5x8 스프라이트 애니메이션."""

import os
from enum import Enum

from pico2d import SDLK_a, SDLK_d, SDLK_e, SDLK_LEFT, SDLK_RIGHT, SDLK_SPACE
from pico2d import SDLK_LCTRL, SDLK_LSHIFT, SDLK_RCTRL, SDLK_RSHIFT, SDLK_s
from pico2d import load_image


class PlayerState(Enum):
    IDLE = 0
    WALK = 1
    RUN = 2
    JUMP = 3
    FALL = 4
    SLIDE = 5
    CROUCH = 6


class Player:
    SHEET_COLUMNS = 8
    SHEET_ROWS = 5
    ANIMATION_ROWS = {
        PlayerState.IDLE: 0,
        PlayerState.WALK: 1,
        PlayerState.RUN: 2,
        PlayerState.JUMP: 3,
        PlayerState.FALL: 3,
        PlayerState.SLIDE: 4,
        PlayerState.CROUCH: 4,
    }
    ANIMATION_SPEEDS = {
        PlayerState.IDLE: 5.0,
        PlayerState.WALK: 9.0,
        PlayerState.RUN: 20.0,
        PlayerState.JUMP: 8.0,
        PlayerState.FALL: 8.0,
        PlayerState.SLIDE: 10.0,
        PlayerState.CROUCH: 5.0,
    }
    ANIMATION_FRAME_RANGES = {
        PlayerState.IDLE: (0, 0),
        PlayerState.WALK: (1, 6),
        PlayerState.RUN: (0, 7),
        PlayerState.JUMP: (0, 7),
        PlayerState.FALL: (0, 7),
        PlayerState.SLIDE: (0, 7),
        PlayerState.CROUCH: (0, 7),
    }

    def __init__(self, x, ground_y, sheet_name="character_normal_8x5_200px.png"):
        self.x = float(x)
        self.y = float(ground_y)
        self.ground_y = float(ground_y)
        self.speed = 220.0
        self.run_speed = 360.0
        self.jump_speed = 620.0
        self.gravity = 1550.0
        self.velocity_y = 0.0
        self.facing = 1
        self.state = PlayerState.IDLE
        self.frame = 0
        self.frame_time = 0.0
        self.on_ground = True
        self.interaction_requested = False
        self.image = load_image(os.path.join(os.path.dirname(__file__), sheet_name))
        self.sheet_width, self.sheet_height = self.image.w, self.image.h
        self.draw_height = 142
        self.draw_width = self.draw_height * (self.sheet_width / self.SHEET_COLUMNS) / (
            self.sheet_height / self.SHEET_ROWS
        )

    @property
    def collision_box(self):
        """발 기준의 충돌 박스. 슬라이드/웅크리기에서는 높이를 줄인다."""
        height = 58 if self.state in (PlayerState.SLIDE, PlayerState.CROUCH) else 112
        return (self.x - 26, self.y, self.x + 26, self.y + height)

    def handle_key_down(self, key):
        if key == SDLK_SPACE:
            self.jump()
        elif key == SDLK_s:
            self.state = PlayerState.CROUCH
        elif key == SDLK_LCTRL or key == SDLK_RCTRL:
            if self.on_ground:
                self.state = PlayerState.SLIDE
        else:
            self.interaction_requested = self.interaction_requested or key == SDLK_e

    def handle_key_up(self, key):
        if key == SDLK_s and self.state == PlayerState.CROUCH:
            self.state = PlayerState.IDLE
        if key in (SDLK_LCTRL, SDLK_RCTRL) and self.state == PlayerState.SLIDE:
            self.state = PlayerState.IDLE

    def consume_interaction(self):
        requested = self.interaction_requested
        self.interaction_requested = False
        return requested

    def jump(self):
        if self.on_ground and self.state != PlayerState.CROUCH:
            self.velocity_y = self.jump_speed
            self.on_ground = False
            self.state = PlayerState.JUMP

    def update(self, dt, held_keys=None, min_x=0.0, max_x=None):
        held_keys = held_keys or set()
        left = SDLK_a in held_keys or SDLK_LEFT in held_keys
        right = SDLK_d in held_keys or SDLK_RIGHT in held_keys
        moving = left != right
        ctrl_held = SDLK_LCTRL in held_keys or SDLK_RCTRL in held_keys
        if left:
            self.facing = -1
        elif right:
            self.facing = 1

        direction = 1 if right else -1 if left else 0
        horizontal_speed = self.run_speed if SDLK_LSHIFT in held_keys or SDLK_RSHIFT in held_keys else self.speed

        if self.on_ground:
            if self.state != PlayerState.CROUCH:
                if moving and ctrl_held:
                    self.state = PlayerState.SLIDE
                elif moving and (SDLK_LSHIFT in held_keys or SDLK_RSHIFT in held_keys):
                    self.state = PlayerState.RUN
                elif moving:
                    self.state = PlayerState.WALK
                else:
                    self.state = PlayerState.IDLE
            speed = horizontal_speed
            if self.state in (PlayerState.SLIDE, PlayerState.CROUCH):
                speed *= 0.65
            self.x += direction * speed * dt
        else:
            # 공중에서도 방향키를 유지하면 수평 이동을 계속한다.
            self.x += direction * horizontal_speed * dt
            self.velocity_y -= self.gravity * dt
            self.y += self.velocity_y * dt
            self.state = PlayerState.JUMP if self.velocity_y > 0 else PlayerState.FALL
            if self.y <= self.ground_y:
                self.y = self.ground_y
                self.velocity_y = 0.0
                self.on_ground = True

        self.x = max(min_x, self.x)
        if max_x is not None:
            self.x = min(max_x, self.x)
        self._advance_animation(dt)

    def _advance_animation(self, dt):
        if self.state == PlayerState.IDLE:
            self.frame = 0
            self.frame_time = 0.0
            return
        first_frame, last_frame = self.ANIMATION_FRAME_RANGES[self.state]
        if self.frame < first_frame or self.frame > last_frame:
            self.frame = first_frame
        self.frame_time += dt
        interval = 1.0 / self.ANIMATION_SPEEDS[self.state]
        if self.frame_time >= interval:
            steps = int(self.frame_time / interval)
            frame_count = last_frame - first_frame + 1
            self.frame = first_frame + (self.frame - first_frame + steps) % frame_count
            self.frame_time -= steps * interval

    def draw(self):
        row = self.ANIMATION_ROWS[self.state]
        left = round(self.frame * self.sheet_width / self.SHEET_COLUMNS)
        right = round((self.frame + 1) * self.sheet_width / self.SHEET_COLUMNS)
        top = self.sheet_height - round(row * self.sheet_height / self.SHEET_ROWS)
        bottom = self.sheet_height - round((row + 1) * self.sheet_height / self.SHEET_ROWS)
        source_width = right - left
        source_height = top - bottom
        self.image.clip_composite_draw(
            left,
            bottom,
            source_width,
            source_height,
            0,
            "" if self.facing == 1 else "h",
            self.x,
            self.y + self.draw_height / 2,
            self.draw_width,
            self.draw_height,
        )
