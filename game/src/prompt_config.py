"""
Prompt and context-length settings of the pipeline, loaded from the YAML
files in game/prompts/. No prompt text is hard-coded in the engine.

A provider can bring its own version of a file: game/prompts/<provider>/<file>
(e.g. game/prompts/qwen/prompt_rule_stage1.yaml) replaces game/prompts/<file>
for the stage that runs on that provider.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml

PROMPTS_DIR = Path(__file__).parent.parent / 'prompts'


def load_prompt_file(name: str, provider: str = '') -> Dict[str, Any]:
    """game/prompts/<provider>/<name>.yaml if it exists, else game/prompts/<name>.yaml."""
    path = PROMPTS_DIR / provider / f'{name}.yaml'
    if not provider or not path.exists():
        path = PROMPTS_DIR / f'{name}.yaml'
    print(f'[PROMPTS] {name} ← {path.relative_to(PROMPTS_DIR.parent)}')
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@dataclass(frozen=True)
class DecisionConfig:
    """Stage 1 (function choice) — prompt_rule_stage1.yaml."""
    role: str
    decision_rules: str  # {fallback}: name of the fallback function
    history_length: int
    history_chars: int
    max_output_tokens: int
    max_attempts: int
    retry_hint: str  # {reason}, {functions}, {fallback}
    reason_no_call: str
    reason_unknown_function: str  # {called}

    @classmethod
    def load(cls, provider: str = '') -> DecisionConfig:
        d = load_prompt_file('prompt_rule_stage1', provider)
        return cls(
            role=d['role'],
            decision_rules=d['decisionRules'],
            history_length=d['historyLength'],
            history_chars=d['historyChars'],
            max_output_tokens=d['maxOutputTokens'],
            max_attempts=d['maxAttempts'],
            retry_hint=d['retryHint'],
            reason_no_call=d['reasonNoCall'],
            reason_unknown_function=d['reasonUnknownFunction'],
        )


@dataclass(frozen=True)
class NarrationConfig:
    """Stage 2 (narration) for one case — prompt_rule_stage2_with_function.yaml
    (a game action ran) or prompt_rule_stage2_without_function.yaml (none did)."""
    role: str  # who speaks when the game has no personality
    rules: str
    history_length: int
    history_chars: int
    max_output_tokens: int
    extra: Dict[str, Any]  # file-specific keys (actionNote, welcomeInput, fallbackAnswer)

    @classmethod
    def load(cls, name: str, provider: str = '') -> NarrationConfig:
        d = load_prompt_file(name, provider)
        known = ('role', 'rules', 'historyLength', 'historyChars', 'maxOutputTokens')
        return cls(
            role=d['role'],
            rules=d['rules'],
            history_length=d['historyLength'],
            history_chars=d['historyChars'],
            max_output_tokens=d['maxOutputTokens'],
            extra={k: v for k, v in d.items() if k not in known},
        )


@dataclass(frozen=True)
class MoodConfig:
    """Companion mood — prompt_rule_mood.yaml."""
    rules: str  # {scale}, {current}
    question: str  # {scale}
    window: int
    history_chars: int
    max_output_tokens: int

    @classmethod
    def load(cls, provider: str = '') -> MoodConfig:
        d = load_prompt_file('prompt_rule_mood', provider)
        return cls(
            rules=d['rules'],
            question=d['question'],
            window=d['window'],
            history_chars=d['historyChars'],
            max_output_tokens=d['maxOutputTokens'],
        )


@dataclass(frozen=True)
class GoalConfig:
    """Goal reminder (Telegram) — prompt_rule_goal.yaml."""
    interval: int
    question: str  # {goal}, {history}
    max_output_tokens: int

    @classmethod
    def load(cls, provider: str = '') -> GoalConfig:
        d = load_prompt_file('prompt_rule_goal', provider)
        return cls(interval=d['interval'], question=d['question'], max_output_tokens=d['maxOutputTokens'])
