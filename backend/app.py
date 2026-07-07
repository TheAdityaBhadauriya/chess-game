"""
app.py — Flask API for the chess game.
Step 1 scope: game state + rules only (bot comes in later steps).
Games are kept in-memory keyed by game_id.
"""

import uuid
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from game_engine import ChessGame

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


if __name__ == "__main__":
    app.run(debug=True, port=5000)