"""타이틀 메뉴, 오두막 INTRO와 Stage 1 진입."""

import os
from pico2d import SDLK_ESCAPE, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN
from pico2d import clear_canvas, draw_rectangle, load_image

import game_framework
from player import Player, PlayerState


class Title:
    MENU, APPEARANCE, IDLE = range(3)
    INTRO = APPEARANCE
    MOVE = IDLE
    WIDTH, HEIGHT = 1280, 720
    # 배경 원본의 오두막 문 앞 지면을 1280x720 좌표로 환산한 값이다.
    GROUND_Y = 180
    APPEARANCE_X = 245
    MIN_PLAYER_X = 180

    def __init__(self):
        self.state = self.MENU
        self.background = None
        self.logo = None
        self.start = None
        self.exit = None
        self.player = None
        self.held_keys = set()
        self.overlay_frames = []
        self.overlay_index = 0
        self.overlay_time = 0.0
        self.intro_time = 0.0
        self.transitioned = False
        self.scale = 1.0
        self.background_left = 0.0
        self.background_bottom = 0.0

    def init(self):
        root = os.path.dirname(__file__)
        self.background = self._load_optional(root, "title_original.png")
        self.logo = load_image(os.path.join(root, "logo.png"))
        self.start = load_image(os.path.join(root, "start.png"))
        self.exit = load_image(os.path.join(root, "exit.png"))
        self.overlay_frames = self._load_overlays(root)

        if self.background is not None:
            self.scale = min(self.WIDTH / self.background.w, self.HEIGHT / self.background.h)
            self.background_left = (self.WIDTH - self.background.w * self.scale) / 2
            self.background_bottom = (self.HEIGHT - self.background.h * self.scale) / 2

    def finish(self):
        self.player = None

    def handle_events(self, events):
        for event in events:
            if event.type == SDL_MOUSEBUTTONDOWN and self.state == self.MENU:
                if self._inside_button(event.x, event.y, self.start, 950, 410):
                    self.state = self.APPEARANCE
                    self.intro_time = 0.0
                    self.overlay_index = 0
                    self.overlay_time = 0.0
                    self.player = Player(self.APPEARANCE_X, self.GROUND_Y)
                elif self._inside_button(event.x, event.y, self.exit, 950, 230):
                    game_framework.quit()
            elif event.type == SDL_KEYDOWN:
                if event.key == SDLK_ESCAPE:
                    game_framework.quit()
                self.held_keys.add(event.key)
            elif event.type == SDL_KEYUP:
                self.held_keys.discard(event.key)

    def update(self):
        dt = 1.0 / 60.0
        if self.state == self.APPEARANCE:
            self.intro_time += dt
            if self.overlay_frames:
                self.overlay_time += dt
                if self.overlay_time >= 0.1:
                    self.overlay_index = min(self.overlay_index + 1, len(self.overlay_frames) - 1)
                    self.overlay_time = 0.0
                if self.intro_time >= len(self.overlay_frames) * 0.1:
                    self._finish_appearance()
            elif self.intro_time >= 1.6:
                self._finish_appearance()
        elif self.state == self.IDLE:
            self.player.update(dt, self.held_keys, min_x=self.MIN_PLAYER_X, max_x=1270)
            if self.player.collision_box[2] >= self.WIDTH and not self.transitioned:
                self.transitioned = True
                from playmode import Stage1

                game_framework.change_mode(Stage1())

    def draw(self):
        self._draw_background()
        if self.state == self.MENU:
            self.logo.draw(640, 590, 650, 244)
            self.start.draw(950, 410, 390, 143)
            self.exit.draw(950, 230, 368, 134)
        elif self.state == self.APPEARANCE:
            if self.overlay_frames:
                self._draw_overlay()
            elif self.player is not None:
                self.player.draw()
        elif self.player is not None:
            self.player.draw()

    def _finish_appearance(self):
        """등장 연출 종료 후 같은 좌표에서 조작 대기 상태로 전환한다."""
        self.state = self.IDLE
        self.held_keys.clear()
        if self.player is not None:
            self.player.state = PlayerState.IDLE
            self.player.frame = 0
            self.player.frame_time = 0.0

    def _draw_background(self):
        if self.background is None:
            draw_rectangle(0, 0, self.WIDTH, self.HEIGHT)
            return
        self.background.draw(
            self.background_left + self.background.w * self.scale / 2,
            self.background_bottom + self.background.h * self.scale / 2,
            self.background.w * self.scale,
            self.background.h * self.scale,
        )

    def _draw_overlay(self):
        frame = self.overlay_frames[self.overlay_index]
        frame.draw(
            self.background_left + (170 + 185) * self.scale,
            self.background_bottom + (941 - 450 - 130) * self.scale,
            370 * self.scale,
            260 * self.scale,
        )

    @staticmethod
    def _load_optional(root, name):
        path = os.path.join(root, name)
        return load_image(path) if os.path.exists(path) else None

    @staticmethod
    def _load_overlays(root):
        folder = os.path.join(root, "resources", "cottage_overlay_aligned_16frames")
        if not os.path.isdir(folder):
            folder = os.path.join(root, "cottage_overlay_aligned_16frames")
        if not os.path.isdir(folder):
            return []
        frames = []
        for index in range(16):
            path = os.path.join(folder, "overlay_%02d.png" % index)
            if os.path.exists(path):
                frames.append(load_image(path))
        return frames if len(frames) == 16 else []

    @staticmethod
    def _inside_button(x, y, image, center_x, center_y):
        width = image.w * 0.94
        height = image.h * 0.86
        return center_x - width / 2 <= x <= center_x + width / 2 and center_y - height / 2 <= y <= center_y + height / 2
