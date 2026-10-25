"""
The player asks what he can do: stage 2 gets what is possible right now
and gives a subtle hint. Nothing happens in the game.
"""
from .builtin_function import BuiltinContext, BuiltinFunction


class ActionHelfeDemSpieler(BuiltinFunction):
    name = 'helfe_dem_spieler'

    def run(self, context: BuiltinContext) -> str:
        possible = context.engine.state_engine.get_available_actions()
        if not possible:
            return self.texts['noteNothingToDo']
        actions = '\n'.join(f'- {action.description}' for action in possible)
        return self.texts['note'].replace('{actions}', actions)
