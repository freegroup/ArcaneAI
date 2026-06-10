"""
ArcaneAI — main entry point.
Usage:
    python main.py [runner]

Available runners:
    console    — Interactive terminal game
    web        — FastAPI web server (browser play)
    developer  — REST API for editor integration
    telegram   — Telegram bot

If no runner is specified, an interactive selection is shown.
"""
import sys
from runners import RUNNERS


def select_runner() -> str:
    print()
    print("╔════════════════════════════════════════╗")
    print("║           ArcaneAI — Runner            ║")
    print("╠════════════════════════════════════════╣")
    names = list(RUNNERS.keys())
    for i, name in enumerate(names, 1):
        print(f"║  [{i}] {name:<34}║")
    print("╚════════════════════════════════════════╝")
    print()

    while True:
        try:
            choice = input("Runner wählen (Name oder Nummer): ").strip().lower()
            if choice in RUNNERS:
                return choice
            idx = int(choice) - 1
            if 0 <= idx < len(names):
                return names[idx]
        except (ValueError, KeyboardInterrupt):
            pass
        print(f"Ungültige Eingabe. Optionen: {', '.join(RUNNERS.keys())}")


def main() -> None:
    runner_name = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if runner_name and runner_name not in RUNNERS:
        print(f"Unbekannter Runner: '{runner_name}'")
        print(f"Verfügbar: {', '.join(RUNNERS.keys())}")
        sys.exit(1)

    if not runner_name:
        runner_name = select_runner()

    print(f"\nStarte Runner: {runner_name}\n")
    runner_cls = RUNNERS[runner_name]
    if callable(runner_cls) and not isinstance(runner_cls, type):
        runner_cls = runner_cls()  # call loader function to get the class
    runner_cls().run()


if __name__ == "__main__":
    main()
