# Architecture


## 🛠️ Technical Details

This engine is built at the intersection of traditional programming and AI innovation:
1. **Internal State Engine**:
   - Controls the flow of the game: which room you're in, available actions, and the consequences of your decisions.
   - Provides the scaffolding for deterministic, rule-based logic.

2. **Large Language Model (LLM)**:
   - Injects creativity into the game.
   - Each state modifies the system prompt to guide the LLM's responses, ensuring they stay consistent with the world-building and narrative.

3. **Dynamic Prompts**:
   - Every "room" or "state" uses its unique system prompt to adapt the LLM's storytelling to the context of the current environment.

### Why This Approach?
Unlike classic text adventure engines, which rely solely on predefined scripts, this engine combines deterministic logic (state engines) with the dynamic and creative potential of LLMs. The result is a game that's both predictable enough to feel structured and creative enough to surprise you.
