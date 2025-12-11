// team6/static/js/game1.js

// DOM要素の参照
const boardDiv = document.getElementById('game-board');
const statusDiv = document.getElementById('game-status');
const cells = document.querySelectorAll('.cell');
const resetButton = document.getElementById('reset-button');

// 1. WebSocketからメッセージを受信したときの処理 (game_socket.jsから呼ばれる)
function handleGameMessage(type, data) {
    if (type === 'game_state' || type === 'initial_state') {
        // ゲーム状態の更新 (移動、リセット後の状態)
        updateGameDisplay(data);
    } else if (type === 'error') {
        // エラー表示
        statusDiv.textContent = `エラー: ${data.message}`;
    }
    // その他のメッセージタイプに応じた処理...
}

// 2. ボードの更新とUIの状態制御
function updateGameDisplay(gameState) {
    const { board, current_player, game_over, winner, message, winning_line } = gameState;

    // A. ボードの描画
    cells.forEach((cell, index) => {
        // 内容の更新
        cell.textContent = board[index] === ' ' ? '' : board[index];
        
        // 勝ちラインのハイライト (CSSクラスを追加)
        cell.classList.remove('winning-cell');
        if (game_over && winner !== 'draw' && winning_line && winning_line.includes(index)) {
            cell.classList.add('winning-cell');
        }
    });

    // B. ステータスの更新
    if (game_over) {
        if (winner === 'draw') {
            statusDiv.textContent = "🔥 引き分けです！";
        } else {
            statusDiv.textContent = `🏆 プレイヤー ${winner} が勝ちました！`;
        }
        boardDiv.classList.add('disabled'); // クリックを無効化
        resetButton.style.display = 'block'; // リセットボタンを表示
    } else {
        // 通常のターン表示
        statusDiv.textContent = `現在のプレイヤー: ${current_player} のターンです。`;
        boardDiv.classList.remove('disabled'); // クリックを有効化
        resetButton.style.display = 'none'; // リセットボタンを非表示
    }
    
    // C. サーバーからのメッセージ（例：無効な移動）を一時的に表示
    if (message && !game_over) {
        console.log(`サーバーメッセージ: ${message}`);
        // ユーザーに短い通知を表示する処理を追加しても良い
    }
}

// 3. マスのクリックイベント (移動の送信)
cells.forEach((cell) => {
    cell.addEventListener('click', () => {
        // data-position属性から位置を取得 (HTMLで0-8を設定済み)
        const position = cell.getAttribute('data-position');
        
        // ボードが終了している、またはすでにセルが埋まっている場合は無視
        if (boardDiv.classList.contains('disabled') || cell.textContent !== '') {
            return; 
        }

        // game_socket.jsで定義された関数を使ってサーバーに送信
        sendGameMessage({
            'type': 'move',
            'position': parseInt(position)
        });
    });
});

// 4. リセットボタンのイベント
resetButton.addEventListener('click', () => {
    // サーバーにリセット要求を送信
    sendGameMessage({
        'type': 'reset'
    });
});

// 5. 初期状態の適用 (ページロード時に接続が確立された後、サーバーから受信した状態を適用)
// サーバーから 'initial_state' が送られてくるので、ここでは特別な初期化は不要
// ただし、CSSで `winning-cell` スタイルを定義する必要があります。