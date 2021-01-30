
import logging

from ..db import Database
from .context import Context
from .config import Config

class MatchMaker:
    def __init__(self, config: Config, database: Database):
        self.logger = logging.getLogger(__name__)
        self.database: Database = database
        self.config: Config = config
        self.context: Context = Context()
