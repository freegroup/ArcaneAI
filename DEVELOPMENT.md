# Development
This repository has two versions of the AI Dungeon engine: the Console version and the Web UI version.

- **Console Version**: The console version can run with user input or voice input by using different Speech-to-Text (STT) engines like Whisper, Faster Whisper, or Google STT.
- **Web Version**: The web version uses the highly advanced Speech-to-Text engine of the Google Chrome browser, which is powered by a Google backend.


## Prerequisites
The prerequisites are required for either the bash version and for the Web version

### Clone the Repository

```sh
git clone https://github.com/freegroup/ai-dungeon.git
cd ai-dungeon

```

### Install Python 3.12.7 and Dependencies

Other versions may work as well, but this is tested and works perfectly.

```sh
# Go into the game directory to prepare the Python environment
cd game 

# Create a virtual environment to keep the global environment clean
python3.12 -m venv venv 

# Activate the virtual environment
source ./venv/bin/activate  

# Install required libraries
pip install -r requirements.txt
```

### An API Key for Your Preferred LLM

Due to the use of `function calling`, the only fully working LLM for now is OpenAI GPT-4. Other models may work with adjustments to the prompt, but as of now, they require more tweaking, and I haven't gotten them running yet.

We use a `.env` file or environment variables to expose API keys for the different LLM and TTS providers. Let’s create one and configure it:

Create a file `./game/.env` with the following content:

```ini
OPENAI_API_KEY=#############your-key##########

# Uncomment and set up additional API keys if needed.
# By default, this project uses OpenAI only.
#
#GEMINI_API_KEY=#####gemini-key##################
#GOOGLE_APPLICATION_CREDENTIALS=./secrets/gen-lang-client-#############.json

# Configuration for the web UI
#
MAP_FILE=TheTipsyQuest.yaml
USERNAME=<username>
PASSWORD=<password>

```


## 🖥️ How to Run the bash version locally

### The very simple state engine
we are still in the `./game` directory

```sh


```