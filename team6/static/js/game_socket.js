// team6/static/js/game_socket.js

const mainEl = document.querySelector('[data-room-name]');
const roomName = mainEl ? mainEl.getAttribute('data-room-name') : "test";
const myUsername = document.getElementById('my-username').value;
const gameType = 'tictactoe';

const gameSocket = new WebSocket(
    `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${gameType}/${roomName}/`
);

gameSocket.onopen = function(e) {
    updateStatus("サーバーに接続しました。対戦相手を待機中...");
};

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'game_state') {
        updateBoard(data.board);
        updatePlayerNames(data.player_x, data.player_o);
        
        if (data.game_over) {
            if (data.winner === 'draw') {
                updateStatus("🔥 引き分け！");
            } else {
                const winnerName = data.winner === 'X' ? data.player_x : data.player_o;
                updateStatus(`🏆 ${winnerName} (${data.winner}) の勝利！`);
            }
            document.getElementById('reset-btn').style.display = 'inline-block';
        } else {
            // --- 課題1&2: ターン表示と操作制限 ---
            const currentMark = data.current_player;
            const currentName = currentMark === 'X' ? data.player_x : data.player_o;
            
            if (currentName) {
                const isMyTurn = (currentName === myUsername);
                let statusMsg = `現在のターン: ${currentMark} (${currentName})`;
                if (isMyTurn) statusMsg += " ✨ あなたの番です！";
                updateStatus(statusMsg);
                
                // 自分のターンでない時は盤面のクリックを無効化し、少し透明にする
                const boardEl = document.getElementById('online-board');
                if (isMyTurn) {
                    boardEl.style.opacity = "1.0";
                    boardEl.style.pointerEvents = "auto";
                } else {
                    boardEl.style.opacity = "0.6";
                    boardEl.style.pointerEvents = "none";
                }
            } else {
                updateStatus("対戦相手を待っています...");
            }
            document.getElementById('reset-btn').style.display = 'none';
        }
    }
};

function updateBoard(boardData) {
    const cells = document.querySelectorAll('.cell');
    cells.forEach((cell, index) => {
        const mark = boardData[index];
        cell.textContent = mark === ' ' ? "" : mark;
        cell.className = 'cell'; 
        if (mark !== ' ') {
            cell.classList.add('taken');
            cell.classList.add(mark === 'X' ? 'text-x' : 'text-o');
        }
    });
}

function updatePlayerNames(pX, pO) {
    const p1NameEl = document.getElementById('p1-name');
    const p2NameEl = document.getElementById('p2-name');
    if (pX) p1NameEl.textContent = pX;
    if (pO) {
        p2NameEl.textContent = pO;
    } else {
        p2NameEl.textContent = "待機中...";
    }
}

function updateStatus(msg) {
    document.getElementById('game-status').textContent = msg;
}

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