import logging
from enum import Enum
from typing import Optional, Union

logger = logging.getLogger(__name__)


class Title(Enum):
    GM = "Grandmaster"
    IM = "International Master"
    FM = "FIDE Master"
    CM = "Candidate Master"
    WGM = "Woman Grandmaster"
    WIM = "Woman International Master"
    WFM = "Woman FIDE Master"
    WCM = "Woman Candidate Master"


class Player:
    """
    Class represents a chess player.
    """
    first_name: str
    last_name: str
    nationality: str
    gender: str
    title: Optional[Title]
    rating: int

    def __init__(self,
                 first_name: str,
                 last_name: str,
                 nationality: str,
                 title: Optional[Union[Title, str]],
                 rating: Optional[int]) -> None:
        self.first_name = first_name
        self.last_name = last_name

        if isinstance(title, str):
            try:
                self.title = Title[title.upper()]
            except ValueError:
                logger.warning("Invalid title, setting to None.")
        else:
            self.title = title

        self.nationality = nationality

        if rating is None:
            self.rating = 1500
        self.rating = rating

    def full_name(self) -> str:
        """
        Returns the full name of the player.
        """
        if self.title:
            return f"{self.title.name} {self.first_name} {self.last_name} " + \
                        f"({self.rating})"
        return f"{self.first_name} {self.last_name} ({self.rating})"
