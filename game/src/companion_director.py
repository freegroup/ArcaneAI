from __future__ import annotations
import threading
from typing import TYPE_CHECKING, List

from llm import LLMMessage

if TYPE_CHECKING:
    from llm import BaseLLMProvider
    from game_history import GameHistory, HistoryEntry
    from inventory import Inventory


REMINDER_INTERVAL = 6


class CompanionDirector:
    """
    Handles background companion logic: mood tracking and goal-drift detection.
    Runs async — results are ready for the next turn, never blocking the game loop.
    """

    def __init__(self, llm: BaseLLMProvider, inventory: Inventory, game_data: dict) -> None:
        self.llm = llm
        self.inventory = inventory
        self.game_data = game_data

    def update_async(self, history: GameHistory) -> None:
        threading.Thread(target=self._update_mood, args=(history,), daemon=True).start()

    def get_goal_reminder(self, history: GameHistory) -> str:
        reminder_text = self.game_data.get('game_target', '')
        if not reminder_text:
            return ''

        entries = history.entries
        if len(entries) < REMINDER_INTERVAL:
            return ''
        if len(entries) % REMINDER_INTERVAL != 0:
            return ''
        if self._player_is_on_goal(reminder_text, entries[-REMINDER_INTERVAL:]):
            return ''

        return reminder_text

    def _update_mood(self, history: GameHistory) -> None:
        # mood_keys come from the inventory enum constraint — the canonical source.
        # The personality template references companion_mood via Jinja2; the enum
        # values define which moods are valid.
        mood_keys = self.inventory.get_enum_values('companion_mood') or []
        if not mood_keys:
            return

        entries = history.entries
        if not entries:
            return

        recent_text = '\n'.join(f'Spieler: {e.user_input}' for e in entries)
        current_mood = str(self.inventory.get('companion_mood', mood_keys[0]))
        prompt = (
            f'Spieler-Nachrichten:\n{recent_text}\n\n'
            f'Aktuelle Stimmung: {current_mood}\n\n'
            f'Du bist ein Verhaltensspiegel des Spielers. '
            f'Ermittle welche Stimmung der Begleiter annehmen soll – passe dich den Bedürfnissen des Spielers an. '
            f'Ausnahme: bei Aggression oder Feindseligkeit ziehe dich zurück statt mitzumachen.\n\n'
            f'Mögliche Zustände: {", ".join(mood_keys)}\n'
            f'Antworte NUR mit einem einzigen Wort aus dieser Liste.'
        )
        try:
            response = self.llm.call_chat([LLMMessage(role='user', content=prompt)])
            detected = response.content.strip().lower().split()[0]
            if detected in mood_keys:
                old = self.inventory.get('companion_mood', '?')
                self.inventory.set('companion_mood', detected)
                print(f'[MOOD] {old} → {detected}')
        except Exception:
            pass

    def _player_is_on_goal(self, goal: str, recent_entries: List[HistoryEntry]) -> bool:
        history_text = '\n'.join(
            f'Spieler: {e.user_input}\nSpiel: {e.llm_response}'
            for e in recent_entries
        )
        prompt = (
            f'Spielziel: {goal}\n\n'
            f'Letzte Konversation:\n{history_text}\n\n'
            f'Hat der Spieler in dieser Konversation das Spielziel aktiv verfolgt '
            f'oder zumindest erwähnt? Antworte nur mit \'ja\' oder \'nein\'.'
        )
        try:
            response = self.llm.call_chat([LLMMessage(role='user', content=prompt)])
            return 'ja' in response.content.lower()
        except Exception:
            return True
