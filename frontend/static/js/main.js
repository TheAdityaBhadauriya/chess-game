const API_BASE = "http://127.0.0.1:5000/api";

let board = null;
let gameId = null;
let gameState = null;

// ---------- board setup ----------

function initBoard() {
  board = Chessboard("board", {
    position: "start",
    draggable: true,
    pieceTheme: "https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png",
    onDrop: handleMove,
    onDragStart: onDragStart,
  });
}

function onDragStart(source, piece) {
  // prevent dragging if game is over
  if (gameState && gameState.is_game_over) return false;

  // prevent picking up the wrong color's pieces
  const isWhitePiece = piece.startsWith("w");
  const isWhiteTurn = gameState && gameState.turn === "white";
  if (isWhitePiece !== isWhiteTurn) return false;
}

// ---------- API calls ----------

async function startNewGame() {
  const res = await fetch(`${API_BASE}/new_game`, { method: "POST" });
  gameState = await res.json();
  gameId = gameState.game_id;
  board.position(gameState.fen);
  updateSidePanel();
}

async function handleMove(source, target) {
  const uciMove = source + target; // e.g. "e2e4"

  const res = await fetch(`${API_BASE}/game/${gameId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ move: uciMove }),
  });

  if (!res.ok) {
    // illegal move — snap piece back
    return "snapback";
  }

  gameState = await res.json();
  updateSidePanel();

  // sync board to server FEN (handles castling, en passant, promotion visuals)
  board.position(gameState.fen);
}

// ---------- UI updates ----------

function updateSidePanel() {
  document.getElementById("turn-indicator").textContent = gameState.turn;

  let status = "-";
  if (gameState.is_checkmate) status = "Checkmate!";
  else if (gameState.is_stalemate) status = "Stalemate";
  else if (gameState.is_check) status = "Check!";
  else if (gameState.is_game_over) status = gameState.result;
  document.getElementById("status-indicator").textContent = status;

  const moveList = document.getElementById("move-list");
  moveList.innerHTML = "";
  gameState.move_history.forEach((san) => {
    const li = document.createElement("li");
    li.textContent = san;
    moveList.appendChild(li);
  });
}

// ---------- init ----------

document.addEventListener("DOMContentLoaded", () => {
  initBoard();
  startNewGame();
  document.getElementById("new-game-btn").addEventListener("click", startNewGame);
});