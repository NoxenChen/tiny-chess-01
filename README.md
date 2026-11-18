# Tiny Chess

[![make.fun · tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/NoxenChen/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/NoxenChen/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)

A chess engine in 4,096 bytes of Python, built for the make.fun `tiny-chess-01` bounty. `main.py` is the whole engine: an lzma-compressed payload plus a one-line unpacker.

## The engine

- 0x88 board, full legal move generation: castling, en passant, promotion, check, checkmate, stalemate, threefold repetition.
- Negamax with alpha-beta, iterative deepening to a fixed node budget (100,000 nodes/move, no wall clock — deterministic, replays identically).
- Quiescence search over captures and promotions, with MVV-LVA ordering and delta pruning.
- Transposition table, null-move pruning, transposition-table move ordering at the root.
- Evaluation: material plus piece-square tables, bishop pair, and an endgame king table once the queens are off and material is low.

## Run it

The program talks to the competition env at `MAKEFUN_ENV_URL` (`POST /game`, `/move`, `/resign`) and is run as `python3 -P -s main.py`. It uses only the Python standard library and reads no other file.
