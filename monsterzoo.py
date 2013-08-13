import random

class Card(object):
    def __init__(self, name="", description="", card_type="", cost=0, food=0, image=""):
        self.name = name
        self.description = description
        self.card_type = card_type
        self.cost = cost
        self.food = food
    
    def __str__(self):
        return self.name

    def discard(self, player):
        hand = player.hand
        discard = player.discard
        try:
            hand.remove_card(self)
            discard.add_to_bottom(self)
        except:
            print "Card is not in hand"

class Cookies(Card):
    def __init__(self):
        self.name = "Cookies"
        self.description = "3 Food"
        self.card_type = "Food"
        self.cost = 3
        self.food = 3
        self.image = "/static/images/Food.png"
    
    def play(self, player):
        self.discard(player)
        player.food += self.food
        print "Played Cookies"
        self.socket.render_game()

class FumbleeBoogly(Card):
    def __init__(self):
        self.name = "Fumblee Boogly"
        self.description = "Draw 4 Cards. Put 2 Cards Back."
        self.card_type = "Monster"
        self.cost = 4
        self.food = 0
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        self.discard(player)
        print "Played Dirty Socks"
        self.socket.render_game()

class DirtySocks(Card):
    def __init__(self):
        self.name = "Dirty Socks"
        self.description = "1 Food"
        self.card_type = "Food"
        self.cost = 0
        self.food = 1
        self.image = "/static/images/Food.png"
    
    def play(self, player):
        self.discard(player)
        player.food += self.food
        print "Played Dirty Socks"
        self.socket.render_game()

class OoglyBoogly(Card):
    def __init__(self):
        self.name = 'Oogly Boogly'
        self.description = 'Draw 3 Cards'
        self.card_type = "Monster"
        self.cost = 3
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        self.discard(player)
        player.deal(3) # draw 3 cards 
        print "Played Oogly Boogly"
        self.socket.render_game()

class ZookeeZoogly(Card):
    def __init__(self):
        self.name = 'Zookee Zoogly'
        self.description = 'Move a Monster to your Zoo'
        self.card_type = "Monster"
        self.cost = 3
        self.image = "/static/images/Zoogly.png"
        self.socket = '' # this will hold the socketio object
    
    def play(self, player):
        if self.socket.selected_card:
            index_of_card = int(self.socket.selected_card)
            card = player.hand.cards[index_of_card]
            player.hand.remove_card(card)
            player.zoo.add_to_bottom(card)
            self.discard(player)
            '''
            hand = player.hand
            discard = player.discard
            zoo = player.zoo
            index_of_card = self.socket.selected_card
            print int(index_of_card)
            card = hand.cards[int(index_of_card)]
            print card
            hand.remove_card(self)
            discard.add_to_bottom(self)
            hand.remove_card(card)
            zoo.add_to_bottom(card)
            '''
            self.socket.log('Played: Zookee Zoogly')
            self.socket.render_game()
            # reset the selected card for next time
            self.socket.selected_card = None
        else:
            self.get_index_from_client(player)

    def get_index_from_client(self, player):
        self.socket.log('Getting Selected Card from Client')
        # this sets self.socket.selected_card
        self.socket.emit('get_card_for_zoo', player.player_id) 

class Deck(object):
    def __init__(self):
        self.cards = []
    
    def shuffle_cards(self):
        random.shuffle(self.cards)

    def show_cards(self):
        for card in self.cards:
            print card
    
    def draw_card(self):
        return self.cards.pop(0)

    def is_empty(self):
        return (len(self.cards) == 0)

    def add_to_top(self, card):
        self.cards.insert(0, card)
    
    def add_to_bottom(self, card):
        self.cards.append(card)
    
    def remove_card(self, card):
        self.cards.remove(card)
    
    def deal(self, hand, num):
        for i in range(num):
            if self.is_empty():
                break # need to add back discard and shuffle
            card = self.draw_card()
            hand.add_to_top(card)

class Hand(Deck):
    def __init__(self, name=""):
        self.cards = []
        self.name = name
    
    def play(self, card, players):
        card.play(players)
    
class Player(object):
    def __init__(self, player_id=""):
        starter_deck = [OoglyBoogly(),ZookeeZoogly(), ZookeeZoogly(), ZookeeZoogly(), ZookeeZoogly(), DirtySocks(), DirtySocks(), DirtySocks(), DirtySocks(), DirtySocks(), DirtySocks()]
        self.deck = Deck()
        self.deck.cards = list(starter_deck)
        self.hand = Hand()
        self.discard = Deck()
        self.zoo = Hand()
        self.food = 0
        self.score = 0
        self.player_id = player_id
    
    def deal(self, num):
        cards = []
        for i in range(num):
            if self.deck.is_empty():
                print "Deck is EMPTY"
                print "============="
                print "Shuffling in Discard"
                for card in self.discard.cards:
                    self.discard.remove_card(card)
                    self.deck.add_to_bottom(card)
                self.deck.shuffle_cards()
                
            card = self.deck.draw_card()
            self.hand.add_to_bottom(card)
            cards.append(card)
        return cards
    
    def play(self, card):
        card.play(self)

class Wild(Player):
    def __init__(self, player_id='wild'):
        starter_deck = [
                OoglyBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                Cookies(),
                Cookies(),
                FumbleeBoogly(),
                FumbleeBoogly()
            ]
        self.deck = Deck()
        self.deck.cards = list(starter_deck)
        self.deck.shuffle_cards()
        self.hand = Hand()
        self.discard = Deck()
        self.player_id = player_id

class Game(object):
    def __init__(self, players):
        self.state = 'play'
        self.players = players
        self.num_of_players = len(players)
        self.wild = Wild()

        # create a dictionary of player items (hands, decks, discards, zoos, etc) for each player
        #for player in range(num_of_players):
        #    self.players.append(Player())

        # shuffle decks
        for player in self.players:
            player.deck.shuffle_cards()
            
        '''
        WILD_DECK = [
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly(),
            OoglyBoogly()
        ]
        self.wild_deck = Deck()
        self.wild_deck.cards = WILD_DECK
        self.wild_discard = Deck()
        self.wild_hand = Hand() # this is the open face pile in middle
        '''

    def start(self):
        print "Dealing cards to players"
        for player in self.players:
            print "Dealing %r" % player
            player.deal(5)
        
        print "Dealing cards to the Wild"
        self.wild.deal(5)
        self.status()
    
    def status(self):
        for player in self.players:
            print "Player Status"
            print "============="
            print "Deck: %r" % player.deck.cards
            print "Hand: %r" % player.hand.cards
            print "Discard: %r" % player.discard.cards
            print "Zoo: %r" % player.zoo.cards
            print "Food: %r" % player.food
            print "Score: %r\n" % player.score

        print "Wild Status"
        print "==========="
        print "Wild Deck: %r" % self.wild.deck.cards
        print "Wild Discard: %r" % self.wild.discard.cards
        print "Wild Hand: %r" % self.wild.hand.cards

    def turn(self, player):
        hand = player.hand
        print "Cards in Hand"
        print "============="
        x = 0
        # print out the cards in hand and index numbers
        for card in hand.cards:
            print "[%r] - %s" % (x, card)
            x += 1
        print "[C] - Catch Something from The Wild"
        print "[Q] - End Turn"
        # ask for selection
        index_of_card = raw_input("> ")
        if index_of_card == 'C': # buy something from the wild
            x = 0
            print "Wild Cards"
            print "=========="
            for card in self.wild.hand.cards:
                print "[%r] - %r" % (x, card)
                x += 1
            print "Your Food: %r" % player.food
            selection = raw_input("> ")
            try:
                selected_card = self.wild.hand.cards[int(selection)]
            except IndexError:
                print "Not a Valid Selection"
                return

            if selected_card.cost <= player.food:
                print "Buying card"
                player.food = player.food - selected_card.cost
                self.wild.hand.remove_card(selected_card)
                player.discard.add_to_bottom(selected_card)
            else:
                print "Not enough food"
        
        elif index_of_card == 'Q': # end turn
            return

        else: # play the card
            try:
                selected_card = hand.cards[int(index_of_card)]
                player.play(selected_card)
            except IndexError:
                print "Not a valid selection"
            except ValueError:
                print "Please choose something else"

        self.status()
        if not hand.cards:
            #check to see if hand is empty
            print "No More Cards. Ending Turn."
            return
        else:
            print "Continue Playing."
            self.turn(player)
    
    def setup_next_turn(self, player):
        count_of_cards = len(player.hand.cards)
        print "Setting up next turn for Player %r" % player
        print "Player has %r cards" % count_of_cards
        cards_to_draw = 5 - count_of_cards
        print "Dealing Player %r cards" % cards_to_draw
        player.deal(cards_to_draw)
        print "Player now has %r cards" % len(player.hand.cards)

    def calculate_scores(self):
        for player in self.players:
            score = 0
            for card in player.zoo.cards:
                if card.cost:
                    score += card.cost
            player.score = score
            if player.score >= 20:
                self.state = 'end'
                print 'Game Over'
            print "Player %r Score: %r" % (player, player.score)

    def play_game(self):
        high_score = 0
        while high_score < 20:
            for player in self.players:
                print "Player %r's turn" % player
                self.turn(player)
                self.calculate_scores()
                self.setup_next_turn(player)


def test_game():
    game = Game(2)
    game.start()
    game.play_game()
    return game
