document.addEventListener('DOMContentLoaded', () => {
    const roomNameData = document.getElementById('room-name-data');
    const userEl = document.getElementById('my-username');

    if (!roomNameData || !userEl) {
        console.error("必要な要素が見つかりません");
        return;
    }

    const roomName = roomNameData.textContent.trim();
    const myUsername = userEl.value;

    const gameSocket = new WebSocket(
        `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/ecard/${roomName}/`
    );

    gameSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);

        // 1. 最初の手札を表示する処理（これが抜けていました）
        if (data.type === 'initial_state') {
            const sideLabel = (data.side === 'emperor_side' ? "皇帝側" : "奴隷側");
            document.getElementById('side-badge').innerText = sideLabel;
            updateUI(data.hand, gameSocket);
            document.getElementById('status-msg').innerText = "カードを選んでください";
        }

        // 2. 毎回の判定結果の処理
        if (data.type === 'round_result') {
            alert(data.message);
            
            if (data.is_over) {
                // ゲーム終了時：リセットボタンを表示
                document.getElementById('status-msg').innerHTML = 
                    `<div class="text-danger fw-bold fs-4">${data.message}</div>
                     <button class="btn btn-warning btn-lg mt-3 shadow" onclick="location.reload()">もう一度遊ぶ</button>`;
                document.getElementById('my-cards').innerHTML = ""; 
            } else {
                // 継続時：減った後の新しい手札でボタンを再作成
                updateUI(data.new_hand, gameSocket);
                document.getElementById('status-msg').innerText = "次のカードを選んでください";
            }
        }

        // 3. サーバー側からリセット命令が来た場合
        if (data.type === 'game_reset') {
            window.location.reload();
        }
    };

    // WebSocketが閉じた時のエラー表示
    gameSocket.onclose = function(e) {
        console.error("WebSocket closed unexpectedly");
        document.getElementById('status-msg').innerText = "接続が切れました。再読み込みしてください。";
    };
});

// ボタン（手札）を生成する関数
function updateUI(hand, socket) {
    const container = document.getElementById('my-cards');
    if (!container) return;
    
    container.innerHTML = "";
    hand.forEach(card => {
        const btn = document.createElement('button');
        btn.className = "btn btn-outline-dark p-4 fw-bold card-btn"; // スタイル用クラス追加
        btn.style.minWidth = "100px";
        btn.innerText = (card === 'E' ? "皇帝" : (card === 'S' ? "奴隷" : "市民"));
        
        btn.onclick = () => {
            socket.send(JSON.stringify({'type': 'play_card', 'card': card}));
            document.getElementById('status-msg').innerText = "提出済み。相手を待っています...";
            // 二重送信防止：全ボタンを無効化
            document.querySelectorAll('#my-cards button').forEach(b => b.disabled = true);
        };
        container.appendChild(btn);
    });
}