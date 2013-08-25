import unittest

import os
import sys

# Add game directory to path so we can import game files from the test folder
pwd = os.path.dirname(__file__)
root = os.path.abspath(os.path.join(pwd, '..'))
sys.path.append(root)

import game
import monsterzoo


class TestGame(unittest.TestCase):

    # setUp is run before each test
    # Initialize stuff onto self in here to re-use for each test
    def setUp(self):

        # This is flask's test app, which lets you run tests by hitting the appropriate urls
        # and examining the responses
        self.app = game.app.test_client()

    # Each test should be named test_*

    # Test some urls
    def test_index(self):
        response = self.app.get('/')

        # Make sure the index page is displayed, by looking for "Start a Game" in the returned html
        self.assertIn('Start a Game', response.data)

    def test_start_game(self):
        # 0 rooms to start
        self.assertEqual(len(game.live_rooms), 0)

        response = self.app.post('/create_room', data={'name': 'test room'})

        # 1 room after
        self.assertEqual(len(game.live_rooms), 1)

        # With the name we gave it
        new_game = game.live_rooms[0]
        self.assertEqual(new_game.name, 'test room')


    # Test some cards
    # (You can eventually refactor these into their own test_cards.py:TestCards class etc)

    def test_player(self):
        """ Test creation of a player instance """
        player = monsterzoo.Player(player_id=1)

        self.assertEqual(player.player_id, 1)
        self.assertEqual(player.score, 0)

    def test_player_deal(self):
        """ Test that dealing a card removes one from the deck and adds one to the hand """
        player = monsterzoo.Player(player_id=1)

        deck_length = len(player.deck.cards)
        hand_length = len(player.hand.cards)
        player.deal(1)
        self.assertEqual(len(player.deck.cards), deck_length - 1)
        self.assertEqual(len(player.hand.cards), hand_length + 1)

    def test_dirty_socks(self):
        player = monsterzoo.Player(player_id=1)
        food = player.food

        card = monsterzoo.DirtySocks()
        player.hand.add_to_bottom(card)
        player.play(card)

        self.assertEqual(player.food, food + 1)


if __name__ == '__main__':
    unittest.main()
