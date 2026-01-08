const mainEl = document.querySelector('[data-room-name]');
const roomName = mainEl ? mainEl.getAttribute('data-room-name') : "test";
const myUsername = document.getElementById('my-username').value;
const gameType = 'tictactoe';

const gameSocket = new WebSocket(
    `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${gameType}/${roomName}/`
);

let turnCountdown = null;

gameSocket.onopen = function(e) {
    updateStatus("サーバーに接続しました。対戦相手を待機中...");
};

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    // 相手が離脱した場合
    if (data.type === 'opponent_retired') {
        const retiredModalEl = document.getElementById('opponentRetiredModal');
        if (retiredModalEl) {
            new bootstrap.Modal(retiredModalEl).show();
        }
        return;
    }
    
    // ゲーム開始演出
    if (data.type === 'game_start') {
        const myMark = (data.player_x === myUsername) ? 'X' : 'O';
        triggerStartAnimation(myMark);
    }
    // ゲーム状態の更新
    else if (data.type === 'game_state') {
        updateBoard(data.board, data.winning_line);
        updatePlayerNames(data.player_x, data.player_o);
        
        if (data.game_over) {
            clearInterval(turnCountdown);
            const timerBox = document.getElementById('timer-box');
            if (timerBox) timerBox.style.display = 'none';

            // 自分が離脱（リロード等）して負けた場合
            let myMark = (data.player_x === myUsername) ? 'X' : 'O';
            if (data.end_reason === 'retired' && data.winner !== myMark && data.winner !== 'draw') {
                const selfRetiredModalEl = document.getElementById('selfRetiredModal');
                if (selfRetiredModalEl) new bootstrap.Modal(selfRetiredModalEl).show();
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
            if (resetBtn) {
                resetBtn.style.display = 'inline-block';
                if (data.reset_requested && data.reset_requested.includes(myUsername)) {
                    resetBtn.disabled = true;
                    resetBtn.textContent = "相手の同意を待っています...";
                } else {
                    resetBtn.disabled = false;
                    resetBtn.textContent = "もう一度遊ぶ";
                }
            }
            document.getElementById('online-board').style.pointerEvents = "none";
        } else {
            // 通常の手番処理
            const currentMark = data.current_player;
            const currentName = (currentMark === 'X') ? data.player_x : data.player_o;
            
            if (currentName) {
                const isMyTurn = (currentName === myUsername);
                
                // タイマー更新
                updateTimer(isMyTurn);

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
            }
            const resetBtn = document.getElementById('reset-btn');
            if (resetBtn) resetBtn.style.display = 'none';
        }
    }
};

function triggerStartAnimation(myMark) {
    const overlay = document.getElementById('game-start-overlay-new');
    const turnText = document.getElementById('turn-announcement');
    if (!overlay || !turnText) return;

    turnText.innerText = (myMark === 'X') ? "あなたは【先行 ✖】です" : "あなたは【後攻 〇】です";
    overlay.style.display = 'flex';
    overlay.style.opacity = "1";

    setTimeout(() => {
        overlay.style.transition = "opacity 0.8s";
        overlay.style.opacity = "0";
        setTimeout(() => { 
            overlay.style.display = 'none'; 
            overlay.style.opacity = "1";
        }, 800);
    }, 2000);
}

function updateTimer(isMyTurn) {
    clearInterval(turnCountdown);
    const timerBox = document.getElementById('timer-box');
    const timerCount = document.getElementById('timer-count');
    if (!timerBox || !timerCount) return;

    let timeLeft = 20;
    timerBox.style.display = 'block';
    timerCount.innerText = timeLeft;
    timerBox.firstElementChild.className = isMyTurn ? "badge rounded-pill bg-danger p-2 px-4" : "badge rounded-pill bg-secondary p-2 px-4";

    turnCountdown = setInterval(() => {
        timeLeft--;
        timerCount.innerText = timeLeft;
        if (timeLeft <= 0) {
            clearInterval(turnCountdown);
            if (isMyTurn) {
                alert("時間切れです！");
                executeExit(); // 自動降参
            }
        }
    }, 1000);
}

function confirmExit() {
    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn && resetBtn.style.display !== 'none') {
        window.location.href = "/tictactoe/";
        return;
    }
    const exitModalEl = document.getElementById('exitModal');
    if (exitModalEl) {
        new bootstrap.Modal(exitModalEl).show();
    }
}

function executeExit() {
    if (gameSocket.readyState === WebSocket.OPEN) {
        gameSocket.send(JSON.stringify({'type': 'surrender'}));
    }
    window.location.href = "/tictactoe/";
}

function updateBoard(boardData, winningLine = []) {
    const cells = document.querySelectorAll('.cell');
    cells.forEach((cell, index) => {
        const mark = boardData[index];
        let displayMark = (mark === 'X') ? "✖" : (mark === 'O' ? "〇" : "");
        
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
    if (p1NameEl && pX) p1NameEl.textContent = pX;
    if (p2NameEl) p2NameEl.textContent = pO ? pO : "待機中...";
}

function updateStatus(msg) {
    const statusEl = document.getElementById('game-status');
    if (statusEl) statusEl.innerHTML = msg;
}

function sendMove(index) {
    if (gameSocket.readyState === WebSocket.OPEN) {
        gameSocket.send(JSON.stringify({'type': 'move', 'position': index}));
    }
}

function sendReset() {
    if (gameSocket.readyState === WebSocket.OPEN) {
        gameSocket.send(JSON.stringify({'type': 'reset'}));
    }
}