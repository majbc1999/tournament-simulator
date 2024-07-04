import logging
import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pandas as pd

from tournament_simulator.dataclasses.player import Player

logger = logging.getLogger(__name__)

class Result(Enum):
    WHITE = (1, 0)
    BLACK = (0, 1)
    DRAW = (0.5, 0.5)


class Game:
    """
    Class representing a game in a chess tournament.
    """
    white: Player
    black: Player
    result: Optional[Result]

    def __init__(self,
                 white: Player,
                 black: Player) -> None:
        self.white = white
        self.black = black
        self.result = None

    def set_result(self,
                   result: Enum) -> None:
        """
        Set the result of the game.
        """
        self.result = result

    def simulate_game(self) -> None:
        """
        Simulate the game based on ratings and corresponding probabilities.
        """
        if self.result is not None:
            logger.warning(f"Game {self.white.last_name} vs "
                           f"{self.black.last_name} already simulated,"
                           " skipping.")
            return

        elo_diff = self.white.rating - self.black.rating

        # expected score for white player
        white_weight = 1 / (1 + 10 ** (-elo_diff / 400))
        black_weight = 1 / (1 + 10 ** (elo_diff / 400))

        # draw probability based on rating difference:
        # https://en.chessbase.com/post/sonas-what-exactly-is-the-problem-
        if abs(elo_diff) <= 100:
            draw_prob = 0.35
        elif abs(elo_diff) <= 200:
            draw_prob = 0.25
        elif abs(elo_diff) <= 300:
            draw_prob = 0.15
        elif abs(elo_diff) <= 400:
            draw_prob = 0.10
        else:
            draw_prob = 0.05

        # enhance draw probability if both players have high ratings and 
        # vice versa
        higher_player_rating = max(self.white.rating, self.black.rating)

        if higher_player_rating >= 2500:
            draw_prob *= 1.3

        elif higher_player_rating <= 2000:
            draw_prob *= 0.7

        # calculate probabilities
        not_draw_prob = 1 - draw_prob
        white_prob = white_weight * not_draw_prob
        black_prob = black_weight * not_draw_prob

        self.result = random.choices(population=[Result.WHITE,
                                                 Result.BLACK,
                                                 Result.DRAW],
                                     weights=[white_prob * 1.05,
                                              black_prob * 0.95,
                                              draw_prob],
                                     k=1)[0]
        
        return


class Round:
    """
    Class representing a round in a chess tournament.
    """
    number: int
    games: List[Game]
    finished: bool

    def __init__(self,
                 number: int,
                 games: List[Game]) -> None:
        self.number = number
        self.games = games
        self.finished = False

    def simulate_round(self) -> None:
        """
        Simulate all games in the round.
        """
        if self.finished:
            logger.warning(f"Round {self.number} already simulated, skipping.")
            return

        for game in self.games:
            game.simulate_game()

        self.finished = True
        return


class Tournament(ABC):
    """
    Abstract class representing a chess tournament.
    """
    name: str
    location: str
    players: List[Player]
    rounds: Optional[List[Round]]
    tiebreak: Optional[str]

    def __init__(self,
                 name: str,
                 location: str,
                 players: List[Player],
                 tiebreak: Optional[str]) -> None:
        self.name = name
        self.location = location
        self.rounds = None

        # TODO: tiebreaks must not be hardcoded
        if tiebreak is not None and tiebreak.lower() not in ['buchholz',
                                                             'opponent_rating',
                                                             'most_wins']:
            logger.error(f"Invalid tiebreak: {tiebreak}. "
                         "Instead using `None`.")
            self.tiebreak = None
        else:
            self.tiebreak = tiebreak.lower()

        # sort players by rating
        self.players = sorted(players,
                              key=lambda x: x.rating,
                              reverse=True)

    def simulate_tournament(self) -> None:
        """
        Simulate the tournament.
        """
        if self.rounds is None:
            logger.error("No rounds generated. Please generate the pairings"
                         " first.")

        for rnd in self.rounds:
            rnd.simulate_round()

        return

    def calculate_leaderboard(
            self) -> Dict[Player, Tuple[float, int, int, int, float]]:
        """
        Calculate the leaderboard of the tournament.
        """
        # meaning [points, wins, draws, losses, tiebreak_value]
        ldb = {p.full_name(): [0, 0, 0, 0, 0] for p in self.players}
        rounds_played = 0

        for rnd in self.rounds:
            if not rnd.finished:
                break
            else:
                rounds_played += 1

            for game in rnd.games:
                match game.result:
                    case Result.WHITE:
                        ldb[game.white.full_name()][0] += 1
                        ldb[game.white.full_name()][1] += 1
                        ldb[game.black.full_name()][3] += 1
                    case Result.BLACK:
                        ldb[game.black.full_name()][0] += 1
                        ldb[game.black.full_name()][1] += 1
                        ldb[game.white.full_name()][3] += 1
                    case Result.DRAW:
                        ldb[game.white.full_name()][0] += 0.5
                        ldb[game.white.full_name()][2] += 1
                        ldb[game.black.full_name()][0] += 0.5
                        ldb[game.black.full_name()][2] += 1

                if self.tiebreak == 'most_wins':
                    if game.result == Result.WHITE:
                        ldb[game.white.full_name()][4] += 1
                    elif game.result == Result.BLACK:
                        ldb[game.black.full_name()][4] += 1                        

        if self.tiebreak == 'buchholz':
            for player in ldb:
                buchholz = 0
                for rnd in self.rounds:
                    for game in rnd.games:
                        if game.white.full_name() == player:
                            buchholz += ldb[game.black.full_name()][0]
                        elif game.black.full_name() == player:
                            buchholz += ldb[game.white.full_name()][0]
                ldb[player][4] = buchholz

        elif self.tiebreak == 'opponent_rating':
            for player in ldb:
                opponent_rating = 0
                for rnd in self.rounds:
                    for game in rnd.games:
                        if game.white.full_name() == player:
                            opponent_rating += game.black.rating
                        elif game.black.full_name() == player:
                            opponent_rating += game.white.rating
                ldb[player][4] = round(opponent_rating / rounds_played, 2)

        for key, value in ldb.items():
            ldb[key] = tuple(value)

        return ldb

    def display_leaderboard(self) -> pd.DataFrame:
        """
        Display the leaderboard of the tournament.
        """
        leaderboard = self.calculate_leaderboard()

        df = pd.DataFrame.from_dict(leaderboard,
                                    orient='index',
                                    columns=['Points',
                                             'Wins',
                                             'Draws',
                                             'Losses',
                                             'Tiebreak'])

        df = df.sort_values(by=['Points', 'Tiebreak'],
                            ascending=False)

        return df