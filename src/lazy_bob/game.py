from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import random
import time


FRAME_TIME = 0.05
GRAVITY = 0.42
JUMP_VELOCITY = -2.7
BASE_SPEED = 1.0
MAX_SPEED = 2.8
SCORE_FILE = Path.home() / ".lazy_bob_score"
MIN_WIDTH = 44
MIN_HEIGHT = 16
JUMP_EXCLAMATION_TICKS = 10
BOBISM_TICKS = 26

BOB_SPRITES: dict[str, list[str]] = {
    "idle_a": [
        " o ",
        "/|_",
        "/ \\",
    ],
    "idle_b": [
        " o ",
        "/|_",
        "/| ",
    ],
    "crouch": [
        " o ",
        "/|_",
        "_/ ",
    ],
    "jump": [
        " o ",
        "_|\\",
        " /\\",
    ],
    "land": [
        " o ",
        "/|_",
        "_\\\\",
    ],
    "bonk": [
        " x ",
        "_|_",
        "/ \\",
    ],
}

OBSTACLE_SHAPES: list[list[str]] = [
    ["|"],
    ["#", "#"],
    ["##", "##"],
    ["/|", "##"],
    ["[]"],
    ["|/", "##"],
    ["&&"],
    ["&&", "&&"],
    ["&&&"],
    ["& &"],
]

JUMP_EXCLAMATIONS_CASUAL = [
    "drab",
    "yawn",
    "hmmm",
    "meh",
]

JUMP_EXCLAMATIONS_URGENT = [
    "oof",
    "ugh",
    "hrmph",
    "barely",
]

JUMP_EXCLAMATIONS_FAST = [
    "whoa",
    "still fine",
    "too much",
    "why run",
]

BOBISMS = [
    "Lazies shall inherit the Earth.",
    "Don't try too hard.",
    "Don't sweat. Catch some z's.",
    "Quit making others rich by working too hard.",
    "Living is also chilling.",
    "See, I got through.",
    "Thinkers don't do nothing.",
    "Your job is not your life.",
    "Breathe. Live.",
    "Don't forget livin.",
    "Ease up, Fred!",
    "By doing nothing, you save energy.",
]


@dataclass
class Obstacle:
    x: float
    shape: list[str] = field(default_factory=lambda: ["|"])
    passed: bool = False
    previous_x: float | None = None

    @property
    def height(self) -> int:
        return len(self.shape)

    @property
    def width(self) -> int:
        return max((len(row) for row in self.shape), default=1)


@dataclass
class GameState:
    width: int
    height: int
    bob_x: int
    ground_y: int
    bob_y: float
    bob_velocity: float = 0.0
    score: int = 0
    best_score: int = 0
    ticks: int = 0
    speed: float = BASE_SPEED
    spawn_cooldown: int = 0
    alive: bool = True
    obstacles: list[Obstacle] = field(default_factory=list)
    crouch_ticks: int = 0
    landing_ticks: int = 0
    bonk_ticks: int = 0
    jump_exclamation: str = ""
    jump_exclamation_ticks: int = 0
    bobism: str = ""
    bobism_ticks: int = 0

    @property
    def bob_row(self) -> int:
        return round(self.bob_y)

    @property
    def on_ground(self) -> bool:
        return self.bob_row >= self.ground_y


def load_best_score() -> int:
    try:
        return int(SCORE_FILE.read_text(encoding="utf-8").strip() or "0")
    except (FileNotFoundError, ValueError, OSError):
        return 0


def save_best_score(score: int) -> None:
    try:
        SCORE_FILE.write_text(str(score), encoding="utf-8")
    except OSError:
        pass


def create_state(width: int, height: int, best_score: int | None = None) -> GameState:
    best = load_best_score() if best_score is None else best_score
    ground_y = height - 2
    bob_x = max(4, width // 6)
    return GameState(
        width=width,
        height=height,
        bob_x=bob_x,
        ground_y=ground_y,
        bob_y=float(ground_y),
        best_score=best,
    )


def nearest_obstacle_distance(state: GameState) -> float | None:
    ahead_distances = [
        obstacle.x - (state.bob_x + 2)
        for obstacle in state.obstacles
        if obstacle.x + obstacle.width - 1 >= state.bob_x
    ]
    return min(ahead_distances) if ahead_distances else None


def pick_jump_exclamation(state: GameState, rng: random.Random) -> str:
    nearest = nearest_obstacle_distance(state)
    if state.speed >= 2.1:
        pool = JUMP_EXCLAMATIONS_FAST
    elif nearest is not None and nearest < 8:
        pool = JUMP_EXCLAMATIONS_URGENT
    else:
        pool = JUMP_EXCLAMATIONS_CASUAL
    return rng.choice(pool)


def set_bobism(state: GameState, rng: random.Random) -> None:
    state.bobism = rng.choice(BOBISMS)
    state.bobism_ticks = BOBISM_TICKS


def maybe_set_bobism(state: GameState, rng: random.Random) -> None:
    should_crack = state.score > 0 and (state.score % 5 == 0 or rng.random() < 0.18)
    if should_crack:
        set_bobism(state, rng)


def jump(state: GameState, rng: random.Random | None = None) -> None:
    if state.on_ground and state.alive:
        state.crouch_ticks = 2
        state.landing_ticks = 0
        state.bob_velocity = JUMP_VELOCITY
        picker = rng if rng is not None else random
        state.jump_exclamation = pick_jump_exclamation(state, picker)
        state.jump_exclamation_ticks = JUMP_EXCLAMATION_TICKS
        set_bobism(state, picker)


def choose_obstacle_shape(rng: random.Random, score: int) -> list[str]:
    shape_limit = min(len(OBSTACLE_SHAPES), 3 + score // 3)
    return list(rng.choice(OBSTACLE_SHAPES[:shape_limit]))


def maybe_spawn_obstacle(state: GameState, rng: random.Random) -> None:
    if state.spawn_cooldown > 0:
        state.spawn_cooldown -= 1
        return

    spawn_chance = min(0.1 + state.speed * 0.02, 0.22)
    if rng.random() < spawn_chance:
        shape = choose_obstacle_shape(rng, state.score)
        state.obstacles.append(Obstacle(x=float(state.width - 2), shape=shape))
        state.spawn_cooldown = rng.randint(10, 18)


def move_bob(state: GameState) -> None:
    was_on_ground = state.on_ground
    state.bob_velocity += GRAVITY
    state.bob_y += state.bob_velocity
    if state.bob_y >= state.ground_y:
        state.bob_y = float(state.ground_y)
        if not was_on_ground:
            state.landing_ticks = 2
        state.bob_velocity = 0.0

    if state.crouch_ticks > 0:
        state.crouch_ticks -= 1
    if state.landing_ticks > 0 and state.on_ground:
        state.landing_ticks -= 1
    if state.bonk_ticks > 0:
        state.bonk_ticks -= 1
    if state.jump_exclamation_ticks > 0:
        state.jump_exclamation_ticks -= 1
    elif state.jump_exclamation:
        state.jump_exclamation = ""
    if state.bobism_ticks > 0:
        state.bobism_ticks -= 1
    elif state.bobism:
        state.bobism = ""


def move_obstacles(state: GameState, rng: random.Random) -> None:
    survivors: list[Obstacle] = []
    for obstacle in state.obstacles:
        obstacle.previous_x = obstacle.x
        obstacle.x -= state.speed
        if not obstacle.passed and obstacle.x + obstacle.width - 1 < state.bob_x:
            obstacle.passed = True
            state.score += 1
            if state.score > state.best_score:
                state.best_score = state.score
                save_best_score(state.best_score)
            maybe_set_bobism(state, rng)
        if obstacle.x + obstacle.width > -1:
            survivors.append(obstacle)
    state.obstacles = survivors


def detect_collision(state: GameState) -> bool:
    bob_left = state.bob_x
    bob_right = state.bob_x + 2
    bob_top = state.bob_row - 2
    bob_bottom = state.bob_row

    for obstacle in state.obstacles:
        previous_x = obstacle.previous_x if obstacle.previous_x is not None else obstacle.x
        left_edge = min(previous_x, obstacle.x)
        right_edge = max(previous_x, obstacle.x) + obstacle.width - 1
        obstacle_top = state.ground_y - obstacle.height + 1
        obstacle_bottom = state.ground_y

        x_overlap = not (right_edge < bob_left or left_edge > bob_right)
        y_overlap = not (obstacle_bottom < bob_top or obstacle_top > bob_bottom)
        if not x_overlap or not y_overlap:
            continue
        return True
    return False


def step(state: GameState, rng: random.Random) -> None:
    if not state.alive:
        return

    state.ticks += 1
    state.speed = min(BASE_SPEED + state.score * 0.05, MAX_SPEED)
    maybe_spawn_obstacle(state, rng)
    move_bob(state)
    move_obstacles(state, rng)
    if detect_collision(state):
        state.alive = False
        state.bonk_ticks = 4


def current_bob_sprite(state: GameState) -> list[str]:
    if not state.alive:
        return BOB_SPRITES["bonk"]
    if state.landing_ticks > 0 and state.on_ground:
        return BOB_SPRITES["land"]
    if not state.on_ground:
        return BOB_SPRITES["jump"]
    if state.crouch_ticks > 0:
        return BOB_SPRITES["crouch"]
    if (state.ticks // 6) % 2 == 0:
        return BOB_SPRITES["idle_a"]
    return BOB_SPRITES["idle_b"]


def draw_text(canvas: list[list[str]], row: int, col: int, text: str) -> None:
    if row < 0 or row >= len(canvas):
        return
    for offset, char in enumerate(text):
        x = col + offset
        if 0 <= x < len(canvas[row]):
            canvas[row][x] = char


def render_lines(state: GameState) -> list[str]:
    canvas = [[" " for _ in range(state.width)] for _ in range(state.height)]

    for x in range(state.width):
        canvas[state.ground_y + 1][x] = "_"

    bob_row = max(0, min(state.height - 1, state.bob_row))
    bob_sprite = current_bob_sprite(state)
    bob_top = bob_row - (len(bob_sprite) - 1)
    for sprite_row, sprite_text in enumerate(bob_sprite):
        draw_text(canvas, bob_top + sprite_row, state.bob_x, sprite_text)

    if state.alive and state.on_ground and state.crouch_ticks == 0 and state.landing_ticks == 0:
        if (state.ticks // 14) % 3 == 0:
            draw_text(canvas, max(0, bob_top), state.bob_x + 4, "z")
    if state.jump_exclamation_ticks > 0 and state.jump_exclamation:
        exclamation_row = max(0, bob_top - 1)
        exclamation_col = min(state.width - len(state.jump_exclamation), state.bob_x + 4)
        draw_text(canvas, exclamation_row, max(0, exclamation_col), state.jump_exclamation)

    for obstacle in state.obstacles:
        obstacle_x = round(obstacle.x)
        obstacle_top = state.ground_y - obstacle.height + 1
        for row_offset, row_text in enumerate(obstacle.shape):
            draw_text(canvas, obstacle_top + row_offset, obstacle_x, row_text)

    title = " Lazy Bob "
    controls = "space jump   q quit"
    score = f"score {state.score}   best {state.best_score}   speed {state.speed:.1f}"
    if state.width > len(title):
        start = max(0, (state.width - len(title)) // 2)
        for index, char in enumerate(title):
            canvas[0][start + index] = char

    for row, text in ((1, controls), (2, score)):
        if row < state.height:
            for index, char in enumerate(text[: state.width]):
                canvas[row][index] = char

    if state.bobism_ticks > 0 and state.bobism:
        bobism_row = max(4, bob_top - 2)
        bobism_col = min(state.width - len(state.bobism), max(0, state.bob_x - 1))
        draw_text(canvas, bobism_row, bobism_col, state.bobism)

    if not state.alive:
        message = " bonk. press r to retry or q to quit "
        if state.width > len(message):
            start = (state.width - len(message)) // 2
            for index, char in enumerate(message):
                canvas[state.height // 2][start + index] = char

    return ["".join(row).rstrip() for row in canvas]


def handle_input(key: int, state: GameState, best_score: int) -> GameState | None:
    if key in (-1,):
        return state
    if key in (ord("q"), ord("Q")):
        return None
    if key in (ord(" "),):
        if state.alive:
            jump(state)
            return state
        return create_state(state.width, state.height, best_score=best_score)
    if key in (ord("r"), ord("R")) and not state.alive:
        return create_state(state.width, state.height, best_score=best_score)
    return state


def run_curses(stdscr) -> None:
    import curses

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    rng = random.Random()

    while True:
        height, width = stdscr.getmaxyx()
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            stdscr.erase()
            stdscr.addstr(0, 0, f"Need at least {MIN_WIDTH}x{MIN_HEIGHT}. Current: {width}x{height}")
            stdscr.addstr(1, 0, "Resize the terminal, then press q to leave.")
            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            time.sleep(0.1)
            continue

        state = create_state(width, height)
        while True:
            height, width = stdscr.getmaxyx()
            if width != state.width or height != state.height:
                break

            loop_start = time.monotonic()
            next_state = handle_input(stdscr.getch(), state, state.best_score)
            if next_state is None:
                return
            state = next_state
            step(state, rng)

            stdscr.erase()
            for row_index, line in enumerate(render_lines(state)):
                try:
                    stdscr.addstr(row_index, 0, line)
                except curses.error:
                    pass
            stdscr.refresh()

            remaining = FRAME_TIME - (time.monotonic() - loop_start)
            if remaining > 0:
                time.sleep(remaining)


def main() -> None:
    try:
        import curses
    except ImportError as exc:
        raise SystemExit("Lazy Bob needs the standard curses module to run in the terminal.") from exc

    curses.wrapper(run_curses)
