---
id: console
title: 'Console'
---

# 🖥️ How to Run the bash version locally
Alright adventurers, let’s dive in! With `MAP_FILE`, you can specify the file that holds the state engine definition – basically the script that drives our story. You can pass it as an environment variable or set it dynamically when you run the command, like in the example below.

But hey, no expectations for a fantastical world filled with AI-generated images and epic sounds. I hope you’ve been listening closely: we are in the thrilling realm of Text Adventures! So, what awaits you? Brace yourself... it’s TEXT! 😄

And if you feel your motivation wavering or just can't get it to work, don't worry. There’s a short [YouTube video](/examples/state) that walks you through this exact example. It’s worth investing those 10 minutes – trust me. After all, it’s an exciting journey to bend an LLM to your will! 😉

## The very simple state engine
we are still in the `./game` directory and we installed the [prerequisites](/setup/prerequisites)

```sh

# start the engine and your conversation
# https://youtu.be/6V3JYzU5Cd8
#
MAP_FILE=state_normal.yaml python ./src/main.py

```