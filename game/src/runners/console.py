"""
Console runner — interactive terminal game loop.
"""
from __future__ import annotations
from pathlib import Path

from .base import BaseRunner
from session import GameSession
from config_loader import load_config
from audio import PyAudioSink
from sound import LocalJukebox


class ConsoleRunner(BaseRunner):
    """Runs the game as an interactive console session."""

    def run(self) -> None:
        print("=" * 60)
        print("TEXT ADVENTURE GAME")
        print("=" * 60)
        print()

        try:
            print("Initialisiere Spiel...")
            config = load_config()
            session = GameSession(
                session_id="console",
                config=config,
                audio_sink=PyAudioSink(sample_rate=24000),
                jukebox=LocalJukebox(config=config)
            )

            llm = session.game_engine.controller.llm
            provider_name = llm.__class__.__name__.replace("Provider", "")
            print(f"LLM: {provider_name} - {llm.model}")
            print("Spiel bereit!")
            print()

        except Exception as e:
            print(f"Fehler beim Initialisieren: {e}")
            import traceback
            traceback.print_exc()
            return

        initial_desc = session.game_engine.start_game()
        print(initial_desc)
        print()
        print("(Tippe 'quit' zum Beenden, 'help' für Hilfe)")
        print()

        while True:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue

                if user_input.lower() == 'quit':
                    print("Auf Wiedersehen!")
                    break

                if user_input.lower() == 'help':
                    help_text = session.game_engine.game_data.get('help_text', '')
                    if help_text:
                        # Strip HTML tags for console output
                        import re
                        print("\n" + re.sub(r'<[^>]+>', '', help_text))
                    else:
                        print("\nVerfügbare Befehle:")
                        print("  quit      — Spiel beenden")
                        print("  state     — Aktuellen State anzeigen")
                        print("  inventory — Inventar anzeigen")
                        print("  vars      — Alle Lua-Variablen anzeigen")
                        print("  actions   — Verfügbare Actions anzeigen")
                    print()
                    continue

                if user_input.lower() == 'state':
                    state = session.game_engine.state_engine.get_current_state()
                    print(f"\n{state}")
                    print(f"Description: {state.get_description()}")
                    print()
                    continue

                if user_input.lower() == 'inventory':
                    inv = session.game_engine.inventory.to_dict()
                    print("\n" + "=" * 50)
                    print("INVENTAR")
                    print("=" * 50)
                    for key, value in sorted(inv.items()):
                        val_str = "true" if value is True else "false" if value is False else str(value)
                        print(f"  {key:.<40} {val_str:>5}")
                    print("=" * 50 + "\n")
                    continue

                if user_input.lower() == 'vars':
                    print(f"\nAlle Lua-Variablen: {session.game_engine.inventory.get_all_vars()}\n")
                    continue

                if user_input.lower() == 'actions':
                    actions = session.game_engine.state_engine.get_available_actions()
                    print(f"\nVerfügbare Actions ({len(actions)}):")
                    for action in actions:
                        print(f"  - {action.name}")
                        if action.description:
                            print(f"    → {action.description[:80]}")
                    print()
                    continue

                print()
                response = session.game_engine.process_input(user_input)
                print(response)
                print()

            except KeyboardInterrupt:
                print("\n\nSpiel unterbrochen.")
                break
            except Exception as e:
                print(f"\nFehler: {e}")
                import traceback
                traceback.print_exc()
                print()
