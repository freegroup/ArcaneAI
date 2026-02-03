"""
Main entry point for the text adventure game.
Console interface for playing the game.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from llm import LLMFactory
from state_engine import StateEngine
from game_controller import GameController
from session import GameSession


def main():
    """Main game loop."""
    print("=" * 60)
    print("TEXT ADVENTURE GAME")
    print("=" * 60)
    print()
    
    # Initialize components
    try:
        print("Initialisiere Spiel...")
        
        # Load state engine
        definition_path = Path(__file__).parent / "game_definition_tipsy_full.json"
        state_engine = StateEngine(str(definition_path))
        
        # Load LLM
        llm_factory = LLMFactory()
        
        # Create game controller
        controller = GameController(state_engine, llm_factory)
        
        # Create single session for console mode
        session = GameSession("console", controller)
        
        print("Spiel bereit!")
        print()
        
    except Exception as e:
        print(f"Fehler beim Initialisieren: {e}")
        return
    
    # Start game
    initial_desc = session.start_game()
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
                print("- help: Diese Hilfe anzeigen")
                print()
                continue
            
            if user_input.lower() == 'state':
                print(f"\nAktueller State: {session.get_current_state()}")
                print(session.game_controller.state_engine.get_current_state_description())
                print()
                continue
            
            if user_input.lower() == 'inventory':
                print(f"\nInventar: {session.inventory if session.inventory else 'Leer'}\n")
                continue
            
            # Process input through LLM
            print()
            response = session.process_input(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nSpiel unterbrochen.")
            break
        except Exception as e:
            print(f"\nFehler: {e}")
            print()


if __name__ == "__main__":
    main()