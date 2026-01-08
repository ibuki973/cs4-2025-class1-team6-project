document.addEventListener('DOMContentLoaded', () => {
    const roomNameData = document.getElementById('room-name-data');
    const userEl = document.getElementById('my-username');
    if (!roomNameData || !userEl) return;

    const roomName = roomNameData.textContent.trim();
    const socketPath = '/ws/ecard/' + roomName + '/';
    const gameSocket = new WebSocket(
        (location.protocol === 'https:' ? 'wss:' : 'ws:') + window.location.host + socketPath
    );

    gameSocket.onopen = () => console.log("WebSocket接続成功！ 部屋:", roomName);

    gameSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log("受信データ:", data); // これで中身をチェック

        // 1. 初期化・同期
        if (data.type === 'initial_state') {
            const sideBadge = document.getElementById('side-badge');
            const statusMsg = document.getElementById('status-msg');

            // 陣営表示を更新
            if (sideBadge && data.side) {
                sideBadge.innerText = (data.side === 'emperor_side' ? "皇帝側" : "奴隷側");
                sideBadge.className = `badge ${data.side === 'emperor_side' ? 'bg-primary' : 'bg-danger'} p-2`;
            }

            // 2人揃っているかチェック
            // サーバー側から送られる data.is_ready を見て表示を切り替える
            if (data.is_ready) {
                statusMsg.innerText = "カードを選べ‥‥！";
                statusMsg.className = "alert alert-warning text-dark fw-bold";
                updateUI(data.hand, gameSocket); // 2人揃ったら手札を表示
            } else {
                statusMsg.innerText = "相手の接続を待機中‥‥ざわ‥‥";
                statusMsg.className = "alert alert-secondary";
            }

            // ポイント表示を更新
            if (typeof updatePointsUI === 'function') {
                updatePointsUI(data.points, data.opp_points);
            }
        }

        // 2. 判定結果
        if (data.type === 'round_result') {
            document.getElementById('status-msg').innerText = "開門‥‥‥‥！";
            setTimeout(() => {
                updatePointsUI(data.points, data.opp_points);
                alert(data.message);
                if (data.is_over) {
                    location.reload(); // シンプルにリロードしてリセット
                } else {
                    updateUI(data.new_hand, gameSocket);
                    document.getElementById('status-msg').innerText = "続行だ‥‥！";
                }
            }, 1000);
        }
    };
});

function updateUI(hand, socket) {
    const container = document.getElementById('my-cards');
    if (!container) return;
    container.innerHTML = "";
    if (!hand || hand.length === 0) return;

    hand.forEach(card => {
        const btn = document.createElement('button');
        btn.className = "btn btn-outline-dark p-4 fw-bold card-btn m-1";
        btn.style.minWidth = "110px";
        btn.innerText = (card === 'E' ? "皇帝" : (card === 'S' ? "奴隷" : "市民"));
        btn.onclick = () => {
            socket.send(JSON.stringify({'type': 'play_card', 'card': card}));
            document.getElementById('status-msg').innerText = "ざわ‥　ざわ‥‥（相手の選択待ち）";
            document.querySelectorAll('#my-cards button').forEach(b => b.disabled = true);
        };
        container.appendChild(btn);
    });
}

function updatePointsUI(mine, opp) {
    const ptElement = document.getElementById('star-count');
    if (!ptElement) return;
    ptElement.innerHTML = `
        <div class="d-flex justify-content-center gap-4 p-2 bg-dark rounded border border-secondary">
            <div class="text-warning">YOU: ${mine || 0} pt</div>
            <div class="text-danger">ENEMY: ${opp || 0} pt</div>
        </div>
    `;
}