"""Weird Forest의 간단한 모드 전환 프레임워크."""

from pico2d import clear_canvas, close_canvas, delay, get_events, open_canvas, update_canvas


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
_current_mode = None
_running = True


def change_mode(mode):
    """현재 모드를 종료하고 새 모드를 시작한다."""
    global _current_mode
    if _current_mode is not None:
        _current_mode.finish()
    _current_mode = mode
    _current_mode.init()


def quit():
    """게임 루프를 정상 종료한다."""
    global _running
    _running = False


def run(initial_mode):
    """초기 모드부터 게임 루프를 실행한다."""
    global _running
    _running = True
    open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)
    change_mode(initial_mode)
    while _running and _current_mode is not None:
        events = get_events()
        _current_mode.handle_events(events)
        _current_mode.update()
        clear_canvas()
        _current_mode.draw()
        update_canvas()
        delay(1.0 / 60.0)
    if _current_mode is not None:
        _current_mode.finish()
    close_canvas()
