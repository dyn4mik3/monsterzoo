$(function() {
    socket = io.connect('/game');

    socket.on('connect', function() {
        $('#game').append($('<p>').text(this.socket.sessionid));
    });

    socket.on('game_start', function (players) {
        $('#game').append($('<p>Game start</p>'));
    });

    socket.on('player_number', function (game_update) {
        $('#game').append(game_update);
    });

    socket.on('announcement', function (msg) {
        $('#lines').append($('<p>').append($('<em>').text(msg)));
        setTimeout(function() {
            $("#lines").scrollTop($("#lines")[0].scrollHeight);
        }, 10);
    });

    socket.on('message', message);

    function message (from, msg) {
        $('#lines').append($('<p>').append($('<b style="margin-right:2px;">').text(from), msg));
        setTimeout(function() {
            $("#lines").scrollTop($("#lines")[0].scrollHeight);
        }, 10);
    };

    socket.on('deal_card', function(player, card_name, card_cost, card_image, card_text) {
        var card_layout = '<div class="card"><div class="corner top_left"><span class="number">' + card_name + 
        '</span></div><div class="corner top_right"><span class="number">' + card_cost + 
        '</span></div><div class="card_image"><p><img src="' + card_image +
        '" height="80px"></p>' + card_text +
        '</div>' +
        '<div class="playbutton">' +
        '<button type="button" name="' + card_name + '" class="btn btn-primary btn-mini">Play This Card</button>' +
        '</div></div>';
        if (player == this.socket.sessionid) {
            $('#player1').append(card_layout);
        }
        else {
            $('#player2').append(card_layout);
        };
    });

    socket.on('empty', function(player) {
        if (player == 'wild') {
            $('#wild').empty();
        }
        else if (player == this.socket.sessionid) {
            $('#player1').empty();
        }
        else {
            $('#player2').empty();
        }
    });

    socket.on('render_card', function(player, card_name, card_cost, card_image, card_text, index_location) {
        var card_layout = '<div class="card"><div class="corner top_left"><span class="number">' + card_name + 
        '</span></div><div class="corner top_right"><span class="number">' + card_cost + 
        '</span></div><div class="card_image"><p><img src="' + card_image +
        '" height="80px"></p>' + card_text +
        '</div>' +
        '<div class="playbutton">' +
        '<button type="button" ' +
        'name="' + index_location + '" class="btn btn-primary btn-mini play-this">Play This Card</button>' +
        '</div></div>';
        if (player == 'wild') {
            $('#wild').append(card_layout);
        }
        else if (player == this.socket.sessionid) {
            $('#player1').append(card_layout);
        }
        else {
            $('#player2').append(card_layout);
        };
    });


});
