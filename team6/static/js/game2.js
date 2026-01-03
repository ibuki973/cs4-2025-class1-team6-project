//game2.js: ゲーム2用のJavaScript

console.log("game2.js loaded")

//関数

function startGame2() {
    //Todo:
}

function selectCard(cardType) {
    // サーバーに「このカードを出した」という情報を送る
    gameSocket.send(JSON.stringify({
        'type': 'play_card',
        'card': cardType
    }));
}

gameSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.type === 'round_result') {
        // 結果を表示（皇帝が市民に勝った！など）
        alert("結果: " + data.result);
    }
};