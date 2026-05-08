# Lazy Bob

`Lazy Bob` is a tiny terminal game for people who appreciate low-effort heroics.

Bob is too laid back to run. He only jumps when absolutely necessary.
Your job is to hit `space` just in time so he avoids the next hurdle.

Everything is intentionally bare-bones:

- terminal only
- ASCII only
- one button that matters
- no external dependencies

## Install

```bash
pip install lazy-bob
```

For local development:

```bash
pip install -e .
```

## Run

```bash
lazy-bob
```

## Controls

- `space`: jump
- `r`: restart after a crash
- `q`: quit

## Notes

- The game uses Python's built-in `curses` module, so it works best on macOS and Linux terminals.
- Bob's best score is saved locally in `~/.lazy_bob_score`.

Drop me a line if you like Lazy Bob at anantdhavale@gmail.com.

Copyright for the Lazy Bob character and Bob-isms © Anant Dhavale.
