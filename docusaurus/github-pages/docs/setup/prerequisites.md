---
id: prerequisites
title: 'Prerequisites'
---

# Prerequisites
...so, if your curiosity has been piqued and you’ve been hunting for a <span class="color">"Try it out"</span> button... sorry, not here. Running an LLM for everyone is just too expensive for us normal folks. But don’t worry, I’ll show you how to get it running locally. There’s just one small hurdle... but hey, consider it the first step in your text adventure—obtain the key! Yes, just like in a classic adventure game, but instead of a rusty old key, you'll need an API key from OpenAI to summon GPT-4. 😉

There are two versions: a console version and a UI version. The UI version comes with Chrome’s great speech-to-text feature, but for getting started, the console version is just perfect.



- <span class="color">Console Version</span>: The console version can run with user input or voice input by using different Speech-to-Text (STT) engines like Whisper, Faster Whisper, or Google STT.
- <span class="color">Web Version</span>: The web version uses the highly advanced Speech-to-Text engine of the Google Chrome browser, which is powered by a Google backend.


The prerequisites are required for either the bash version and for the Web version

### Clone the Repository

```bash
git clone https://github.com/freegroup/ArcaneAI.git
cd ArcaneAI

```

### Install Python 3.12.7 and Dependencies

Other versions may work as well, but this is tested and works perfectly.

```bash
# Go into the ./game directory to prepare the Python environment
cd game 

# Create a virtual environment to keep the global environment clean
python3.12 -m venv venv 

# Activate the virtual environment
source ./venv/bin/activate  

# Install required libraries
pip install -r requirements.txt
```

### An API Key for Your Preferred LLM

Due to the use of `function calling`, the only fully working LLM for now is OpenAI GPT-4o. Other models may work with adjustments to the prompt, but as of now, they require more tweaking, and I haven't gotten them running yet.

I use a `.env` file or environment variables to expose API keys for the different LLM and TTS providers. Let’s create one and configure it:

Create a file `./game/.env` with the following content:

```bash
OPENAI_API_KEY=#############your-key##########

# Uncomment and set up additional API keys if needed.
# By default, this project uses OpenAI only.
#
#GEMINI_API_KEY=#####gemini-key##################
#GOOGLE_APPLICATION_CREDENTIALS=./secrets/gen-lang-client-#############.json

# info, debug, error, fatal
ARCANEAI_LOG_LEVEL=info

# Configuration for the web UI
#
MAP_FILE=TheTipsyQuest
USERNAME=<username>
PASSWORD=<password>

```


now you are ready to run a demo setup...