"""Stage1~4 모드. 현재는 Stage 1의 임시 지형만 제공한다."""

from pico2d import SDLK_ESCAPE, SDL_KEYDOWN, SDL_KEYUP

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
        from pico2d import draw_rectangle, draw_string

        draw_rectangle(0, 0, game_framework.SCREEN_WIDTH, self.ground_y)
        draw_rectangle(0, self.ground_y, game_framework.SCREEN_WIDTH, game_framework.SCREEN_HEIGHT)
        self.player.draw()
        draw_string(30, 680, "Stage 1 - Peaceful Forest (temporary)", (255, 255, 255))


class Stage1(StageBase):
    pass


class Stage2(StageBase):
    pass


class Stage3(StageBase):
    pass


class Stage4(StageBase):
    pass
