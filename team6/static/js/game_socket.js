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
    
    // 1. ゲーム開始演出のハンドリング
    if (data.type === 'game_start') {
        showStartAnimation(data.player_x, data.player_o);
    }
    // 2. 通常の盤面更新
    else if (data.type === 'game_state') {
        updateBoard(data.board);
        updatePlayerNames(data.player_x, data.player_o);
        
        if (data.game_over) {
            if (data.winner === 'draw') {
                updateStatus("引き分け！");
            } else {
                const winnerName = data.winner === 'X' ? data.player_x : data.player_o;
                updateStatus(`勝者: ${winnerName} (${data.winner})`);
            }
            document.getElementById('reset-btn').style.display = 'inline-block';
        } else {
            const currentMark = data.current_player;
            const currentName = currentMark === 'X' ? data.player_x : data.player_o;
            
            if (currentName) {
                const isMyTurn = (currentName === myUsername);
                let statusMsg = `現在のターン: ${currentMark} (${currentName})`;
                if (isMyTurn) statusMsg += " (あなたの番です)";
                updateStatus(statusMsg);
                
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

function showStartAnimation(pX, pO) {
    // 既に演出が表示されている場合は削除
    const oldOverlay = document.getElementById('game-start-overlay');
    if (oldOverlay) oldOverlay.remove();

    const overlay = document.createElement('div');
    overlay.id = 'game-start-overlay';
    overlay.innerHTML = `
        <div class="animation-container">
            <h1 class="anim-title">BATTLE START!</h1>
            <div class="player-vs">
                <div class="vs-player text-primary">
                    <span class="mark">X</span>
                    <span class="name">${pX}</span>
                </div>
                <div class="vs-icon">VS</div>
                <div class="vs-player text-danger">
                    <span class="mark">O</span>
                    <span class="name">${pO || '...'}</span>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    // 2.5秒後に自動で消える
    setTimeout(() => {
        overlay.classList.add('fade-out');
        setTimeout(() => overlay.remove(), 800);
    }, 2500);
}

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