"""
None of the game's actions fits: nothing happens, the companion just
answers. Also what counts when stage 1 gives no usable answer.
"""
from .builtin_function import BuiltinContext, BuiltinFunction


class ActionKeineAktion(BuiltinFunction):
    name = 'keine_aktion'

    def run(self, context: BuiltinContext) -> str:
        return self.texts['note']
