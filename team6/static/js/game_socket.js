// team6/static/js/game_socket.js

// data-room-name 属性を持つ要素を確実に探す
const container = document.getElementById('game-container');
const roomName = container ? container.getAttribute('data-room-name') : null;

if (!roomName) {
    console.error("エラー: ルーム名が取得できません。URLを確認してください。");
} else {
    const gameType = 'tictactoe';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//${window.location.host}/ws/${gameType}/${roomName}/`;
    
    console.log("Connecting to:", socketUrl);
    const gameSocket = new WebSocket(socketUrl);

    let myMark = null; 
    const myUsername = document.getElementById('my-username').value;

    gameSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'player_joined') {
            updatePlayerUI(data.username, data.rating);
            determineMyMark();
            checkAndShowStartEffect();
        } else if (data.type === 'game_state') {
            updateBoard(data.board);
            determineMyMark();
            if (data.game_over) {
                handleGameOver(data);
            } else {
                updateTurnDisplay(data.current_player);
                applyTurnLock(data.current_player);
            }
        }
    };

    // --- 必要な関数群 ---
    window.sendMove = function(index) {
        if (gameSocket.readyState === WebSocket.OPEN && myMark) {
            gameSocket.send(JSON.stringify({'type': 'move', 'position': index, 'player_mark': myMark}));
        }
    };

    window.sendReset = function() {
        if (gameSocket.readyState === WebSocket.OPEN) {
            gameSocket.send(JSON.stringify({'type': 'reset'}));
        }
    };

    function determineMyMark() {
        const p1 = document.getElementById('p1-name').textContent;
        const p2 = document.getElementById('p2-name').textContent;
        if (p1 === myUsername) myMark = 'X';
        else if (p2 === myUsername) myMark = 'O';
    }

    function updatePlayerUI(username, rating) {
        const p1 = document.getElementById('p1-name');
        const p2 = document.getElementById('p2-name');
        if (p1.textContent === username || p2.textContent === username) return;
        if (p1.textContent === "Waiting...") {
            p1.textContent = username;
            document.getElementById('p1-rate').textContent = `R: ${rating}`;
        } else if (p2.textContent === "Waiting...") {
            p2.textContent = username;
            document.getElementById('p2-rate').textContent = `R: ${rating}`;
        }
    }

    function updateTurnDisplay(currentMark) {
        const p1Name = document.getElementById('p1-name').textContent;
        const p2Name = document.getElementById('p2-name').textContent;
        const currentPlayerName = (currentMark === 'X') ? p1Name : p2Name;
        document.getElementById('game-status').textContent = `現在のターン: ${currentPlayerName} (${currentMark})`;
    }

    function applyTurnLock(currentMark) {
        const boardEl = document.getElementById('online-board');
        if (myMark && currentMark === myMark) {
            boardEl.style.opacity = "1";
            boardEl.style.pointerEvents = "auto";
        } else {
            boardEl.style.opacity = "0.5";
            boardEl.style.pointerEvents = "none";
        }
    }

    function updateBoard(boardData) {
        const cells = document.querySelectorAll('.cell');
        cells.forEach((cell, index) => {
            const mark = boardData[index];
            cell.textContent = (mark === ' ' || !mark) ? '' : mark;
            cell.className = 'cell'; 
            if (mark && mark !== ' ') {
                cell.classList.add('taken', mark === 'X' ? 'text-x' : 'text-o');
            }
        });
    }

    function checkAndShowStartEffect() {
        const p1 = document.getElementById('p1-name').textContent;
        const p2 = document.getElementById('p2-name').textContent;
        if (p1 !== "Waiting..." && p2 !== "Waiting..." && myMark) {
            const overlay = document.getElementById('start-overlay');
            if (overlay && overlay.style.display === 'none') showStartEffect();
        }
    }

    function showStartEffect() {
        const overlay = document.getElementById('start-overlay');
        const text = document.getElementById('overlay-text');
        overlay.style.display = 'flex';
        text.textContent = `You are ${myMark === 'X' ? '先行 (X)' : '後攻 (O)'}`;
        text.style.color = myMark === 'X' ? "#0d6efd" : "#dc3545";
        text.classList.add('pop-in');
        setTimeout(() => {
            overlay.style.opacity = '0';
            overlay.style.transition = '0.8s';
            setTimeout(() => { overlay.style.display = 'none'; }, 800);
        }, 2200);
    }

    function handleGameOver(data) {
        const statusEl = document.getElementById('game-status');
        if (data.winner === 'draw') statusEl.textContent = "Draw! (引き分け)";
        else {
            const winnerName = (data.winner === 'X') ? document.getElementById('p1-name').textContent : document.getElementById('p2-name').textContent;
            statusEl.innerHTML = `🏆 <span>${winnerName}</span> の勝ち！`;
            if (data.winning_line) {
                data.winning_line.forEach(idx => { document.querySelectorAll('.cell')[idx].classList.add('win'); });
            }
        }
        document.getElementById('reset-btn').style.display = 'inline-block';
        document.getElementById('online-board').style.pointerEvents = "none";
    }
}