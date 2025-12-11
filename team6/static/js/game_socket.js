// team6/static/js/game_socket.js

// ★デバッグ表示用関数
function addDebugStep(step, message, color="black") {
    const list = document.getElementById('debug-list');
    if (!list) return; // 要素がない場合は無視
    const li = document.createElement('li');
    li.innerHTML = `<strong>[Step ${step}]</strong> ${message}`;
    li.style.color = color;
    list.appendChild(li);
    console.log(`[Step ${step}] ${message}`);
}

// ---------------------------------------------------------
// ★ここが汎用化のポイント
// ---------------------------------------------------------
const mainElement = document.querySelector('[data-room-name]');
const roomName = mainElement.getAttribute('data-room-name');
// HTMLに data-game-type があればそれを使い、なければ 'tictactoe' をデフォルトにする
const gameType = mainElement.getAttribute('data-game-type') || 'tictactoe';

addDebugStep("Init", `${gameType} 用の game_socket.js 読み込み完了`);

// 1. WebSocket接続の確立
// URLの一部を gameType 変数に置き換え、どのゲームのURLにも接続できるようにする
addDebugStep("Pre-9", `ws://${window.location.host}/ws/${gameType}/${roomName}/ へ接続を試みます...`);

const gameSocket = new WebSocket(
    `ws://${window.location.host}/ws/${gameType}/${roomName}/`
);

// ---------------------------------------------------------
// 以下は以前と同じイベントハンドラ
// ---------------------------------------------------------

// ★Step 13: 接続確立（onopen）
gameSocket.onopen = function(e) {
    addDebugStep(13, "クライアント: ソケット接続が確立しました (onopen)", "green");
    const statusDiv = document.getElementById('game-status');
    if (statusDiv) {
        statusDiv.textContent = "サーバーと接続されました！";
    }
};

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    // ★Step 12の通知受信（サーバーから来たデバッグメッセージ）
    if (data.type === 'debug_connection_step') {
        addDebugStep(data.step, `サーバーからの応答: ${data.message}`, "blue");
        return;
    }

    // ★Step 14: データ受信と画面更新
    addDebugStep(14, `データ受信: type=${data.type}`, "green");

    if (typeof handleGameMessage === 'function') {
        handleGameMessage(data.type || 'game_state', data); 
    } else {
        console.error("handleGameMessage関数が定義されていません。各ゲームのjsファイルを確認してください。");
    }
};

gameSocket.onclose = function(e) {
    addDebugStep("Error", "ソケットが切断されました", "red");
    console.warn('Game socket closed unexpectedly');
};

gameSocket.onerror = function(e) {
    addDebugStep("Error", "接続エラーが発生しました。コンソールを確認してください", "red");
    console.error('Game socket error:', e);
};

// サーバーへの送信ヘルパー関数
function sendGameMessage(message) {
    if (gameSocket.readyState === WebSocket.OPEN) {
        gameSocket.send(JSON.stringify(message));
    } else {
        console.warn("WebSocketは開いていません。");
    }
}