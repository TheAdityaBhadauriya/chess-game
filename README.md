# ♟ Chess Game — Adaptive Bot Difficulty + Full Game Analysis

A full-stack chess web app with a rules engine, 10-tier bot difficulty (from
a from-scratch minimax/alpha-beta engine to Stockfish at max strength), and
a post-game analysis suite similar to chess.com — move classification,
accuracy scoring, opening detection, and an evaluation graph.

Built with Python (Flask + `python-chess` + Stockfish) and vanilla JS.

## Features

- **Full rules engine** — legal move generation, check/checkmate/stalemate,
  castling, en passant, pawn promotion, and all draw conditions, via
  `python-chess`.
- **Two move input styles** — drag-and-drop or click-to-move, both with
  instant legal-move highlighting and enforcement.
- **10-tier bot difficulty**, named and rated against real benchmarks:

  | Level | Name | ~Rating | Engine |
  |---|---|---|---|
  | 1 | Pawn Shuffler | 500 | Custom minimax |
  | 2 | Club Rookie | 800 | Custom minimax |
  | 3 | Club Player | 1100 | Custom minimax |
  | 4 | Strong Club Player | 1400 | Custom minimax + alpha-beta |
  | 5 | Candidate Master | 1700 | Stockfish (skill 2) |
  | 6 | National Master | 2000 | Stockfish (skill 5) |
  | 7 | Judit Polgar-level | 2300 | Stockfish (skill 9) |
  | 8 | Viswanathan Anand-level | 2500 | Stockfish (skill 13) |
  | 9 | Bobby Fischer-level | 2700 | Stockfish (skill 17) |
  | 10 | Magnus Carlsen-level | 2850 | Stockfish (skill 20) |

- **Custom chess engine** (levels 1–4): material evaluation, piece-square
  tables, minimax search with alpha-beta pruning, and controlled randomness
  at lower tiers to simulate human imperfection.
- **Post-game analysis** (chess.com-style):
  - Opening detection via the Lichess ECO dataset (3,500+ named openings)
  - Every move evaluated by Stockfish at depth 15
  - Moves classified as Best / Good / Inaccuracy / Mistake / Blunder based
    on centipawn loss
  - Per-side accuracy percentage
  - Evaluation graph across the whole game
- **Resign** option, ending the game and unlocking analysis without playing
  to checkmate.
- **Captured pieces** tracker.
- Distinctive wood-and-brass tournament-styled UI (not a default dark
  theme) — serif display type, monospace scoresheet-style move list,
  color-coded move breakdown.

## Tech stack

- **Backend:** Python, Flask, `python-chess`, Stockfish (via the `stockfish`
  PyPI package)
- **Frontend:** vanilla JS, `chessboard.js`, jQuery, custom CSS
- **Data:** Lichess `chess-openings` ECO dataset (public domain)

## Project structure

chess-game/
├── backend/
│   ├── app.py               # Flask routes / API
│   ├── game_engine.py       # python-chess wrapper (rules, state, PGN)
│   ├── bot_engine.py        # custom minimax + alpha-beta bot (levels 1-4)
│   ├── stockfish_engine.py  # Stockfish integration (levels 5-10)
│   ├── openings.py          # ECO opening lookup
│   ├── game_analysis.py     # post-game analysis engine
│   └── data/                # Lichess ECO tsv files
├── frontend/
│   ├── templates/index.html
│   └── static/
│       ├── css/style.css
│       └── js/main.js
├── requirements.txt
└── README.md

## Setup

**Prerequisites:** Python 3.10+, and the [Stockfish binary](https://stockfishchess.org/download/) downloaded separately.

```bash
git clone https://github.com/TheAdityaBhadauriya/chess-game.git
cd chess-game
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

Download Stockfish and update the path in `backend/stockfish_engine.py`:
```python
STOCKFISH_PATH = r"C:\stockfish\stockfish.exe"  # adjust to your path
```

Download the opening dataset into `backend/data/`:
```bash
cd backend/data
curl -O https://raw.githubusercontent.com/lichess-org/chess-openings/master/a.tsv
curl -O https://raw.githubusercontent.com/lichess-org/chess-openings/master/b.tsv
curl -O https://raw.githubusercontent.com/lichess-org/chess-openings/master/c.tsv
curl -O https://raw.githubusercontent.com/lichess-org/chess-openings/master/d.tsv
curl -O https://raw.githubusercontent.com/lichess-org/chess-openings/master/e.tsv
```

Run it:
```bash
cd backend
python app.py
```

Visit `http://127.0.0.1:5000`.

## API reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/new_game` | Start a new game, returns `game_id` |
| GET | `/api/game/<id>` | Current game state |
| GET | `/api/game/<id>/legal_moves?square=e2` | Legal moves (optionally by square) |
| POST | `/api/game/<id>/move` | Body: `{"move": "e2e4"}` (UCI, promotions e.g. `"e7e8q"`) |
| POST | `/api/game/<id>/bot_move` | Body: `{"level": 1-10}` — bot plays a move |
| POST | `/api/game/<id>/resign` | Body: `{"color": "white"/"black"}` |
| POST | `/api/game/<id>/undo` | Undo last move |
| POST | `/api/game/<id>/reset` | Reset the board |
| GET | `/api/game/<id>/pgn` | Export as PGN |
| GET | `/api/game/<id>/opening` | Identify the opening played so far |
| GET | `/api/game/<id>/analysis` | Full post-game analysis |
| GET | `/api/difficulty_levels` | List all 10 bot tiers with names/ratings |
| GET | `/api/health` | Health check |

## Roadmap / possible extensions

- Sound effects for moves/captures
- Move undo button in the UI
- Deployment (Render/Railway) for a live demo link
- Puzzle mode using the analysis engine's blunder detection