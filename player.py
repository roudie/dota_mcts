import random
from node import Node
import logging
import numpy
import pickle

logger = logging.getLogger('mcts')


class Player:

    #def get_first_move(self, k=1):
        #with open('models/hero_freqs.pickle', 'rb') as f:
        #    a, p = pickle.load(f)
        #    return [[x, 1] for x in numpy.random.choice(a, size=k, p=p)]


    def get_moves(self, move_type, k=1):
        raise NotImplementedError

    def get_best_move(self, move_type):
        moves = self.get_moves(move_type=move_type)
        best_move, best_win_rate = sorted(moves, key=lambda x: x[1], reverse=True)[0]
        return best_move


class RandomPlayer(Player):

    def __init__(self, draft):
        self.draft = draft
        self.name = 'random'

    def get_moves(self, move_type, k=1):
        """
        decide the next move
        """
        #if self.draft.if_first_move():
        #    return self.get_first_move(k)
        moves = self.draft.get_moves()

        return [[x, 1] for x in random.sample(moves, k)]


class HighestWinRatePlayer(Player):

    def __init__(self, draft):
        self.draft = draft
        self.name = 'hwr'
        with open('models/hero_win_rates.pickle', 'rb') as f:
            self.win_rate_dist = pickle.load(f)

    def get_moves(self, move_type, k=1):
        """
        decide the next move
        """
        #if self.draft.if_first_move():
        #    return self.get_first_move(k)
        moves = self.draft.get_moves()
        move_win_rates = [(m, self.win_rate_dist[m]) for m in moves]
        best_k_moves_with_rate = sorted(move_win_rates, key=lambda x: x[1], reverse=True)[:k]
        #best_move, best_win_rate = sorted(move_win_rates, key=lambda x: x[1])[-1]
        return best_k_moves_with_rate


class MCTSPlayer(Player):

    def __init__(self, name, draft, maxiters, c):
        self.draft = draft
        self.name = name
        self.maxiters = maxiters
        self.c = c

    def get_moves(self, move_type, k=1):
        """
        decide the next move
        """
        #if self.draft.if_first_move():
        #    return self.get_first_move(k)

        root = Node(player=self.draft.player, untried_actions=self.draft.get_moves(), c=self.c)

        for i in range(self.maxiters):
            node = root
            tmp_draft = self.draft.copy()

            # selection - select best child if parent fully expanded and not terminal
            while len(node.untried_actions) == 0 and node.children != []:
                # logger.info('selection')
                node = node.select()
                tmp_draft.move(node.action)
            # logger.info('')

            # expansion - expand parent to a random untried action
            if len(node.untried_actions) != 0:
                # logger.info('expansion')
                a = random.sample(node.untried_actions, 1)[0]
                tmp_draft.move(a)
                p = tmp_draft.player
                node = node.expand(a, p, tmp_draft.get_moves())
            # logger.info('')

            # simulation - rollout to terminal state from current
            # state using random actions
            while not tmp_draft.end():
                # logger.info('simulation')
                moves = tmp_draft.get_moves()
                #print(moves)
                if self.draft.move_cnt[0]+self.draft.move_cnt[1] > 30:
                    NameError("move cnt error")

                a = random.sample(moves, 1)[0]
                tmp_draft.move(a)
            # logger.info('')

            # backpropagation - propagate result of rollout game up the tree
            # reverse the result if player at the node lost the rollout game
            while node != None:
                # logger.info('backpropagation')
                if node.player == 0:
                    result = tmp_draft.eval()
                else:
                    result = 1 - tmp_draft.eval()
                node.update(result)
                node = node.parent
            # logger.info('')

        return root.select_final(k=k)
