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
from flask import Flask, Response, request, render_template, url_for, redirect

# import sqlalchemy - a ORM for making it easier to interact with DB
# DO I EVEN NEED A DB FOR THIS?
# from flask.ext.sqlalchemy import SQLAlchemy

# create a Flask app
app = Flask(__name__)
app.debug = True

# "models"
class GameRoom():
	def __init__(self,name=""):
		self.name = name
		self.players = []
	
	def add_player(self, player):
		self.players.append(player)

class Player():
	def __init__(self):
		self.name = ""


# variable to hold the rooms
live_rooms = [1,2,3,4]

# create my views
@app.route('/')
def rooms():
	"""
	Homepage - Lists all game rooms and users.
	"""
	return render_template('game_rooms.html', live_rooms = live_rooms)

@app.route('/login', methods=['GET', 'POST'])
def login():
	"""
	Login - Allows user to login through a form.
	"""
	if request.method == 'POST':
		session['username'] = request.form['username']
		return redirect(url_for('rooms'))


@app.route('/create_room', methods=['POST'])
def create_room():
	"""
	Handles POST from the "Add Room" form on the Homepage. Redirects you to new room. This is the "game" room for each set of players.
	"""
	name = request.form['name']
	if name:
		room = GameRoom() 
		live_rooms.append(room)
	return redirect(url_for('rooms'))

if __name__ == '__main__':
	app.run()

