import random
import importlib

class MinigameManager:
    def __init__(self):
        # We map the "minigame" string from your JSON to the actual Class
        # This makes it easy to add new games later
        from minigames.reaction_game import ReactionGame
        from minigames.typing_game import TypingGame
        from minigames.puzzle_game import PuzzleGame
        from minigames.memory_game import MemoryGame

        self.game_map = {
            "reaction": ReactionGame,
            "typing": TypingGame,
            "puzzle": PuzzleGame,
            "memory": MemoryGame
        }

    async def run(self, ctx, game_key: str):
        """
        Triggers a minigame based on the key provided.
        If the key is 'random' or not found, it picks one.
        """
        # Handle random selection
        if game_key == "random" or game_key not in self.game_map:
            game_key = random.choice(list(self.game_map.keys()))

        # Initialize the game class
        game_class = self.game_map[game_key]
        game_instance = game_class()

        # All your games in /minigames/ MUST have a .start(ctx) method
        # that returns True (win) or False (loss)
        success = await game_instance.start(ctx)
        return success
      
