// HTMLの属性から情報を取得
const mainEl = document.querySelector('[data-room-name]');
const roomName = mainEl ? mainEl.getAttribute('data-room-name') : "test";
const gameType = 'tictactoe';

console.log(`接続先: ws://${window.location.host}/ws/${gameType}/${roomName}/`);

const gameSocket = new WebSocket(
    `ws://${window.location.host}/ws/${gameType}/${roomName}/`
);

// プレイヤー管理用
let p1Name = null;
let p2Name = null;

gameSocket.onopen = function(e) {
    updateStatus("サーバーに接続しました。対戦相手を待機中...");
};

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    // 1. ゲーム状態の受信 (盤面更新)
    if (data.type === 'game_state') {
        updateBoard(data.board);
        
        if (data.game_over) {
            if (data.winner) {
                updateStatus(`🏆 ${data.winner} の勝ち！`);
                highlightWin(data.winning_line);
            } else {
                updateStatus("引き分け！");
            }
            document.getElementById('reset-btn').style.display = 'inline-block';
        } else {
            // ターン表示
            const turnMark = data.current_player; // 'X' or 'O'
            updateStatus(`現在のターン: ${turnMark}`);
            document.getElementById('reset-btn').style.display = 'none';
        }
    }
    // 2. プレイヤー参加通知 (名前表示の更新)
    else if (data.type === 'player_joined') {
        updatePlayerNames(data.username, data.rating);
    }
    // 3. レート更新通知
    else if (data.type === 'rating_update') {
        // { "UserA": 1520, "UserB": 1480 } のようなデータが来る想定
        // 簡易的にアラートで通知
        alert("対戦終了！レートが更新されました。");
    }
};

// 盤面描画
function updateBoard(boardData) {
    const cells = document.querySelectorAll('.cell');
    cells.forEach((cell, index) => {
        const mark = boardData[index];
        cell.textContent = mark || "";
        
        // クラスのリセットと適用
        cell.className = 'cell'; 
        if (mark) {
            cell.classList.add('taken');
            cell.classList.add(mark === 'X' ? 'text-x' : 'text-o');
        }
    });
}

// 名前表示の更新 (簡易ロジック: 空いている方に埋める)
function updatePlayerNames(username, rating) {
    const p1NameEl = document.getElementById('p1-name');
    const p2NameEl = document.getElementById('p2-name');
    
    // 既に表示されている名前なら何もしない
    if (p1NameEl.textContent === username || p2NameEl.textContent === username) return;

    if (p1NameEl.textContent === "Waiting...") {
        p1NameEl.textContent = username;
        document.getElementById('p1-rate').textContent = `R: ${rating}`;
    } else if (p2NameEl.textContent === "Waiting...") {
        p2NameEl.textContent = username;
        document.getElementById('p2-rate').textContent = `R: ${rating}`;
        updateStatus("対戦開始！");
    }
}

function updateStatus(msg) {
    document.getElementById('game-status').textContent = msg;
}

function highlightWin(line) {
    if (!line) return;
    line.forEach(idx => {
        const cell = document.querySelector(`.cell[data-index="${idx}"]`);
        if (cell) cell.classList.add('win');
    });
}

// 送信アクション
function sendMove(index) {
    if (gameSocket.readyState === WebSocket.OPEN) {
        gameSocket.send(JSON.stringify({
            'type': 'move',
            'position': index
        }));
    }
}

function sendReset() {
    gameSocket.send(JSON.stringify({'type': 'reset'}));
}