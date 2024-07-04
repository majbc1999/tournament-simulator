import logging
from copy import deepcopy
from typing import List, Optional

from tournament_simulator.dataclasses.player import Player
from tournament_simulator.dataclasses.tournament import Game, Round, Tournament

logger = logging.getLogger(__name__)


class DoubleRoundRobinTournament(Tournament):
    """
    Class representing a double round-robin chess tournament.
    """

    def __init__(self,
                 name: str,
                 location: str,
                 players: List[Player],
                 tiebreak: str) -> None:
        super().__init__(name, location, players, tiebreak)

    def generate_rounds(self) -> None:
        """
        Generate pairings for the tournament (list of `Round` objects).
        """
        if self.rounds is not None:
            logger.warning("Pairings already generated, skipping.")
            return

        player_list: List[Optional[Player]] = deepcopy(self.players)

        if len(self.players) % 2:
            player_list.append(None)

        rounds = []

        player_whites = {player: 0 for player in player_list}

        for round_num in range(0, len(self.players)):
            games = []

            player_list = [player_list[0]] + [player_list[-1]] + \
                player_list[1:-1]

            for i in range(0, len(player_list) // 2):
                player_1 = player_list[i]
                player_2 = player_list[-i-1]

                if player_1 and player_2:
                    if player_whites[player_1] <= player_whites[player_2]:  # noqa: E501
                        games.append(Game(player_1, player_2))
                        player_whites[player_1] += 1
                    else:
                        games.append(Game(player_2, player_1))
                        player_whites[player_2] += 1

            rounds.append(Round(round_num + 1, games))

        self.rounds = deepcopy(rounds)

        # add reverse color rounds
        for j, round in enumerate(rounds):
            games = []
            for game in round.games:
                games.append(Game(game.black, game.white))
            self.rounds.append(Round(len(self.players) + j, games))

        return
