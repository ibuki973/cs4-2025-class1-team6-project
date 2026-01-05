// team6/static/js/hb_socket.js

const mainEl = document.querySelector('[data-room-name]');
const roomName = mainEl.getAttribute('data-room-name');
const myUsername = document.getElementById('my-username').value;
const gameSocket = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/hitandblow/${roomName}/`);

let currentInput = [];
let gamePhase = 'waiting';

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    // フェーズ管理
    gamePhase = data.phase;
    updateUI(data);
};

function updateUI(data) {
    document.getElementById('p1-name').textContent = data.player_x || "Waiting...";
    document.getElementById('p2-name').textContent = data.player_o || "Waiting...";
    
    const inputSection = document.getElementById('input-section');
    const statusText = document.getElementById('game-status');
    const submitBtn = document.getElementById('submit-btn');

    if (gamePhase === 'setup') {
        inputSection.style.display = 'block';
        const isSet = (myUsername === data.player_x ? data.secret_x_set : data.secret_o_set);
        statusText.textContent = isSet ? "相手の設定を待っています..." : "自分の秘密の3桁を決めてください";
        submitBtn.disabled = (currentInput.length !== 3 || isSet);
    } 
    else if (gamePhase === 'playing') {
        inputSection.style.display = 'block';
        const isMyTurn = (data.current_turn === 'X' && myUsername === data.player_x) || (data.current_turn === 'O' && myUsername === data.player_o);
        statusText.innerHTML = isMyTurn ? "<span class='text-success'>あなたの番です！相手の数字を予想してください</span>" : "相手が考え中です...";
        submitBtn.disabled = (currentInput.length !== 3 || !isMyTurn);
    }

    if (data.game_over) {
        statusText.innerHTML = `🏆 終了！勝者: ${data.winner}`;
        inputSection.style.display = 'none';
    }

    // 履歴更新
    updateHistory(data.history);
}

function pressKey(num) {
    if (currentInput.length < 3 && !currentInput.includes(parseInt(num))) {
        currentInput.push(parseInt(num));
        updateDigitDisplay();
    }
}

function clearInput() {
    currentInput = [];
    updateDigitDisplay();
}

function updateDigitDisplay() {
    const display = document.getElementById('digit-display');
    display.textContent = currentInput.join(" ") + " _ ".repeat(3 - currentInput.length);
    document.getElementById('submit-btn').disabled = (currentInput.length !== 3);
}

function submitAction() {
    const type = (gamePhase === 'setup') ? 'set_secret' : 'guess';
    gameSocket.send(JSON.stringify({
        'type': type,
        'value': currentInput
    }));
    currentInput = [];
    updateDigitDisplay();
}

function updateHistory(history) {
    const list = document.getElementById('history-list');
    list.innerHTML = "";
    history.slice().reverse().forEach(item => {
        const li = document.createElement('li');
        li.className = "history-item";
        li.innerHTML = `
            <span><strong>${item.user}</strong>: ${item.guess}</span>
            <span>
                <span class="badge badge-hit">${item.hit} Hit</span>
                <span class="badge badge-blow">${item.blow} Blow</span>
            </span>
        `;
        list.appendChild(li);
    });
}