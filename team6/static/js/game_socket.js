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

    if (data.type === 'opponent_retired') {
        // 1. モーダルの要素を取得して表示
        const retiredModalEl = document.getElementById('opponentRetiredModal');
        const retiredModal = new bootstrap.Modal(retiredModalEl);
        retiredModal.show();

        // 2. 3000ミリ秒（3秒）待ってからメニューへ遷移させたいときはこれをオンにする
        // setTimeout(() => {
        //    window.location.href = "/tictactoe/";
        //}, 3000);
        
        return;
    }
    
    if (data.type === 'game_start') {
        showStartAnimation(data.player_x, data.player_o);
    }
    else if (data.type === 'game_state') {
        updateBoard(data.board, data.winning_line);
        updatePlayerNames(data.player_x, data.player_o);
        
        if (data.game_over) {
            // 切断(リロード)による終了で、かつ自分が負けの場合の判定
            // 自分のマークを特定 ('X' か 'O' か)
            let myMark = null;
            if (data.player_x === myUsername) {
                myMark = 'X';
            } else if (data.player_o === myUsername) {
                myMark = 'O';
            }

            // end_reason が 'retired' で、勝者が自分じゃない (=自分が切断した) 場合
            if (data.end_reason === 'retired' && data.winner !== myMark && data.winner !== 'draw') {
                const selfRetiredModalEl = document.getElementById('selfRetiredModal');
                // HTMLに追加済みかチェックしてから表示
                if (selfRetiredModalEl) {
                    new bootstrap.Modal(selfRetiredModalEl).show();
                }
                // これ以降の通常の勝敗表示処理を行わないように return しても良いですし、
                // 裏で表示が変わっていてもモーダルが被さるのでそのままでも大丈夫です。
            }

            if (data.winner === 'draw') {
                updateStatus("引き分け！");
            } else {
                const winnerName = data.winner === 'X' ? data.player_x : data.player_o;
                const displayMark = data.winner === 'X' ? '✖' : '〇';
                const colorClass = data.winner === 'X' ? 'text-x' : 'text-o';
                updateStatus(`勝者: <span class="${colorClass} fw-bold">${winnerName} (${displayMark})</span>`);
            }

            const resetBtn = document.getElementById('reset-btn');
            resetBtn.style.display = 'inline-block';

            // 追加：リセット投票の状態によってボタンの表示を切り替える
            // data.reset_requested はサーバー側の consumers.py で追加したリストです
            if (data.reset_requested && data.reset_requested.includes(myUsername)) {
                resetBtn.disabled = true;
                resetBtn.textContent = "相手の同意を待っています...";
            } else {
                resetBtn.disabled = false;
                resetBtn.textContent = "もう一度遊ぶ";
            }
            
            // ボードの操作を無効化
            document.getElementById('online-board').style.pointerEvents = "none";
        } else {
            const currentMark = data.current_player; // 'X' or 'O'
            const currentName = currentMark === 'X' ? data.player_x : data.player_o;
            
            if (currentName) {
                const isMyTurn = (currentName === myUsername);
                
                // 課題解決: ✖ (X) は青字 (text-x)、〇 (O) は赤字 (text-o)
                const displayMark = currentMark === 'X' ? '✖' : '〇';
                const colorClass = currentMark === 'X' ? 'text-x' : 'text-o';
                
                let statusMsg = `現在のターン: <span class="${colorClass} fw-bold">${displayMark} (${currentName})</span>`;
                if (isMyTurn) statusMsg += " <span class='text-dark ms-2'>✨ あなたの番です</span>";
                
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
    const oldOverlay = document.getElementById('game-start-overlay');
    if (oldOverlay) oldOverlay.remove();

    const overlay = document.createElement('div');
    overlay.id = 'game-start-overlay';
    overlay.innerHTML = `
        <div class="animation-container">
            <h1 class="anim-title">BATTLE START!</h1>
            <div class="player-vs">
                <div class="vs-player text-primary">
                    <span class="mark">✖</span>
                    <span class="name">${pX}</span>
                </div>
                <div class="vs-icon">VS</div>
                <div class="vs-player text-danger">
                    <span class="mark">〇</span>
                    <span class="name">${pO || '...'}</span>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    setTimeout(() => {
        overlay.classList.add('fade-out');
        setTimeout(() => overlay.remove(), 800);
    }, 2500);
}

// モーダルを表示する関数
function confirmExit() {
    // ゲームが終了している場合はそのまま戻る
    if (document.getElementById('reset-btn').style.display !== 'none') {
        window.location.href = "/tictactoe/";
        return;
    }
    // ゲーム中の場合はモーダルを表示
    const exitModal = new bootstrap.Modal(document.getElementById('exitModal'));
    exitModal.show();
}

// モーダルで「戻る」を押した時の処理
function executeExit() {
    if (gameSocket.readyState === WebSocket.OPEN) {
        // サーバーに「降参」を通知
        gameSocket.send(JSON.stringify({
            'type': 'surrender'
        }));
    }
    // メニューへ遷移
    window.location.href = "/tictactoe/";
}

function updateBoard(boardData, winningLine = []) {
    const cells = document.querySelectorAll('.cell');
    cells.forEach((cell, index) => {
        const mark = boardData[index];
        
        // 内部の 'X', 'O' を表示用の記号に変換
        let displayMark = "";
        if (mark === 'X') displayMark = "✖";
        if (mark === 'O') displayMark = "〇";
        
        cell.textContent = displayMark;
        cell.className = 'cell'; 
        
        if (mark !== ' ') {
            cell.classList.add('taken');
            cell.classList.add(mark === 'X' ? 'text-x' : 'text-o');
        }

        if (winningLine && winningLine.includes(index)) {
            cell.classList.add('winning-cell');
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

// 課題解決: textContent ではなく innerHTML を使うように変更
function updateStatus(msg) {
    document.getElementById('game-status').innerHTML = msg;
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