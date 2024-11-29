# 🕹️ AI-Powered Text Adventure Engine

![Game Screenshot](./images/screnshoot.png)  
_Enter a world where classic text adventures meet the cutting edge of AI._

Welcome to the **AI-Powered Text Adventure Engine**, a modern twist on classic interactive fiction like _Zork_ (originally released in **1980**). Imagine if a **state engine** from the golden age of gaming and a **Large Language Model (LLM)** like GPT had a child—this project is that child.

The engine dynamically generates engaging narratives, custom-tailored to your journey through a world of interconnected rooms, characters, and puzzles. By merging the deterministic logic of a state machine with the creativity of an AI, the result is an adventure that's both structured and limitless.

---

## 🚀 Features
- **State-Driven Gameplay**: Every "room" or "state" dynamically defines the story, puzzles, and actions available.
- **LLM-Driven Storytelling**: An intelligent narrative adapts to your decisions and deepens immersion.
- **Modular Prompts**: Game-specific prompts frame the AI responses, keeping the story coherent and aligned with the adventure's theme.
- **Infinite Possibilities**: Extend the game world with new states, rooms, or narrative prompts.

---

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

---

## 🖥️ How to Run Locally

### Prerequisites
1. Install [Node.js](https://nodejs.org/).
2. An API key for your preferred LLM (e.g., OpenAI GPT-4).

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ai-text-adventure-engine.git
   cd ai-text-adventure-engine