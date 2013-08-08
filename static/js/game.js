$(function() {
    socket = io.connect('/game');

    $('#turn-player1').hide();

    socket.on('connect', function() {
        $('#game').append($('<p>').text(this.socket.sessionid));
    });

    socket.on('game_start', function (players) {
        $('#game').append($('<p>Game start</p>'));
    });

    socket.on('player_number', function (game_update) {
        $('#game').append(game_update);
    });

    socket.on('turn', function(player) {
        if (player == this.socket.sessionid) {
            $('#turn-player1').hide();
            $('.play-this').hide();
        }
        else {
            $('#turn-player1').show();
            $('.play-this').show();
        };
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

    socket.on('empty_zoo', function(player) {
        if (player == this.socket.sessionid) {
            $('#player1-zoo').empty();
        }
        else {
            $('#player2-zoo').empty();
        }
    });

    socket.on('render_wild', function(player, card_name, card_cost, card_image, card_text, index_location) {
        var button = '<div class="playbutton">' +
        '<button type="button" ' +
        'name="' + index_location + '" class="btn btn-primary btn-mini buy-this">Buy This Card</button>' +
        '</div>';
        var card_layout = '<div class="card"><div class="corner top_left"><span class="number">' + card_name + 
        '</span></div><div class="corner top_right"><span class="number">' + card_cost + 
        '</span></div><div class="card_image"><p><img src="' + card_image +
        '" height="80px"></p>' + card_text +
        '</div>'; 
        var close_div = '</div>';
        var food = $('#player1-food').html();
        if (player == 'wild') {
            if (food >= card_cost) {
                card_layout = card_layout + button + close_div;
            }
            else {
                card_layout = card_layout + close_div;
            };
            $('#wild').append(card_layout);
        };
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

    socket.on('render_zoo', function(player, card_name, card_cost, card_image, card_text, index_location) {
        var card_layout = '<div class="card"><div class="corner top_left"><span class="number">' + card_name + 
        '</span></div><div class="corner top_right"><span class="number">' + card_cost + 
        '</span></div><div class="card_image"><p><img src="' + card_image +
        '" height="80px"></p>' + card_text +
        '</div>' +
        '<div class="playbutton">' +
        '<button type="button" ' +
        'name="' + index_location + '" class="btn btn-primary btn-mini play-this">Play This Card</button>' +
        '</div></div>';
        if (player == this.socket.sessionid) {
            $('#player1-zoo').append(card_layout);
        }
        else {
            $('#player2-zoo').append(card_layout);
        };
    });

    socket.on('food', function(player, food) {
        if (player == this.socket.sessionid) {
            $('#player1-food').html(food);
        }
        else {
            $('#player2-food').html(food);
        };
    });

    socket.on('score', function(player, score) {
        if (player == this.socket.sessionid) {
            $('#player1-score').html(score);
        }
        else {
            $('#player2-score').html(score);
        };
    });

});
