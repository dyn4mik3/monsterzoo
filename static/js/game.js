$(function() {
    socket = io.connect('/game');
     
    var turn;

    $('#turn-player1').hide();

    socket.on('connect', function() {
        $('#game').append($('<p>').text(this.socket.sessionid));
    });

    socket.on('game_start', function (players) {
        $('#game').append($('<p>Game start</p>'));
    });
    
    socket.on('game_over', function(player) {
        if (player == this.socket.sessionid) {
            $('.play-this').hide();
            $('#turn-player1').hide();
            $('#win-message').modal('toggle');
        }
        else {
            $('.play-this').hide();
            $('#lose-message').modal('toggle');
        };
    });

    socket.on('player_number', function (game_update) {
        $('#game').append(game_update);
    });

    socket.on('turn', function(player) {
        if (player == this.socket.sessionid) {
            turn = false;
            $('#turn-player1').hide();
            $('.btn').hide();
        }
        else {
            turn = true;
            $('.btn').hide(); // hide all buttons
            $('#turn-player1').show(); // show the "end turn" button
            $('#player1 .play-this').show(); // show the "play this card" buttons
        };
    });

    function clear_buttons() {
        if (turn == true) {
            $('.btn').hide();
            $('#turn-player1').show();
            $('#player1 .play-this').show();
        }
        else if (turn == false) {
            $('.btn').hide();
        };
    };

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
        var button = '<button type="button" ' + 'id="wild' + index_location +'" ' +
        'name="' + index_location + '" class="btn btn-primary btn-mini buy-this">Buy This Card</button>';
        var card_layout = '<div class="card"><div class="corner top_left"><span class="number">' + card_name + 
        '</span></div><div class="corner top_right"><span class="number">' + card_cost + 
        '</span></div><div class="card_image"><p><img src="' + card_image +
        '" height="80px"></p>' + card_text +
        '</div><div class="playbutton">'; 
        var close_div = '</div></div>';
        var food = $('#player1-food').html();
        if (player == 'wild') {
            if (food >= card_cost && turn == true) {
                card_layout = card_layout + button + close_div;
            }
            else {
                card_layout = card_layout + close_div;
            };
            $('#wild').append(card_layout);
        };
    });

    socket.on('render_card', function(player, card_name, card_cost, card_image, card_text, index_location) {
        var card_back = '<div class="card cardback" style="background-color:#f79a2f;"><div class="corner top_left"><span class="number">' + 
        '</span></div><div class="corner top_right"><span class="number">' + 
        '</span></div><div class="card_image"><p><img src="/static/images/Logo.png" height="80px"></p>' +
        '</div>' +
        '</div>';

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
            $('#player2').append(card_back);
        };
        clear_buttons();
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
            $('#player1-zoo .playbutton .btn').hide();
        }
        else {
            $('#player2-zoo').append(card_layout);
            $('#player2-zoo .playbutton .btn').hide();
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

    socket.on('select_cards', function(player, card_index) {
        $('#player1-zoo .playbutton .btn').hide();
        $('#player1 .playbutton .btn').show();
        $('#player1 .play-this').html('Pick This Card');
        $('#player1 .playbutton .btn').toggleClass('play-this pick-this');
        $('#player1 .playbutton .btn').toggleClass('btn-primary btn-warning');
        //console.log(card_index);
        if (card_index != null) {
            for (var i=0; i < card_index.length; i++) {
            $('#player1 .playbutton [name="'+ card_index[i] +'"]').hide();
            };
        };
    });

    socket.on('select_card_from_zoo', function(player, card_index) {
        $('#player1 .playbutton .btn').hide();
        $('#player1-zoo .play-this').html('Pick This Card');
        $('#player1-zoo .playbutton .btn').show();
        $('#player1-zoo .playbutton .btn').toggleClass('play-this pick-this');
        $('#player1-zoo .playbutton .btn').toggleClass('btn-primary btn-warning');
    });

    socket.on('select_card_from_wild', function(player, card_index) {
        $('#wild .playbutton .buy-this').hide(); // hide any buy this buttons
        var index_location = 0;
        $('#wild .playbutton').each(function(index_location) {
            var button = '<button type="button" ' + 'id="wild' + index_location +'" ' +
            'name="' + index_location + '" class="btn btn-warning btn-mini select-this">Select This</button>';
            $(this).append(button);
            index_location = index_location + 1;
        });
    });


});
