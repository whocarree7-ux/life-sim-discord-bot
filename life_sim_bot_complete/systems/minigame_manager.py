import random
import importlib

class MinigameManager:
    def __init__(self):
        # Local imports to prevent circular dependency
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

    async def run(self, interaction, game_key: str):
        """
        Triggers a minigame based on the key provided.
        Handles the transition from Crime Cog (Slash Command) to Minigame View.
        """
        # Handle random selection
        if game_key == "random" or game_key not in self.game_map:
            game_key = random.choice(list(self.game_map.keys()))

        # Initialize the game class
        game_class = self.game_map[game_key]
        game_instance = game_class()

        # CRITICAL: We pass 'interaction' instead of 'ctx'
        # All your games in /minigames/ MUST now accept 'interaction' in their .start() method
        try:
            success = await game_instance.start(interaction)
            return success
        except Exception as e:
            print(f"Minigame Execution Error ({game_key}): {e}")
            # If the game crashes, we report it via followup
            await interaction.followup.send(f"⚠️ Minigame '{game_key}' failed to load.")
            return False