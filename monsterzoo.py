import random

class Card(object):
    def __init__(self, name="", description="", card_type="", card_family="",cost=0, food=0, image=""):
        self.name = name
        self.description = description
        self.card_type = card_type
        self.card_family = card_family
        self.cost = cost
        self.food = food
    
    def __str__(self):
        return self.name

    def zoo_effect(self, player):
        pass

    def move_selected_card_to_zoo(self, player):
        card = self.get_selected_card()
        # Special rule for Ripli Oogly
        if card.name == "Ripli Oogly":
            player.food += len(player.zoo.cards)
        player.hand.remove_card(card)
        player.zoo.add_to_bottom(card)

    def discard(self, player):
        hand = player.hand
        discard = player.discard
        try:
            print "Trying to remove card %r from hand" % self
            hand.remove_card(self)
            discard.add_to_bottom(self)
        except:
            print "Card is not in hand"

    def put_back(self, player):
        hand = player.hand
        deck = player.deck
        try:
            hand.remove_card(self)
            deck.add_to_top(self)
        except:
            print "Card is not in hand"

    def select_cards(self, num, player, played_card_index):
        self.socket.log('Getting Selected Card from Client')
        self.socket.log('Data passed to select_cards %r %r %r' % (num, player, played_card_index))
        card_index = [played_card_index]
        self.socket.emit('select_cards', player.player_id, card_index) 
        self.socket.log('Sent emit selected_cards')

    def select_only_monsters(self, num, player, played_card_index):
        self.socket.log('Getting Selected Card from Client')
        self.socket.log('Data passed to select_cards %r %r %r' % (num, player, played_card_index))
        card_index = [played_card_index]
        # ADD FOOD TO CARD INDEX
        for card in player.hand.cards:
            if card.card_type == "Food":
                card_index.append(player.hand.cards.index(card))
        print "Card index for selected_cards %r" % card_index
        self.socket.emit('select_cards', player.player_id, card_index) 
        self.socket.log('Sent emit selected_cards')

    def select_cards_wild(self, num, player):
        self.socket.emit('select_card_from_wild', player.player_id)

    def get_other_player(self, player):
        # this is buggy
        player_index = self.socket.game.players.index(player)
        if player_index == 0:
            return self.socket.players[1]
        elif player_index == 1:
            return self.socket.players[0]
        else:
            print "Something went wrong when getting the other player index"

    def find_location(self, player):
        hand = player.hand
        deck = player.deck
        zoo = player.zoo
        if self in hand:
            location = hand.index(self)
            print "Card found in Hand"
            return 'hand', location
        elif self in deck:
            location = deck.index(self)
            print "Card found in Deck"
            return 'deck', location
        elif self in zoo:
            location = zoo.index(self)
            print "Card found in Zoo"
            return 'zoo', location
        else:
            print "Card not found"
            return False

    def select_card_from_zoo(self, player, played_card_index):
        self.socket.emit('select_card_from_zoo', player.player_id, played_card_index)

    def select_card_from_wild(self, player):
        self.socket.emit('select_card_from_wild', player.player_id)

    def get_selected_card(self):
        selected_cards = self.socket.selected_cards
        card = selected_cards.pop(0)
        return card

    def get_selected_card_wild(self):
        selected_cards = self.socket.selected_cards_wild
        card = selected_cards.pop(0)
        return card

    def peak_at_play_stack(self):
        try:
            card = self.socket.play_stack[-1]
            print "Card at the top of the stack is %r" % card
            return card
        except:
            print "Peaking at Play Stack: Play Stack is Empty"
            return False

    def is_in_stack(self):
        try:
            card = self.socket.play_stack.index(self)
            print "Card %r is in stack at location" % card
            return True
        except:
            print "Card is not in the play stack"
            return False

class DirtySocks(Card):
    def __init__(self):
        self.name = "Dirty Socks"
        self.description = "1 Food"
        self.card_type = "Food"
        self.card_family = "Food"
        self.cost = 0
        self.food = 1
        self.image = "/static/images/Food.png"

    def play(self, player):
        self.discard(player)
        player.food += self.food
        print "Played Dirty Socks"
        self.socket.render_game()

class Cookies(Card):
    def __init__(self):
        self.name = "Cookies"
        self.description = "3 Food"
        self.card_type = "Food"
        self.card_family = "Food"
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
        self.card_family = "Boogly"
        self.cost = 4
        self.food = 0
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        if len(self.socket.selected_cards) == 2:
            card = self.socket.selected_cards[1]
            card.put_back(player) # put the second card back on deck
            self.discard(player) # discard the fumblee boogly card
            self.socket.log('Played: Fumblee Boogly')
            self.socket.render_game()
            self.socket.selected_cards = [] # reset the selected cards
        elif len(self.socket.selected_cards) == 1:
            self.socket.log('Discard first card')
            card = self.socket.selected_cards[0]
            card.put_back(player) # put the first card back on deck
            self.socket.render_game()
            self.socket.log('Grab another card')
            try:
                fumblee = player.hand.cards.index(self)
            except:
                fumblee = None
                print "Fumblee is not in Hand"
            self.select_cards(1, player, fumblee)
        else:
            player.deal(4)
            self.socket.render_game()
            self.socket.log('Going to select_cards function')
            fumblee = player.hand.cards.index(self)
            self.select_cards(1, player, fumblee)

class BooBoogly(Card):
    def __init__(self):
        self.name = 'Boo Boogly'
        self.description = 'Draw 3 Cards'
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 3
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        self.discard(player)
        player.deal(3) # draw 3 cards 
        print "Played Boo Boogly"
        self.socket.render_game()

class MeeraBoogly(Card):
    def __init__(self):
        self.name = 'Meera Boogly'
        self.description = 'Play a card from your Zoo'
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 3
        self.image = "/static/images/Boogly.png"

    def play(self, player):
        if self.socket.selected_cards and self.peak_at_play_stack() == self:
            # Meera is the top card in the stack and a selected card exists
            card = self.get_selected_card()
            self.socket.selected_cards = [] # reset the selected cards
            print "Meera Loop: Playing %r" % card
            card.play(player)
            self.play(player)
        elif self.socket.selected_cards and self.peak_at_play_stack() != self:
            # Meera is not the top card, but there is already a selected card.
            # Pass it back to the top card in the stack.
            card = self.peak_at_play_stack()
            print "Meera Loop: Selected Card Exists & Meera is not top of stack"
            print "Try playing the top card on stack"
            card.play(player)
            self.play(player)
        elif self.peak_at_play_stack() == self:
            print "Meera Loop: Meera is the top card in stack"
            self.discard(player)
            print "Played Meera Boogly"
            self.socket.render_game()
            self.socket.play_stack.remove(self)
        elif self.is_in_stack():
            print "Meera is in the stack, but not at the top"
            pass
        else:
            meera = player.hand.cards.index(self)
            self.select_card_from_zoo(player, meera)
            self.socket.play_stack.append(self)
            print "Meera: Play stack is %r" % self.socket.play_stack

class WhompoBoogly(Card):
    def __init__(self):
        self.name = 'Whompo Boogly'
        self.description = '+2 Food. Zoo Effect: Draw a card.'
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 4
        self.food = 2
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        self.discard(player)
        player.food += 2 
        print "Played Whompo Boogly"
        self.socket.render_game()

    def zoo_effect(self, player):
        player.deal(1)
        print "Zoo Effect Whompo Boogly"
        self.socket.render_game()

class BoomerBoogly(Card):
    def __init__(self):
        self.name = 'Boomer Boogly'
        self.description = 'Draw 2 Cards for Every Boogly in Your Zoo'
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 6
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        self.discard(player)
        count = 0
        for card in player.zoo.cards:
            if card.card_family == "Boogly":
                count += 1
        if count > 0:
            count = count * 2
            player.deal(count)
        else:
            print "No Boogly in Zoo"
        print "Played Whompo Boogly"
        self.socket.render_game()

class FloBoogly(Card):
    def __init__(self):
        self.name = 'Flo Boogly'
        self.description = 'Zoo Effect: Draw a card each time you put a Monster into your Zoo'
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 3
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        self.discard(player)
        print "Played Flo Boogly"
        self.socket.render_game()

class KoppiBoogly(Card):
    def __init__(self):
        self.name = 'Koppi Boogly'
        self.description = 'Draw 3 Cards if you have a Boogly in your Zoo.'
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 2
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        self.discard(player)
        count = 0
        for card in player.zoo.cards:
            if card.card_family == "Boogly":
                count += 1
        if count > 0:
            print "Found a Boogly in Zoo. Dealing 3 Cards."
            player.deal(3)
        else:
            print "No Boogly in Zoo"
        print "Played Koppi Boogly"
        self.socket.render_game()

class LanzoBoogly(Card):
    def __init__(self):
        self.name = 'Lanzo Boogly'
        self.description = "Take a random card from other player\'s hand. Put it in your hand."
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 5
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        opponent = self.get_other_player(player)
        opponent_hand = opponent.hand.cards
        card = random.choice(opponent_hand)
        card.discard(opponent)
        player.hand.add_to_bottom(card)
        print "Played Lanzo Boogly"
        self.discard(player)
        self.socket.render_game()

class LurtiBoogly(Card):
    def __init__(self):
        self.name = 'Lurti Boogly'
        self.description = "Put the top card from other player's deck into your hand."
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 4
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        opponent = self.get_other_player(player)
        print "This is the opponent returned by Lurti: %r" % opponent
        card = opponent.deck.draw_card()
        print "This is the card returned by Lurti: %r" % card
        if card:
            player.hand.add_to_bottom(card)
        else:
            print "No card to add. Lurti Boogly did nothing"
        print "Played Lurti Boogly"
        self.discard(player)
        self.socket.render_game()

class PortaBoogly(Card):
    def __init__(self):
        self.name = 'Porta Boogly'
        self.description = "Swap a Monster card from your hand with a card in The Wild."
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 3
        self.image = "/static/images/Boogly.png"
    
    def play(self, player):
        self.socket.log('In the Play Loop for Porta Boogly')
        # First select a card from hand
        # Then select a card in the wild
        # Then move the wild card into hand
        if self.socket.selected_cards and self.socket.selected_cards_wild:
            card = self.get_selected_card()
            wildcard = self.get_selected_card_wild()
            wild = self.socket.game.wild
            # swap card in wild and hand
            player.hand.remove_card(card)
            wild.hand.add_to_bottom(card)
            wild.hand.remove_card(wildcard)
            player.hand.add_to_bottom(wildcard)
            self.discard(player)
            self.socket.log('Played: Porta Boogly')
            self.socket.selected_cards = [] # reset the selected cards
            self.socket.selected_cards_wild = [] # reset the selected cards from wild
            self.socket.render_game()
            self.socket.play_stack.remove(self)
        elif self.socket.selected_cards and not self.socket.selected_cards_wild:
            self.socket.log('Going to select_cards_wild function')
            self.select_cards_wild(1, player)
        else:
            self.socket.log('Going to select_cards function')
            try:
                porta = player.hand.cards.index(self)
            except:
                porta = None
                print "Porta is not in hand."
            self.select_only_monsters(1, player, porta) # issue with meera boogly, if this is run then meera is played before card can be selected
            self.socket.play_stack.append(self)
            print "Porta: Play stack is %r" % self.socket.play_stack

class HuntoOogly(Card):
    def __init__(self):
        self.name = 'Hunto Oogly'
        self.description = "Move a card from The Wild to the top of your deck."
        self.card_type = "Monster"
        self.card_family = "Oogly"
        self.cost = 5
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        self.socket.log('In the Play Loop for Hunto Oogly')
        # select a card in the wild
        # move card to top of deck
        if self.socket.selected_cards_wild:
            wildcard = self.get_selected_card_wild()
            wild = self.socket.game.wild
            wild.hand.remove_card(wildcard)
            player.deck.add_to_top(wildcard)
            wild.deal(1)
            self.discard(player)
            self.socket.log('Played: Hunto Oogly')
            self.socket.selected_cards_wild = [] # reset the selected cards from wild
            self.socket.render_game()
            self.socket.play_stack.remove(self)
        else:
            self.socket.log('Going to select_cards function')
            try:
                hunto = player.hand.cards.index(self)
            except:
                hunto = None
                print "Hunto is not in hand."
            self.select_cards_wild(1, player) # issue with meera boogly, if this is run then meera is played before card can be selected
            self.socket.play_stack.append(self)
            print "Hunto: Play stack is %r" % self.socket.play_stack

class ChunkyOogly(Card):
    def __init__(self):
        self.name = 'Chunky Oogly'
        self.description = '+2 Food. Draw a Card.'
        self.card_type = "Monster"
        self.card_family = "Oogly"
        self.cost = 3
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        player.deal(1) # draw 3 cards 
        player.food += 2
        print "Played Chunky Oogly"
        self.discard(player)
        self.socket.render_game()

class YummliOogly(Card):
    def __init__(self):
        self.name = 'Yummli Oogly'
        self.description = 'Double all Food gained so far this turn.'
        self.card_type = "Monster"
        self.card_family = "Oogly"
        self.cost = 6
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        player.food = player.food * 2
        print "Played Yummli Oogly"
        self.discard(player)
        self.socket.render_game()


class RinkaOogly(Card):
    def __init__(self):
        self.name = 'Rinka Oogly'
        self.description = '+Food equal to the number of Monsters in your Zoo'
        self.card_type = "Monster"
        self.card_family = "Oogly"
        self.cost = 2
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        player.food += len(player.zoo.cards)
        print "Played Rinka Oogly"
        self.discard(player)
        self.socket.render_game()

class RipliOogly(Card):
    def __init__(self):
        self.name = 'Ripli Oogly'
        self.description = 'Gain Food equal to the number of cards in your Zoo when this card enters your Zoo.'
        self.card_type = "Monster"
        self.card_family = "Oogly"
        self.cost = 3
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        print "Played Ripli Oogly"
        self.discard(player)
        self.socket.render_game()

class ParksOogly(Card):
    def __init__(self):
        self.name = 'Parks Oogly'
        self.description = '+2 Food. Monsters cost 1 less food to catch this turn.'
        self.card_type = "Monster"
        self.card_family = "Oogly"
        self.cost = 5
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        player.food += 2
        player.food_discount += 1
        print "Played Parks Oogly"
        self.discard(player)
        self.socket.render_game()

class FifiOogly(Card):
    def __init__(self):
        self.name = 'Fifi Oogly'
        self.description = '+1 Food. Monsters cost 1 less food to catch this turn. Zoo Effect: Monsters cost 1 less to catch this turn.'
        self.card_type = "Monster"
        self.card_family = "Oogly"
        self.cost = 3
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        player.food += 1
        player.food_discount += 1
        print "Played Fifi Oogly"
        self.discard(player)
        self.socket.render_game()
    
    def zoo_effect(self, player):
        player.food_discount += 1

class OoglyBoogly(Card):
    def __init__(self):
        self.name = 'Oogly Boogly'
        self.description = 'Draw 3 Cards'
        self.card_type = "Monster"
        self.card_family = "Boogly"
        self.cost = 3
        self.image = "/static/images/Oogly.png"
    
    def play(self, player):
        player.deal(3) # draw 3 cards 
        print "Played Oogly Boogly"
        self.discard(player)
        self.socket.render_game()

class JusteeZoogly(Card):
    def __init__(self):
        self.name = 'Justee Zoogly'
        self.description = 'Remove a card in your hand from the game. Draw a card.'
        self.card_type = "Monster"
        self.card_family = "Zoogly"
        self.cost = 2
        self.image = "/static/images/Zoogly.png"

    def play(self, player):
        self.socket.log('In the Play Loop for Justee Zoogly')
        if self.socket.selected_cards:
            card = self.get_selected_card()
            player.hand.remove_card(card)
            player.deal(1)
            self.discard(player)
            self.socket.log('Played: Justee Zoogly')
            self.socket.selected_cards = [] # reset the selected cards
            self.socket.render_game()
            self.socket.play_stack.remove(self)
        else:
            self.socket.log('Going to select_cards function')
            try:
                justee = player.hand.cards.index(self)
            except:
                justee = None
                print "Justee is not in hand."
            self.select_cards(1, player, justee) # issue with meera boogly, if this is run then meera is played before card can be selected
            self.socket.play_stack.append(self)
            print "Justee: Play stack is %r" % self.socket.play_stack

class OhnoZoogly(Card):
    def __init__(self):
        self.name = 'Ohno Zoogly'
        self.description = 'Swap this card with a card in your Zoo.'
        self.card_type = "Monster"
        self.card_family = "Zoogly"
        self.cost = 6
        self.image = "/static/images/Zoogly.png"

    def play(self, player):
        if self.socket.selected_cards:
            card = self.get_selected_card()
            self.socket.selected_cards = [] # reset the selected cards
            player.hand.remove_card(self)
            player.zoo.remove_card(card)
            player.hand.add_to_bottom(card)
            player.zoo.add_to_bottom(self)
            self.socket.log('Played Ohno Zoogly')
            self.socket.render_game()
        else:
            ohno = player.hand.cards.index(self)
            self.select_card_from_zoo(player, ohno)

class ViktorZoogly(Card):
    def __init__(self):
        self.name = 'Viktor Zoogly'
        self.description = 'Gain food equal to the number of monsters in your opponents Zoo.'
        self.card_type = "Monster"
        self.card_family = "Zoogly"
        self.cost = 2
        self.image = "/static/images/Zoogly.png"
        self.socket = '' # this will hold the socketio object
    
    def play(self, player):
        opponent = self.get_other_player(player)
        player.food += len(opponent.zoo.cards)
        self.discard(player)
        self.socket.log('Played Viktor Zoogly')
        self.socket.render_game()

class BossiZoogly(Card):
    def __init__(self):
        self.name = 'Bossi Zoogly'
        self.description = '+2 Food. Force other player to discard a Monster from their Zoo.'
        self.card_type = "Monster"
        self.card_family = "Zoogly"
        self.cost = 4
        self.image = "/static/images/Zoogly.png"
        self.socket = '' # this will hold the socketio object
    
    def play(self, player):
        if self.socket.selected_cards:
            card = self.get_selected_card()
            self.socket.selected_cards = []
            opponent = self.get_other_player(player)
            opponent.zoo.remove_card(card)
            opponent.discard.add_to_bottom(card)
            self.discard(player)
            player.food += 2
            self.socket.log('Played Bossi Zoogly')
            self.socket.play_stack.remove(self)
            self.socket.render_game()
        else:
            self.socket.log('Getting card from other player zoo')
            self.socket.play_stack.append(self)
            self.socket.emit('select_card_from_other_zoo', player.player_id, 1)
        
 
class SluggoZoogly(Card):
    def __init__(self):
        self.name = 'Sluggo Zoogly'
        self.description = 'Move a random Monster in opponents Zoo back to opponents hand'
        self.card_type = "Monster"
        self.card_family = "Zoogly"
        self.cost = 2
        self.image = "/static/images/Zoogly.png"
        self.socket = '' # this will hold the socketio object
    
    def play(self, player):
        if self.socket.selected_cards:
            card = self.get_selected_card()
            self.socket.selected_cards = []
            opponent = self.get_other_player(player)
            opponent.zoo.remove_card(card)
            opponent.hand.add_to_bottom(card)
            self.discard(player)
            self.socket.log('Played Sluggo Zoogly')
            self.socket.play_stack.remove(self)
            self.socket.render_game()
        else:
            self.socket.log('Getting card from other player zoo')
            self.socket.play_stack.append(self)
            self.socket.emit('select_card_from_other_zoo', player.player_id, 1)
 
class ZookeeZoogly(Card):
    def __init__(self):
        self.name = 'Zookee Zoogly'
        self.description = 'Move a Monster to your Zoo'
        self.card_type = "Monster"
        self.card_family = "Zoogly"
        self.cost = 3
        self.image = "/static/images/Zoogly.png"
        self.socket = '' # this will hold the socketio object
    
    def play(self, player):
        self.socket.log('In the Play Loop for Zookee Zoogly')
        if self.socket.selected_cards:
            self.move_selected_card_to_zoo(player)
            #card = self.get_selected_card()
            #player.hand.remove_card(card)
            #player.zoo.add_to_bottom(card)
            self.discard(player)
            self.socket.log('Played: Zookee Zoogly')
            self.socket.selected_cards = [] # reset the selected cards
            self.socket.render_game()
            self.socket.play_stack.remove(self)
        else:
            self.socket.log('Going to select_cards function')
            try:
                zookee = player.hand.cards.index(self)
            except:
                zookee = None
                print "Zookee is not in hand."
            self.select_only_monsters(1, player, zookee) # issue with meera boogly, if this is run then meera is played before card can be selected
            self.socket.play_stack.append(self)
            print "Zookee: Play stack is %r" % self.socket.play_stack

class ZoomiZoogly(Card):
    def __init__(self):
        self.name = 'Zoomi Zoogly'
        self.description = 'Move a Monster to your Zoo. If you put an Oogly into your Zoo, draw 2 cards.'
        self.card_type = "Monster"
        self.card_family = "Zoogly"
        self.cost = 5
        self.image = "/static/images/Zoogly.png"
        self.socket = '' # this will hold the socketio object
    
    def play(self, player):
        self.socket.log('In the Play Loop for Zoomi Zoogly')
        if self.socket.selected_cards:
            self.move_selected_card_to_zoo(player)
            if card.card_family == "Oogly":
                player.deal(2)
            self.discard(player)
            self.socket.log('Played: Zoomi Zoogly')
            self.socket.selected_cards = [] # reset the selected cards
            self.socket.render_game()
            self.socket.play_stack.remove(self)
        else:
            self.socket.log('Going to select_cards function')
            try:
                zoomi = player.hand.cards.index(self)
            except:
                zoomi = None
                print "Zoomi is not in hand."
            self.select_only_monsters(1, player, zoomi) # issue with meera boogly, if this is run then meera is played before card can be selected
            self.socket.play_stack.append(self)
            print "Zoomi: Play stack is %r" % self.socket.play_stack

class Deck(object):
    def __init__(self):
        self.cards = []
    
    def shuffle_cards(self):
        random.shuffle(self.cards)

    def show_cards(self):
        for card in self.cards:
            print card
    
    def draw_card(self):
        try:
            card = self.cards.pop(0)
            return card
        except:
            print "No more cards in deck"
            return None

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
        starter_deck = [BossiZoogly(), ZookeeZoogly(), ZookeeZoogly(), ZookeeZoogly(), ZookeeZoogly(), DirtySocks(), DirtySocks(), DirtySocks(), DirtySocks(), DirtySocks(), DirtySocks()]
        self.deck = Deck()
        self.deck.cards = list(starter_deck)
        self.hand = Hand()
        self.discard = Deck()
        self.zoo = Hand()
        self.food = 0
        self.food_discount = 0
        self.score = 0
        self.player_id = player_id
        self.turn = False
    
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
            if card:
                self.hand.add_to_bottom(card)
                cards.append(card)
            else:
                print "No cards drawn. Did not append any cards"
        return cards
    
    def play(self, card):
        card.play(self)

class Wild(Player):
    def __init__(self, player_id='wild'):
        starter_deck = [
                BooBoogly(),
                BooBoogly(),
                MeeraBoogly(),
                MeeraBoogly(),
                OoglyBoogly(),
                OoglyBoogly(),
                Cookies(),
                Cookies(),
                FumbleeBoogly(),
                FumbleeBoogly(),
                WhompoBoogly(),
                WhompoBoogly(),
                BoomerBoogly(),
                BoomerBoogly(),
                KoppiBoogly(),
                KoppiBoogly(),
                LanzoBoogly(),
                LanzoBoogly(),
                LurtiBoogly(),
                LurtiBoogly(),
                PortaBoogly(),
                PortaBoogly(),
                ChunkyOogly(),
                ChunkyOogly(),
                RinkaOogly(),
                RinkaOogly(),
                JusteeZoogly(),
                JusteeZoogly(),
                OhnoZoogly(),
                OhnoZoogly(),
                HuntoOogly(),
                HuntoOogly(),
                YummliOogly(),
                YummliOogly(),
                ZoomiZoogly(),
                ZoomiZoogly(),
                RipliOogly(),
                RipliOogly(),
                ParksOogly(),
                ParksOogly(),
                FifiOogly(),
                FifiOogly(),
                SluggoZoogly(),
                SluggoZoogly(),
                ViktorZoogly(),
                ViktorZoogly(),
                BossiZoogly(),
                BossiZoogly(),
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
        player_location = self.players.index(player)
        if player == self.players[-1]:
            # player is last player, next player set to location 0
            next_player = self.players[0]
        else:
            next_player = self.players[(player_location + 1)]
        for x in self.players:
            if x == next_player:
                x.turn = True
            else:
                x.turn = False
        print "Setting food to zero"
        player.food = 0
        print "Reset card costs"
        player.food_discount = 0
        count_of_cards = len(player.hand.cards)
        print "Setting up next turn for Player %r" % player
        print "Player has %r cards" % count_of_cards
        if count_of_cards <= 5:
            cards_to_draw = 5 - count_of_cards
            print "Dealing Player %r cards" % cards_to_draw
            player.deal(cards_to_draw)
            print "Player now has %r cards" % len(player.hand.cards)
        elif count_of_cards > 5:
            print "Player has more than 5 cards. No extra cards dealt"
        print "Calculating zoo effects"
        for card in player.zoo.cards:
            card.zoo_effect(player)

    def calculate_scores(self):
        for player in self.players:
            score = 0
            for card in player.zoo.cards:
                if card.cost:
                    score += card.cost
            player.score = score
            if player.score >= 30:
                self.state = 'end'
                print 'Game Over'
            print "Player %r Score: %r" % (player, player.score)

    def play_game(self):
        high_score = 0
        while high_score < 30:
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
