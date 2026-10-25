"""
Something in the game failed (e.g. a game action's script): nothing
happens, and the companion says so, fitting what the player was about to
do. Never offered to stage 1 — the engine chooses it.
"""
from .builtin_function import BuiltinContext, BuiltinFunction


class ActionOnSystemError(BuiltinFunction):
    name = 'on_system_error'

    def run(self, context: BuiltinContext) -> str:
        if context.attempted is None:
            wanted = self.texts['wantedUnknown']
        else:
            wanted = self.texts['wantedKnown'].replace('{description}', context.attempted.description.strip())
        return self.texts['note'].replace('{wanted}', wanted)
