"""
Main entry point for the text adventure game.
Console interface for playing the game.
"""
from pathlib import Path
from session import GameSession


def main():
    """Main game loop."""
    print("=" * 60)
    print("TEXT ADVENTURE GAME")
    print("=" * 60)
    print()
    
    # Initialize session (creates all components)
    try:
        print("Initialisiere Spiel...")
        
        definition_path = Path(__file__).parent.parent / "game_definition_tipsy_full.json"
        
        # Create session - it creates everything else!
        session = GameSession(
            session_id="console",
            definition_path=str(definition_path)
        )
        
        print("Spiel bereit!")
        print()
        
    except Exception as e:
        print(f"Fehler beim Initialisieren: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Start game
    initial_desc = session.game_engine.start_game()
    print(initial_desc)
    print()
    print("(Tippe 'quit' zum Beenden, 'help' für Hilfe)")
    print()
    
    # Game loop
    while True:
        try:
            # Get user input
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() == 'quit':
                print("Auf Wiedersehen!")
                break
            
            if user_input.lower() == 'help':
                print("\nVerfügbare Befehle:")
                print("- quit: Spiel beenden")
                print("- state: Aktuellen State anzeigen")
                print("- inventory: Inventar anzeigen")
                print("- vars: Alle Lua-Variablen anzeigen (Debug)")
                print("- actions: Verfügbare Actions anzeigen")
                print("- help: Diese Hilfe anzeigen")
                print()
                continue
            
            if user_input.lower() == 'state':
                state = session.game_engine.state_engine.get_current_state()
                print(f"\n{state}")  # Uses __str__
                print(f"Description: {state.get_description()}")
                print()
                continue
            
            if user_input.lower() == 'inventory':
                inv = session.game_engine.inventory.to_dict()
                print("\n" + "=" * 50)
                print("INVENTAR")
                print("=" * 50)
                
                for key, value in sorted(inv.items()):
                    # Format value
                    if isinstance(value, bool):
                        val_str = "true" if value else "false"
                    else:
                        val_str = str(value)
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
                    if action.conditions:
                        print(f"    Conditions: {action.conditions}")
                print()
                continue
            
            # Process input through game engine
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


if __name__ == "__main__":
    main()