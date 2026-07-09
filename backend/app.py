"""
app.py — Flask API for the chess game.
Step 1 scope: game state + rules only (bot comes in later steps).
Games are kept in-memory keyed by game_id.
"""

import uuid
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from stockfish_engine import get_stockfish_move, STOCKFISH_BOT_LEVELS
from game_engine import ChessGame
from bot_engine import get_bot_move_for_level, CUSTOM_BOT_LEVELS
import chess
from openings import identify_opening

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)
CORS(app)

# in-memory game store: { game_id: ChessGame }
GAMES = {}


def get_game_or_404(game_id):
    return GAMES.get(game_id)


# ---------- page ----------

@app.route("/")
def index():
    return render_template("index.html")


# ---------- API ----------

@app.route("/api/new_game", methods=["POST"])
def new_game():
    game_id = str(uuid.uuid4())
    GAMES[game_id] = ChessGame(game_id)
    return jsonify(GAMES[game_id].to_dict()), 201


@app.route("/api/game/<game_id>", methods=["GET"])
def get_game(game_id):
    game = get_game_or_404(game_id)
    if not game:
        return jsonify({"error": "game not found"}), 404
    return jsonify(game.to_dict())


@app.route("/api/game/<game_id>/legal_moves", methods=["GET"])
def legal_moves(game_id):
    game = get_game_or_404(game_id)
    if not game:
        return jsonify({"error": "game not found"}), 404

    square = request.args.get("square")
    if square:
        return jsonify({"moves": game.legal_moves_from_square(square)})
    return jsonify({"moves": game.legal_moves_uci()})


@app.route("/api/game/<game_id>/move", methods=["POST"])
def make_move(game_id):
    game = get_game_or_404(game_id)
    if not game:
        return jsonify({"error": "game not found"}), 404

    data = request.get_json(silent=True) or {}
    uci_move = data.get("move")
    if not uci_move:
        return jsonify({"error": "missing 'move' field (expected UCI, e.g. 'e2e4')"}), 400

    try:
        state = game.push_move(uci_move)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(state)


@app.route("/api/game/<game_id>/undo", methods=["POST"])
def undo_move(game_id):
    game = get_game_or_404(game_id)
    if not game:
        return jsonify({"error": "game not found"}), 404
    return jsonify(game.undo_last_move())


@app.route("/api/game/<game_id>/reset", methods=["POST"])
def reset_game(game_id):
    game = get_game_or_404(game_id)
    if not game:
        return jsonify({"error": "game not found"}), 404
    game.reset()
    return jsonify(game.to_dict())


@app.route("/api/game/<game_id>/pgn", methods=["GET"])
def get_pgn(game_id):
    game = get_game_or_404(game_id)
    if not game:
        return jsonify({"error": "game not found"}), 404
    return jsonify({"pgn": game.to_pgn()})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "active_games": len(GAMES)})

@app.route("/api/game/<game_id>/bot_move", methods=["POST"])
def bot_move(game_id):
    game = get_game_or_404(game_id)
    if not game:
        return jsonify({"error": "game not found"}), 404

    data = request.get_json(silent=True) or {}
    level = data.get("level", 1)

    if level in CUSTOM_BOT_LEVELS:
        move = get_bot_move_for_level(game.board, level)
        if move is None:
            return jsonify({"error": "no legal moves (game over)"}), 400
        move_uci = move.uci()
        bot_name = CUSTOM_BOT_LEVELS[level]["name"]

    elif level in STOCKFISH_BOT_LEVELS:
        move_uci = get_stockfish_move(game.board.fen(), level)
        if move_uci is None:
            return jsonify({"error": "no legal moves (game over)"}), 400
        bot_name = STOCKFISH_BOT_LEVELS[level]["name"]

    else:
        return jsonify({"error": f"invalid level {level} (must be 1-10)"}), 400

    state = game.push_move(move_uci)
    state["bot_move_played"] = move_uci
    state["bot_name"] = bot_name
    return jsonify(state)

@app.route("/api/difficulty_levels", methods=["GET"])
def difficulty_levels():
    levels = {}
    for lvl, cfg in CUSTOM_BOT_LEVELS.items():
        levels[lvl] = {"name": cfg["name"], "rating": cfg["rating"]}
    for lvl, cfg in STOCKFISH_BOT_LEVELS.items():
        levels[lvl] = {"name": cfg["name"], "rating": cfg["rating"]}
    return jsonify(levels)

@app.route("/api/game/<game_id>/opening", methods=["GET"])
def get_opening(game_id):
    game = get_game_or_404(game_id)
    if not game:
        return jsonify({"error": "game not found"}), 404
    opening = identify_opening(game.move_history)
    return jsonify(opening or {"eco": None, "name": "Unknown / Out of book"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
