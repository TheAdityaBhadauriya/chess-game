const API_BASE = "http://127.0.0.1:5000/api";

let board = null;
let gameId = null;
let gameState = null;
let legalMoves = [];
let selectedSquare = null;
let justDragged = false;

// ---------- board setup ----------

function initBoard() {
  board = Chessboard("board", {
    position: "start",
    draggable: true,
    pieceTheme: "https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png",
    onDrop: onDrop,
    onDragStart: onDragStart,
    onMouseoverSquare: onMouseoverSquare,
    onMouseoutSquare: onMouseoutSquare,
  });
}

const PIECE_UNICODE = {
  wP: "♙", wN: "♘", wB: "♗", wR: "♖", wQ: "♕", wK: "♔",
  bP: "♟", bN: "♞", bB: "♝", bR: "♜", bQ: "♛", bK: "♚",
};

const STARTING_COUNTS = {
  wP: 8, wN: 2, wB: 2, wR: 2, wQ: 1,
  bP: 8, bN: 2, bB: 2, bR: 2, bQ: 1,
};

function onMouseoverSquare(square) {
  if (!gameState || gameState.is_game_over) return;
  if (selectedSquare) return; // don't override the persistent selection highlight on hover
  const targets = legalTargetsFrom(square);
  if (targets.length === 0) return;
  highlightSquares([square, ...targets]);
}

function onMouseoutSquare() {
  if (selectedSquare) return; // keep selection highlights visible until move is made
  clearHighlights();
}


function onDragStart(source, piece) {
  if (gameState && gameState.is_game_over) return false;
  return true; // let onDrop handle all real legality checks (for both drags and clicks)
}


// ---------- API calls ----------

async function startNewGame() {
  const res = await fetch(`${API_BASE}/new_game`, { method: "POST" });
  gameState = await res.json();
  gameId = gameState.game_id;
  board.position(gameState.fen);
  await refreshLegalMoves();
  updateSidePanel();
}

function onDrop(source, target) {
  if (target === "offboard") return "snapback";

  if (source === target) {
    return handleSquareClick(source);
  }

  const result = handleDragMove(source, target);
  justDragged = true;
  setTimeout(() => { justDragged = false; }, 100);
  return result;
}

function handleSquareClick(square) {
  if (gameState.is_game_over) return "snapback";

  if (selectedSquare && selectedSquare !== square) {
    const isPromotion = checkIfPromotion(selectedSquare, square);
    const matchExists = legalMoves.some((m) => m.startsWith(selectedSquare + square));

    if (matchExists) {
      const from = selectedSquare;
      selectedSquare = null;
      clearHighlights();
      if (isPromotion) {
        showPromotionPicker(from, square);
      } else {
        playMoveOnServer(from + square);
      }
      return "snapback";
    }
  }

  clearHighlights();
  const targets = legalTargetsFrom(square);
  if (targets.length === 0) {
    selectedSquare = null;
    return "snapback";
  }
  selectedSquare = square;
  highlightSquares([square, ...targets]);
  return "snapback";
}

function handleDragMove(source, target) {
  selectedSquare = null;
  clearHighlights();

  const isPromotion = checkIfPromotion(source, target);
  if (!legalMoves.some((m) => m.startsWith(source + target))) {
    return "snapback";
  }
  if (isPromotion) {
    showPromotionPicker(source, target);
    return "snapback";
  }
  playMoveOnServer(source + target);
}

function checkIfPromotion(source, target) {
  const piece = board.position()[source];
  if (!piece) return false;
  const isPawn = piece[1] === "P";
  const targetRank = target[1];
  return isPawn && (targetRank === "8" || targetRank === "1");
}

function showPromotionPicker(source, target) {
  const pieceColor = board.position()[source][0]; // "w" or "b"
  const choice = prompt("Promote to: q (queen), r (rook), b (bishop), n (knight)", "q");
  const validChoice = ["q", "r", "b", "n"].includes(choice) ? choice : "q";
  const uciMove = source + target + validChoice;

  if (!legalMoves.some((m) => m.startsWith(source + target))) {
    board.position(gameState.fen); // snap back, wasn't actually legal
    return;
  }

  playMoveOnServer(uciMove);
}

async function playMoveOnServer(uciMove) {
  const res = await fetch(`${API_BASE}/game/${gameId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ move: uciMove }),
  });

  if (!res.ok) {
    // shouldn't happen since we pre-validated, but just in case
    board.position(gameState.fen);
    return;
  }

  gameState = await res.json();
  updateSidePanel();
  board.position(gameState.fen);
  await refreshLegalMoves();

  if (!gameState.is_game_over) {
    setTimeout(requestBotMove, 300);
  }
}

async function loadDifficultyLevels() {
  const res = await fetch(`${API_BASE}/difficulty_levels`);
  const levels = await res.json();
  const select = document.getElementById("difficulty-select");
  select.innerHTML = "";

  const tiers = [
    { label: "Beginner", range: [1, 2] },
    { label: "Intermediate", range: [3, 4] },
    { label: "Advanced", range: [5, 6] },
    { label: "Expert", range: [7, 8] },
    { label: "Master", range: [9, 10] },
  ];

  tiers.forEach((tier) => {
    const group = document.createElement("optgroup");
    group.label = tier.label;
    for (let lvl = tier.range[0]; lvl <= tier.range[1]; lvl++) {
      if (!levels[lvl]) continue;
      const opt = document.createElement("option");
      opt.value = lvl;
      opt.textContent = `${levels[lvl].name} (~${levels[lvl].rating})`;
      group.appendChild(opt);
    }
    select.appendChild(group);
  });
}
async function requestBotMove() {
  const level = parseInt(document.getElementById("difficulty-select").value, 10);

  const res = await fetch(`${API_BASE}/game/${gameId}/bot_move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level }),
  });

  if (!res.ok) return;

  gameState = await res.json();
  board.position(gameState.fen);
  updateSidePanel();
  await refreshLegalMoves();
}

async function refreshLegalMoves() {
  const res = await fetch(`${API_BASE}/game/${gameId}/legal_moves`);
  const data = await res.json();
  legalMoves = data.moves; // array of UCI strings, e.g. ["e2e3", "e2e4", ...]
}

function legalTargetsFrom(square) {
  return legalMoves
    .filter((m) => m.startsWith(square))
    .map((m) => m.substring(2, 4));
}

function highlightSquares(squares) {
  squares.forEach((sq) => {
    $(`#board .square-${sq}`).addClass("highlight-move");
  });
}

function clearHighlights() {
  $("#board .square-55d63").removeClass("highlight-move");
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
  document.getElementById("analyze-btn").style.display = gameState.is_game_over ? "inline-block" : "none";
  updateCapturedPieces();
}

async function fetchAnalysis() {
  const res = await fetch(`${API_BASE}/game/${gameId}/analysis`);
  if (!res.ok) return;
  const analysis = await res.json();
  renderAnalysis(analysis);
}

async function resignGame() {
  if (!gameState || gameState.is_game_over) return;

  const resigningColor = gameState.turn; // whoever's turn it is resigns
  const res = await fetch(`${API_BASE}/game/${gameId}/resign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ color: resigningColor }),
  });

  if (!res.ok) return;
  gameState = await res.json();
  updateSidePanel();
}

function updateCapturedPieces() {
  const position = board.position();
  const currentCounts = {};

  Object.values(position).forEach((piece) => {
    currentCounts[piece] = (currentCounts[piece] || 0) + 1;
  });

  let capturedByWhite = ""; // black pieces White has taken
  let capturedByBlack = ""; // white pieces Black has taken

  Object.keys(STARTING_COUNTS).forEach((piece) => {
    const missing = STARTING_COUNTS[piece] - (currentCounts[piece] || 0);
    if (missing <= 0) return;
    const symbol = PIECE_UNICODE[piece].repeat(missing);
    if (piece.startsWith("b")) {
      capturedByWhite += symbol;
    } else {
      capturedByBlack += symbol;
    }
  });

  document.getElementById("captured-by-white").textContent = capturedByWhite;
  document.getElementById("captured-by-black").textContent = capturedByBlack;
}

function renderAnalysis(analysis) {
  document.getElementById("analysis-panel").style.display = "block";
  document.getElementById("opening-name").textContent =
    `${analysis.opening.name} (${analysis.opening.eco || "?"})`;
  document.getElementById("white-accuracy").textContent = analysis.white_accuracy;
  document.getElementById("black-accuracy").textContent = analysis.black_accuracy;

  drawEvalGraph(analysis.eval_graph);
  renderMoveBreakdown(analysis.moves);
}

function drawEvalGraph(evalGraph) {
  const svg = document.getElementById("eval-graph");
  const width = 600, height = 150;
  const maxEval = 500; // clamp display range to +/-500 centipawns for readability
  const points = evalGraph.map((point, i) => {
    const x = (i / (evalGraph.length - 1)) * width;
    const clamped = Math.max(-maxEval, Math.min(maxEval, point.eval));
    const y = height / 2 - (clamped / maxEval) * (height / 2);
    return `${x},${y}`;
  });

  svg.innerHTML = `
    <line x1="0" y1="${height / 2}" x2="${width}" y2="${height / 2}" stroke="#555" stroke-width="1" />
    <polyline points="${points.join(" ")}" fill="none" stroke="#7fb069" stroke-width="2" />
  `;
}

const CLASSIFICATION_COLORS = {
  best: "#7fb069",
  good: "#a3c9a8",
  inaccuracy: "#e6c229",
  mistake: "#e67e22",
  blunder: "#e74c3c",
};

function renderMoveBreakdown(moves) {
  const list = document.getElementById("analysis-move-list");
  list.innerHTML = "";
  moves.forEach((m) => {
    const li = document.createElement("li");
    li.textContent = `${m.san} (${m.player}) — ${m.classification}`;
    li.style.color = CLASSIFICATION_COLORS[m.classification] || "#eee";
    list.appendChild(li);
  });
}

// ---------- init ----------

document.addEventListener("DOMContentLoaded", () => {
  initBoard();
  startNewGame();
  loadDifficultyLevels();
  document.getElementById("new-game-btn").addEventListener("click", startNewGame);
  document.getElementById("analyze-btn").addEventListener("click", fetchAnalysis);
 $("#board").on("click", ".square-55d63", function () {
    if (justDragged) return;
    const classes = $(this).attr("class").split(" ");
    const squareClass = classes.find((c) => /^square-[a-h][1-8]$/.test(c));
    if (!squareClass) return;
    const square = squareClass.replace("square-", "");
    handleSquareClick(square);
  });
  document.getElementById("resign-btn").addEventListener("click", resignGame);
});