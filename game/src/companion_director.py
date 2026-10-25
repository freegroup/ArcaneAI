from __future__ import annotations
import re
import threading
from typing import TYPE_CHECKING, List

from llm import LLMMessage

if TYPE_CHECKING:
    from llm import BaseLLMProvider
    from game_history import GameHistory, HistoryEntry
    from inventory import Inventory
    from prompt_config import GoalConfig, MoodConfig


class CompanionDirector:
    """
    Handles background companion logic: mood tracking and goal-drift detection.
    Prompts come from prompt_rule_mood.yaml and prompt_rule_goal.yaml.
    Runs async — results are ready for the next turn, never blocking the game loop.
    """

    MOOD_VARIABLE = 'companion_mood'

    def __init__(self, llm: BaseLLMProvider, inventory: Inventory, game_data: dict,
                 mood: MoodConfig, goal: GoalConfig) -> None:
        self.llm = llm
        self.inventory = inventory
        self.game_data = game_data
        self.mood = mood
        self.goal = goal

    def update_async(self, history: GameHistory) -> None:
        threading.Thread(target=self._update_mood, args=(history,), daemon=True).start()

    def get_goal_reminder(self, history: GameHistory) -> str:
        reminder_text = self.game_data.get('game_target', '')
        if not reminder_text:
            return ''

        entries = history.entries
        interval = self.goal.interval
        if len(entries) < interval or len(entries) % interval != 0:
            return ''
        if self._player_is_on_goal(reminder_text, entries[-interval:]):
            return ''

        return reminder_text

    def _update_mood(self, history: GameHistory) -> None:
        """
        Shifts the mood by at most one step, judged on how the player treats
        the companion in the latest dialogue. The mood is an enum inventory
        variable; its values form the scale from positive to negative.
        """
        scale = self.inventory.get_enum_values(self.MOOD_VARIABLE) or []
        recent = history.recent(self.mood.window, self.mood.history_chars)
        if not scale or not any(not e.is_welcome for e in recent):
            return

        scale_text = ', '.join(scale)
        current = str(self.inventory.get(self.MOOD_VARIABLE, scale[0]))
        messages = [LLMMessage('system', self.mood.rules.replace('{scale}', scale_text).replace('{current}', current))]
        for entry in recent:
            messages.append(LLMMessage('user', entry.user_input))
            messages.append(LLMMessage('assistant', entry.llm_response))
        messages.append(LLMMessage('user', self.mood.question.replace('{scale}', scale_text)))

        try:
            response = self.llm.chat(messages, max_tokens=self.mood.max_output_tokens, label='Begleiter · Stimmung')
        except Exception as e:
            print(f'[MOOD] {e}')
            return
        words = response.content.strip().lower().split()
        detected = re.sub(r'[^\wäöüß]', '', words[0]) if words else ''
        if detected not in scale:
            return
        current_idx = scale.index(current) if current in scale else 0
        # Enforce max one step at a time
        clamped = scale[max(current_idx - 1, min(current_idx + 1, scale.index(detected)))]
        if clamped != current:
            self.inventory.set(self.MOOD_VARIABLE, clamped)
            print(f'[MOOD] {current} → {clamped}')

    def _player_is_on_goal(self, goal: str, recent_entries: List[HistoryEntry]) -> bool:
        history_text = '\n'.join(
            f'Spieler: {e.user_input}\nSpiel: {e.llm_response}'
            for e in recent_entries
        )
        prompt = self.goal.question.replace('{goal}', goal).replace('{history}', history_text)
        try:
            response = self.llm.chat([LLMMessage('user', prompt)], max_tokens=self.goal.max_output_tokens,
                                     label='Begleiter · Spielziel')
            return 'ja' in response.content.lower()
        except Exception:
            return True
