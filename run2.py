from game2 import app
from gevent import monkey
from socketio.server import SocketIOServer
monkey.patch_all()

PORT = 5000 

if __name__ == '__main__':
    print 'Listening on http://127.0.0.1:%s - Socket Server Enabled' % PORT
    SocketIOServer(('', PORT), app, resource="socket.io").serve_forever()
