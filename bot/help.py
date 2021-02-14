""" Bot help command """

from discord.ext import commands


class Help(commands.HelpCommand):
    """ Help Command """

    async def send_bot_help(self, mapping):
        if len(mapping) == 0:
            return
        dest = self.get_destination()
        message = """```BabyHaxbud MatchMaker
    admin:
        - set_threshold: set queue trigger threshold (doesn't update the queue)
        - set_principal: set match decision method
        - reset: reset queue and current games (doesn't clear the history)
        - clear_queue: removes everybody from the queue
        - clear_history: removes all matches from the match history
        - games: dumps all current games
    
    user:
        - register: 
            registers a team with a player
            example: +register @BabyHaxbud MyNewTeam

        - teams:
            shows all the teams you or the person are part of
            example: +teams / +teams @BabyHaxbud

        - leaderboard:
            shows the 15 best ranked teams
            example: +leaderboard

        - stats:
            creates a graph with elo evolution
            example: +stats / +stats MyNewTeam

        - queue:
            adds your team to the queue, you need to specify the name
            example: +queue MyNewTeam
        
        - dequeue:
            dequeues the team you queued
            example: +dequeue
        
        - who:
            see who is currently queued
            example: +who

        - result:
            specifies the result of your current game (keep the order of the teams)
            example: +result 3-7
```"""
        await dest.send(content=message)
