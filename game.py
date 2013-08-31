# import gevent first, patch it so the standard library is using gevent
from gevent import monkey
monkey.patch_all()

# setup all the socketio stuff
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin

# allows for easy serving of 404 page
from werkzeug.exceptions import NotFound

# import flask stuff
from flask import Flask, Response, flash, request, session, render_template, url_for, redirect

from monsterzoo import *

from datetime import datetime

import logging
from logging.handlers import RotatingFileHandler

# create a Flask app
app = Flask(__name__)
app.debug = True
handler = RotatingFileHandler('console.log', maxBytes=1000000, backupCount=5)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
 
# "models"
class GameRoom():
    def __init__(self,name=""):
        self.name = name
        self.players = []
    
    def add_player(self, player):
        self.players.append(player)

# variable to hold the rooms and users
live_rooms = []
users = []

app.secret_key = '\x03R\xe8!\xfdZ\x87*\xe9\x07sVI\x88|tt"\xdcb\xab=\xf8;'

# create my views
@app.route('/')
def index():
    """
    Homepage - Lists all game rooms and users.
    """
    return render_template('game_rooms.html', live_rooms = live_rooms, users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login - Allows user to login through a form.
    """
    if request.method == 'POST':
        session['username'] = request.form['username']
        flash('You are now logged in as %s' % session['username'])
        users.append(session['username'])
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    flash('You are now logged out %s' % session['username'])
    #users.remove(session['username'])
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/create_room', methods=['POST'])
def create_room():
    """
    Handles POST from the "Add Room" form on the Homepage. Redirects you to new room. This is the "game" room for each set of players.
    """
    name = request.form['name']
    if name:
        room = GameRoom(name=name)
        live_rooms.append(room)
    return redirect(url_for('index'))

@app.route('/game_room')
def room():
    """
    The "room" to play a game.
    """
    return render_template('game_room.html')

class PlayerMixin(object):
    def broadcast_to_player(self, player_id, event, *args):
        pkt = dict(type="event", name=event, args=args, endpoint=self.ns_name)
        
        self.socket.server.sockets[player_id].send_packet(pkt)

    def broadcast_to_players(self, players, event, *args):
        pkt = dict(type="event", name=event, args=args, endpoint=self.ns_name)

        for player in players:
            self.socket.server.sockets[player.player_id].send_packet(pkt)

class GameNamespace(BaseNamespace, RoomsMixin, BroadcastMixin, PlayerMixin):
    nicknames = {} # stores a dictionary with sessionids as key, Player objects as values
    players = [] # stores a list of Player objects
    #game = None
    end_turn = False
    login_count = 0
    player_games = {}
    player_queue = []
    game_list = []

    def initialize(self):
        user_id = self.socket.sessid
        self.emit('userid', user_id)
        self.nicknames[user_id] = Player(user_id)
        self.logger = app.logger
        self.log("Socketio session started")
        self.log("Nicknames data: %r" % self.nicknames)
        self.room = 'default'
        self.join = 'default'
        self.selected_card = None
        self.selected_cards = []
        self.selected_cards_wild = []
        self.play_stack = []
        self.players_in_game = [] # list ids of all players in game with you
        self.card = None
        self.game = None # equal to the instance's specific game object

    def recv_disconnect(self):
        user_id = self.socket.sessid
        self.log("User has disconnected")
        self.log("Nicknames data: %r" % self.nicknames)
        self.log("Checking to see if username exists. Then deleting.")
        # try removing from player_queue
        try:
            self.player_queue.remove(self.nicknames[user_id])
        except:
            print "Player not in queue"

        # try removing player from self.players
        try:
            self.log("self.session['username'] is set to %s" % self.session['username'])
            username = self.session['username']
            self.broadcast_event('announcement','%s has left' % username)
            self.log('Username %s has left' % username)
            self.log('Trying to remove player ID %s from the players list' % user_id)
            player = self.nicknames[user_id]
            player_index = self.players.index(player) + 1
            self.log('Player index is %r' % player_index)
            self.log('Players are %r' % self.players)
            self.players.remove(player)
            self.log('Removed player %s from game' % player_index)
            self.log('Players is now %r' % self.players)
        except:
            self.log("No username passed.")

        self.log("Try to delete ID: %s" % user_id)
        try:
            del self.nicknames[user_id]
            self.log("Successfully deleted %s from nicknames" % user_id)
        except KeyError:
            self.log("Could not find ID to delete. Likely already deleted.")
        
        self.disconnect(silent=True)
        return True

    def log(self, message):
        self.logger.info("{0}: [{1}] {2}".format(datetime.now(),self.socket.sessid, message))

    def on_play(self, location):
        self.log('Received location: %s' % location)
        location = int(location)
        player_id = self.socket.sessid
        player = self.nicknames[player_id]
        card = player.hand.cards[location]
        self.card = card
        card.socket = self
        card.play(player)
        self.log('Trying to play card %s at index location %s' % (card, location))
        self.log("Game is %r" % self.game)
        #self.render(player_id)
        #self.render_game()

    def on_selected_card(self, index):
        player_id = self.socket.sessid
        player = self.nicknames[player_id]
        self.selected_card = index
        card = player.hand.cards[int(index)] # get card object from the index number
        card.socket = self
        self.selected_cards.append(card) # add cards to the list of selected cards
        self.log('Selected Card is Now: %r %r' % (card, self.selected_card))
        self.log('Trying to play: %r' % self.card)
        self.card.play(player)

    def on_selected_card_from_wild(self, index):
        player_id = self.socket.sessid
        player = self.nicknames[player_id]
        card = self.game.wild.hand.cards[int(index)]
        card.socket = self
        self.selected_cards_wild.append(card)
        self.card.play(player)
    
    def on_selected_card_from_zoo(self, index):
        player_id = self.socket.sessid
        player = self.nicknames[player_id]
        self.selected_card = index
        card = player.zoo.cards[int(index)] # get card object from the index number
        card.socket = self
        self.selected_cards.append(card) # add cards to the list of selected cards
        self.log ('Selected Card from Zoo is Now: %r %r' % (card, self.selected_card))
        self.log ('Playing card from self.card %r' % self.card)
        self.card.play(player)

    def on_selected_card_from_other_zoo(self, index):
        player_id = self.socket.sessid
        player = self.nicknames[player_id]
        player_index = self.game.players.index(player)
        opponent = None
        if player_index == 0:
            opponent = self.players[1]
        elif player_index == 1:
            opponent = self.players[0]
        self.selected_card = index
        card = opponent.zoo.cards[int(index)] # get card object from the index number
        card.socket = self
        self.selected_cards.append(card) # add cards to the list of selected cards
        self.log ('Selected Card from Zoo is Now: %r %r' % (card, self.selected_card))
        self.log ('Playing card from self.card %r' % self.card)
        self.card.play(player)

    def on_buy(self, location):
        location = int(location)
        player_id = self.socket.sessid
        player = self.nicknames[player_id]
        wild = self.game.wild
        card = wild.hand.cards[location]
        self.log('Buying card %r' % card)
        modified_card_cost = max(0,(card.cost - player.food_discount))
        if modified_card_cost <= player.food:
            player.food = player.food - modified_card_cost
            wild.hand.remove_card(card)
            player.discard.add_to_bottom(card)
            try:
                wild.deal(1)
            except:
                self.log('No more cards in the wild.')
            self.render_game()
        else:
            print "Card cost greater than food + food_discount"

    def on_deal(self, player_id, num = 1):
        player = self.nicknames[player_id]
        cards = player.deal(num)
        self.log('Cards returned by Player deal function %r' % cards)
        self.render(player_id)
        #for card in cards:
        #    self.log('Player {%s} requested a card. {%r}' % (player_id, card))
        #    self.broadcast_event('announcement', 'Player {%s} has the following cards: %r' % (player_id, player.hand.cards))
        #    self.broadcast_event('deal_card', player_id, card.name, card.cost, card.image, card.description);
        return True

    def get_food_discount(self):
        for player in self.game.players:
            if player.turn == True:
                return player.food_discount

    def render_game(self):
        # NEED TO FIX THIS - RIGHT NOW RENDERING AFFECTS ALL PLAYERS. IT SHOULD ONLY AFFECT PLAYERS ASSOCIATED WITH GAME
        # calculate score
        self.game.calculate_scores()
        # render players
        for player in self.game.players:
            cards = player.hand.cards
            zoo = player.zoo.cards
            self.broadcast_to_players(self.game.players,'empty', player.player_id)
            location = 0
            for card in cards: # render cards in hand
                #self.log('Rendering card with info %r, %r, %r, %r, %r, %r' % (player.player_id, card.name, card.cost, card.image, card.description, location))
                self.broadcast_to_players(self.game.players,'render_card', player.player_id, card.name, card.cost, card.image, card.description, location)
                location += 1
            self.broadcast_to_players(self.game.players, 'empty_zoo', player.player_id)
            location = 0
            for card in zoo: # render cards in zoo
                self.broadcast_to_players(self.game.players,'render_zoo', player.player_id, card.name, card.cost, card.image, card.description, location)
                location += 1
            self.broadcast_to_players(self.game.players, 'food', player.player_id, player.food)
            self.broadcast_to_players(self.game.players,'score', player.player_id, player.score)
            self.broadcast_to_players(self.game.players, 'food_discount', player.player_id, player.food_discount)
        # render wild
        food_discount = self.get_food_discount()
        cards = self.game.wild.hand.cards
        location = 0
        self.broadcast_to_players(self.game.players, 'empty', 'wild')
        #self.broadcast_event('empty', 'wild')
        for card in cards:
            self.broadcast_to_players(self.game.players,'render_wild', 'wild', card.name, max(0,card.cost - food_discount), card.image, card.description, location)
            #self.broadcast_event('render_wild', 'wild', card.name, max(0,card.cost - food_discount), card.image, card.description, location)
            location += 1
        if self.game.state == 'end':
            score_dictionary = {}
            for player in self.game.players:
                score_dictionary[player.player_id] = player.score
            # get player_id for the winning score
            winner = max(score_dictionary, key=score_dictionary.get)
            self.broadcast_to_players(self.game.players,'game_over', winner)
            self.log('Game over. Winner is %r' % winner)

    def render(self, player_id):
        player = self.nicknames[player_id]
        location = 0
        cards = player.hand.cards
        self.broadcast_event('empty', player_id)
        for card in cards:
            self.log('Player {%s} requested a card. {%r}' % (player_id, card))
            #self.broadcast_event('announcement', 'Player {%s} has the following cards: %r' % (player_id, player.hand.cards))
            self.broadcast_event('render_card', player_id, card.name, card.cost, card.image, card.description, location)
            location += 1

    def render_discard(self, player_id):
        player = self.nicknames[player_id]
        cards = player.hand.cards
        self.emit('empty', player_id)
        location = 0
        for card in cards:
            self.emit('render_discard', player_id, card.name, card.cost, card.image, card.description, location)
            location += 1

    def render_wild(self, wild):
        location = 0
        cards = wild.hand.cards
        self.broadcast_event('empty', 'wild')
        for card in cards:
            self.log('Wild requested a card. {%r}' % card)
            #self.broadcast_event('announcement', 'Wild has the following cards: %r' % wild.hand.cards)
            self.broadcast_event('render_wild', 'wild', card.name, card.cost, card.image, card.description, location)
            location += 1

    def on_join_game(self, player_id):
        self.game = self.player_games[int(player_id)]
        print "Player: %r joined game %r" % (player_id, self.game)
        player_registered = 0
        # check to see if all players have joined the game
        for player in self.game.players:
            if self.game:
                player_registered += 1
        if player_registered == len(self.game.players):
            self.render_game()
 
    def start_game(self, players):
        self.broadcast_event('announcement', '2 Players have connected')
        new_game = Game(players)
        self.game_list.append(new_game)
        #GameNamespace.game = new_game
        new_game.wild.deal(5)
        for player in players:
            player.deal(5)
        self.broadcast_to_players(players, 'turn', players[1].player_id)
        players[0].turn = True
        self.log("Start game function complete")
        return new_game

    def register_game(self, player, game):
        self.broadcast_event('register_game', int(player.player_id), self.game_list.index(game))

    def on_login(self, username):
        self.log('Username: {0}'.format(username))
        self.session['username'] = username
        self.log('self.session["username"] is set to %s' % self.session['username'])
        user_id = self.socket.sessid
        self.players.append(self.nicknames[user_id])

        # Send client the Player number
        self.emit('player_number', 'You are player %d' % (self.players.index(self.nicknames[user_id]) + 1))

        # Send everyone status in chat box
        self.broadcast_event('announcement', '%s has connected' % username)
        self.broadcast_event('announcement', '%s is player %d' % (username, self.players.index(self.nicknames[user_id])+1))

        # Player queue. Once 2 are logged in, both are moved to a game.
        GameNamespace.player_queue.append(self.nicknames[user_id])
        if len(self.player_queue) == 2:
            new_game = self.start_game(self.player_queue)
            for player in self.player_queue:
                self.player_games.update({int(player.player_id):new_game})
                print "Updated Player Games: %r" % self.player_games
                # send a message to all players and registers the game object 
                self.register_game(player, new_game)
            GameNamespace.player_queue = []
            #self.render_game()
        print "Player Queue: %r" % self.player_queue
        print "Player Games: %r" % self.player_games

        # Once 2 players login, start game 
        '''
        if len(self.players) == 2:
            self.broadcast_event('announcement', '2 Players have connected')
            self.broadcast_event('game_start', len(self.players))
            GameNamespace.game = Game(self.players)
            self.game.wild.deal(5)
            self.render_wild(self.game.wild)
            for player in self.players:
                self.broadcast_event('announcement', 'Trying to deal to %s' % player.player_id)
                for _ in range(5):
                    self.on_deal(player.player_id)
            self.log('Playing Game')
            self.broadcast_event('turn', self.players[1].player_id)
            self.players[0].turn = True
            self.log("Game is %r" % self.game)
        '''

    def on_turn(self):
        user_id = self.socket.sessid
        player = self.nicknames[user_id]
        self.game.setup_next_turn(player)
        self.play_stack = [] # rest play stack
        self.render_game()
        self.broadcast_to_players(self.game.players, 'turn', self.socket.sessid)
        #self.broadcast_event('turn', self.socket.sessid)

    def on_discard(self, card_index):
        # used when player is discarding right before end of turn
        card_index = int(card_index)
        user_id = self.socket.sessid
        player = self.nicknames[user_id]
        card = player.hand.cards.pop(card_index)
        player.discard.add_to_bottom(card)
        self.render_discard(player.player_id)

    def on_user_message(self, msg):
        self.log('User message: {0}'.format(msg))
        username = self.session['username']
        self.broadcast_event('message', username, msg)
        return True

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        socketio_manage(request.environ, {'/game': GameNamespace}, request)
    except:
        app.logger.error("Exception while handling socketio connect", exc_info=True)

    return Response()

# start the app
if __name__ == '__main__':
   app.run()
