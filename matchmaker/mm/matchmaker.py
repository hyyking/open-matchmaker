
import logging

from ..db import Database
from .context import Context
from .config import Config

class MatchMaker:
    def __init__(self, config: Config, database: Database):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config
        self.context = Context()
