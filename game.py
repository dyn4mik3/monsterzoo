# import gevent first, patch it so the standard library is using gevent
from gevent import monkey
monkey.patch_all()

# for generating random user_ids
from random import randint

# setup all the socketio stuff
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin

# allows for easy serving of 404 page
from werkzeug.exceptions import NotFound

# import flask stuff
from flask import Flask, Response, flash, request, session, render_template, url_for, redirect

# import game logic from monsterzoo.py
from monsterzoo import *

# import logging functions to setup log file
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# create a Flask app (the main web application)
app = Flask(__name__)
app.debug = True

# setup logging, with default level of INFO and higher
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

class User():
    def __init__(self):
        self.username = None
        self.user_id = None
        self.status = None

    def waiting_for_game(self):
        self.status = 'waiting'

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
    try: 
        if session['username']:
            return render_template('users.html')
    except:
        return render_template('users.html')

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login - Allows user to login through a form.
    """
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['user_id'] = randint(1,198237251661)
        flash('You are now logged in as %s' % session['username'])
        users.append(session['username'])
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    flash('You are now logged out %s' % session['username'])
    session.pop('username', None)
    session.pop('user_id', None)
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
    The "room" to play a game. Contains play experience.
    """
    return render_template('game_room.html')

# Routes for static content / static templates

@app.route('/cards')
def cards():
    return render_template('cards.html')

@app.route('/story')
def story():
    return render_template('story.html')

@app.route('/media')
def media():
    return render_template('media.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/printandplay')
def printandplay():
    return render_template('print_and_play.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/credits')
def credits():
    return render_template('credits.html')

class PlayerMixin(object):
    def broadcast_to_player(self, player_id, event, *args):
        """
        This is sent to just the player identified by player_id.
        """
        pkt = dict(type="event", name=event, args=args, endpoint=self.ns_name)
        
        self.socket.server.sockets[player_id].send_packet(pkt)

    def broadcast_to_players(self, players, event, *args):
        """
        This is sent to all players identified by the players variable.
        """
        pkt = dict(type="event", name=event, args=args, endpoint=self.ns_name)

        for player in players:
            self.socket.server.sockets[player.player_id].send_packet(pkt)

class GameNamespace(BaseNamespace, RoomsMixin, BroadcastMixin, PlayerMixin):
    # Pseudocode for user management
    # User created for everyone logging in (cookie)
    # Clicking on start game creates a Player object. Multiple player
    # objects assigned to one user.
    # Queue stores player objects.
    # After 2 players enter queue, both player objects are moved to a room.
    # New game is associated to room.
    # Users return to a game in progress by accessing room URL.
    # Game, players, room is deleted after win/loss.
    # User can join multiple games. Unique room ID is combination 
    # of 2 user ids.
    nicknames = {} # stores a dictionary with sessionids as key, Player objects as values
    usernames = {} # stores a dictionary with sessionids as key, player usernames as values    
    players = [] # stores a list of Player objects
    #game = None
    #end_turn = False
    #login_count = 0
    player_games = {} # stores a dictionary with player ids as key, game objects as values
    player_queue = [] # used to place 2 players together in a game
    game_list = [] # list of game objects
    waiting_list = [] # list of users waiting for a game

    def initialize(self):
        user_id = self.socket.sessid
        self.emit('userid', user_id)
        print "Self.request %r" % self.request.flask_session
        self.request.flask_session['socket_id'] = self.socket.sessid
        print "socket id: %r" % self.request.flask_session['socket_id']

        self.nicknames[user_id] = Player(user_id) # create a new Player object with sessionid as player_id
        #self.usernames[user_id] = username
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
        self.card = None # current card being played
        self.game = None # equal to the instance's specific game object
        self.broadcast_event('users-online', list(self.nicknames))
        print "Nicknames"
        print list(self.nicknames)

        # Store cookie username in GameNamespace
        try:
            GameNamespace.usernames[user_id] = self.request.flask_session['username']
        except:
            print "No username in flask session"
        self.broadcast_event('users-logged-in', list(self.usernames.values()))

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
            #username = self.usernames[user_id]
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

        try:
            print "Trying to delete username from GameNamespace %r" % GameNamespace.usernames[user_id]
            del GameNamespace.usernames[user_id]
        except:
            print "No match in GameNamespace.usernames[user_id]"

        self.log("Try to delete ID: %s" % user_id)
        try:
            del self.nicknames[user_id]
            self.log("Successfully deleted %s from nicknames" % user_id)
        except KeyError:
            self.log("Could not find ID to delete. Likely already deleted.")
        
        self.broadcast_event('users-online', list(self.nicknames))
        self.disconnect(silent=True)
        return True

    def log(self, message):
        # 20130906:LyV: Could not figure out why self does not have the logger object.
        #   So, for now use the application logging facility to log.
        #
        #self.logger.info("{0}: [{1}] {2}".format(datetime.now(),self.socket.sessid, message))
        app.logger.info("{0}: [{1}] {2}".format(datetime.now(),self.socket.sessid, message))

    def set_player_id(self, user_id):
        player = get_player(user_id)
        player.player_id = self.socket.sessid 
        return player.player_id

    def get_player(self, user_id):
        player = dict_of_players_and_user_ids[user_id]
        return player
    
    def on_ready(self):
        user_id = self.request.flask_session['user_id']
        self.request.flask_session['ready'] = True
        GameNamespace.waiting_list.append(user_id)
        self.broadcast_event('waiting', GameNamespace.waiting_list)

    def on_play(self, location):
        self.log('Received location: %s' % location)
        location = int(location)
        player_id = self.socket.sessid
        player = self.nicknames[player_id]
        card = player.hand.cards[location]
        self.card = card
        card.socket = self
        card.play(player)
        # This is useful for debugging. Not essential for logging.
        #
        #self.log('Trying to play card %s at index location %s' % (card, location))
        #self.log("Game is %r" % self.game)
        username = self.session['username']
        #username = self.usernames[user_id]
        self.broadcast_to_players(self.game.players, 'play-update', username, "Played %s. (%s)" % (card.name, card.description))
        self.log("%s: Played %s. (%s)" % (username, card.name, card.description))
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

    def get_opponent(self, player):
        player_index = self.game.players.index(player)
        if player_index == 0:
            opponent = self.players[1]
        elif player_index == 1:
            opponent = self.players[0]
        return opponent

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
        self.broadcast_to_players(self.game.players, 'play-update', self.session['username'], "Bought %s. (%s)" % (card.name, card.description))
        self.log("%s: Bought %s. (%s)" % (self.session['username'], card.name, card.description))
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

    def on_remodel(self, location):
        location = int(location)
        player_id = self.socket.sessid
        player = self.nicknames[player_id]
        card = player.zoo.cards[location]
        card.remodel = False
        opponent = self.get_opponent(player)
        opponent.discard.add_to_bottom(card.remodel_card)
        card.remodel_card = None
        player.food = player.food - card.cost
        self.render_game()

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
                self.broadcast_to_players(self.game.players,'render_card', player.player_id, card.name, card.cost, card.image, card.description, card.card_family, location)
                location += 1
            self.broadcast_to_players(self.game.players, 'empty_zoo', player.player_id)
            location = 0
            self.broadcast_to_players(self.game.players, 'food', player.player_id, player.food)
            for card in zoo: # render cards in zoo
                self.broadcast_to_players(self.game.players,'render_zoo', player.player_id, card.name, card.cost, card.image, card.description, card.remodel, location)
                location += 1
            self.broadcast_to_players(self.game.players,'score', player.player_id, player.score)
            self.broadcast_to_players(self.game.players, 'food_discount', player.player_id, player.food_discount)
            self.broadcast_to_players(self.game.players, 'deck_count', player.player_id, len(player.deck.cards))
            self.broadcast_to_players(self.game.players, 'discard_count', player.player_id, len(player.discard.cards))
            self.broadcast_to_players(self.game.players, 'cards_played', player.player_id, len(player.played.cards))
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
        event_card = new_game.wild.event_card
        print "Event Card: %r" % event_card
        self.broadcast_to_players(players, 'event', event_card.name, event_card.image, event_card.description)
        self.broadcast_to_players(players, 'turn', players[1].player_id)
        players[0].turn = True
        self.log("Start game function complete")
        return new_game

    def register_game(self, player, game):
        self.broadcast_event('register_game', int(player.player_id), self.game_list.index(game))

    def on_already_logged_in(self):
        cookie = self.request.flask_session
        username = cookie['username']
        user_id = cookie['user_id']
        socket_id = cookie['socket_id']
        self.players.append(self.player_objects_by_user_id[user_id])

    def on_login(self, username):
        self.log('Username: {0}'.format(username))
        
        # 20130906:LyV: Added this line to initialize the object.
        # self.initialize(self,username)
        
        # 20130906:LyV: For now, comment out the session attribute, since
        # this object has not associated with a session yet.
        #
        self.session['username'] = username
        self.log('self.session["username"] is set to %s' % self.session['username'])
        user_id = self.socket.sessid
        self.players.append(self.nicknames[user_id])

        # Store cookie username in GameNamespace
        try:
            GameNamespace.usernames[user_id] = self.request.flask_session['username']
        except:
            print "No username in flask session"

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

    def on_turn(self):
        user_id = self.socket.sessid
        player = self.nicknames[user_id]
        self.game.setup_next_turn(player)
        self.play_stack = [] # rest play stack
        self.render_game()
        self.broadcast_to_players(self.game.players, 'turn', self.socket.sessid)
        self.broadcast_to_players(self.game.players, 'play-update', 'Game Event', 'End of Turn')
        self.log('End Turn')
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
        user_id = self.socket.sessid
        username = self.session['username']
        #username = self.usernames[user_id]
        self.broadcast_event('message', username, msg)
        return True

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    try:
        real_request = request._get_current_object()
        real_request.flask_session = session._get_current_object()
        socketio_manage(request.environ, {'/game': GameNamespace}, request=real_request)
    except:
        app.logger.error("Exception while handling socketio connect", exc_info=True)

    return Response()

# start the app
if __name__ == '__main__':
   app.run()
