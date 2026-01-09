// team6/static/js/hb_socket.js

const mainEl = document.querySelector('[data-room-name]');
const roomName = mainEl.getAttribute('data-room-name');
const myUsernameRaw = document.getElementById('my-username').value;
const myUsername = myUsernameRaw.trim().toLowerCase();
const gameSocket = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/hitandblow/${roomName}/`);

let currentInput = [];
let gamePhase = 'waiting';
window.isGameOver = false; // グローバル変数にしてHTMLから見えるようにする

// ブラウザを閉じる時の警告
window.onbeforeunload = function() {
    if (gamePhase !== 'waiting' && !window.isGameOver) {
        return "試合を離脱すると敗北となります。本当によろしいですか？";
    }
};

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log("HB Message Received:", data);

    if (data.type === 'game_start') {
        showStartAnimation(data.player_x, data.player_o);
    }
    else if (data.type === 'player_left') {
        window.isGameOver = true;
        if (data.left_user.toLowerCase() !== myUsername) {
            const oppModal = new bootstrap.Modal(document.getElementById('opponentRetiredModal'));
            oppModal.show();
        }
    }
    else {
        gamePhase = data.phase || gamePhase;
        window.isGameOver = data.game_over || false;
        updateUI(data);
    }
};

// --- 以下、重複を避けるため既存のUI更新系関数のみ残す ---

function showStartAnimation(pX, pO) {
    const old = document.getElementById('game-start-overlay');
    if (old) old.remove();
    const overlay = document.createElement('div');
    overlay.id = 'game-start-overlay';
    overlay.innerHTML = `
        <div class="animation-container" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:10000;display:flex;flex-direction:column;justify-content:center;align-items:center;color:white;">
            <h1 style="font-size:4rem;font-weight:900;">BATTLE START!</h1>
            <div style="font-size:2rem;margin-top:20px;">${pX} VS ${pO || '...'}</div>
            <div style="margin-top:30px;font-size:1.5rem;background:white;color:black;padding:10px 30px;border-radius:50px;">数字を決めてください！</div>
        </div>
    `;
    document.body.appendChild(overlay);
    setTimeout(() => {
        overlay.style.transition = "opacity 0.8s";
        overlay.style.opacity = "0";
        setTimeout(() => overlay.remove(), 800);
    }, 2500);
}

function updateUI(data) {
    document.getElementById('p1-name').textContent = data.player_x || "Waiting...";
    document.getElementById('p2-name').textContent = data.player_o || "Waiting...";
    document.getElementById('p1-status').textContent = data.secret_x_set ? "セット完了" : "準備中";
    document.getElementById('p2-status').textContent = data.secret_o_set ? "セット完了" : "準備中";

    const inputSection = document.getElementById('input-section');
    const statusText = document.getElementById('game-status');
    const submitBtn = document.getElementById('submit-btn');
    const resetBtn = document.getElementById('reset-btn');

    // ゲーム終了時の処理
    if (data.game_over) {
        statusText.innerHTML = `🏆 BATTLE END! 勝者: <span class='text-primary'>${data.winner}</span>`;
        inputSection.style.display = 'none';
        resetBtn.style.display = 'inline-block'; // ボタンを表示
        window.isGameOver = true;
        updateHistory(data.history || []);
        return;
    }

    // ゲーム継続中・リセット後の処理
    resetBtn.style.display = 'none'; // ボタンを隠す
    window.isGameOver = false;

    if (gamePhase === 'setup') {
        inputSection.style.display = 'block';
        const isSet = (myUsername === (data.player_x || "").toLowerCase() ? data.secret_x_set : data.secret_o_set);
        statusText.textContent = isSet ? "相手の入力を待っています..." : "自分の秘密の3桁をセットしてください";
        submitBtn.disabled = (currentInput.length !== 3 || isSet);
    } 
    else if (gamePhase === 'playing') {
        inputSection.style.display = 'block';
        const currentTurnUser = (data.current_turn === 'X' ? data.player_x : data.player_o) || "";
        const isMyTurn = (currentTurnUser.toLowerCase() === myUsername);
        statusText.innerHTML = isMyTurn ? "<span class='text-success fw-bold'>あなたの番です！予想を入力</span>" : `<span class='text-muted'>${currentTurnUser} が考え中...</span>`;
        submitBtn.disabled = (currentInput.length !== 3 || !isMyTurn);
    }

    updateHistory(data.history || []);
}

// 追加: リセット信号の送信
function sendReset() {
    if (gameSocket.readyState === WebSocket.OPEN) {
        gameSocket.send(JSON.stringify({
            'type': 'reset'
        }));
    }
}

function pressKey(num) {
    const n = parseInt(num);
    if (currentInput.length < 3 && !currentInput.includes(n)) {
        currentInput.push(n);
        updateDigitDisplay();
    }
}

function clearInput() {
    currentInput = [];
    updateDigitDisplay();
}

function updateDigitDisplay() {
    const display = document.getElementById('digit-display');
    let str = currentInput.join(" ");
    for(let i=currentInput.length; i<3; i++) str += " _";
    display.textContent = str;
    document.getElementById('submit-btn').disabled = (currentInput.length !== 3);
}

function submitAction() {
    const type = (gamePhase === 'setup') ? 'set_secret' : 'guess';
    gameSocket.send(JSON.stringify({'type': type, 'value': currentInput}));
    currentInput = [];
    updateDigitDisplay();
}

function updateHistory(history) {
    const list = document.getElementById('history-list');
    list.innerHTML = "";
    [...history].reverse().forEach(item => {
        const li = document.createElement('li');
        li.className = "history-item";
        li.innerHTML = `<span><strong>${item.user}</strong>: ${item.guess}</span>
            <span><span class="badge badge-hit">${item.hit} Hit</span><span class="badge badge-blow">${item.blow} Blow</span></span>`;
        list.appendChild(li);
    });
}