// いらなかったら消してもらって大丈夫です
// team6/static/js/game_socket.js
const roomName = document.querySelector('main').getAttribute('data-room-name');
const gameSocket = new WebSocket(
    `ws://${window.location.host}/ws/tictactoe/${roomName}/`
);

const boardDiv = document.getElementById('game-board');
const statusDiv = document.getElementById('status');

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.success) {
        // ボードを更新
        updateBoard(data.board);
        statusDiv.textContent = data.message;
        
        if (data.game_over) {
            boardDiv.classList.add('disabled');
        }
    } else {
        statusDiv.textContent = `エラー: ${data.message}`;
    }
};

// クリック時にサーバーに送信
document.querySelectorAll('.cell').forEach((cell, index) => {
    cell.addEventListener('click', () => {
        gameSocket.send(JSON.stringify({
            'position': index
        }));
    });
});

function updateBoard(board) {
    document.querySelectorAll('.cell').forEach((cell, index) => {
        cell.textContent = board[index] === ' ' ? '' : board[index];
    });
}
