---
id: browser
title: 'Browser'
---

# 🌐 Now with Extra Shenanigans!
So, you've conquered the command line and now hunger for more? Enter the _**browser version**_, a magical realm where you can chat with the bot using nothing but your voice. That's right – no more endless cycles of typing, listening, and typing again. (Remember those old-school parser games where you typed `LOOK AT TREE` and got back, `THERE IS NO TREE`? Yeah, none of that here!)

Instead, with speech-to-text, you simply speak, and the bot hangs on your every word. It's like having a super-intelligent parrot that talks back… minus the feathers and the existential angst.

## Why Should You Care?
Apart from feeling like a tech wizard casting spells with your voice, this setup is perfect for anyone who wants to immerse themselves in a seamless and surprisingly human-like experience. No typing interruptions, no keyboard clatter—just you, the bot, and some seriously good vibes.

And hey, if you've ever dreamed of a world where tech meets empathy, this one's for you: it's an absolute boon for folks with visual impairments or anyone who just wants to avoid the "type–click–repeat" grind. Truly, the future is here, and it sounds amazing.

## A Quick Word About Echoes (The Fun Kind, Not the Greek Myth)
But, a word of caution: the current version doesn't have echo cancellation built-in. (Not yet, my dear adventurers, but rest assured, it's on the to-do list!) This means if you're rocking out without a headset, the bot might end up listening to its own voice and responding... to itself. Forever. It's the kind of loop that would make even a pirate's parrot squawk in confusion. 🦜🔄

<div style={{textAlign: 'center'}}>
  ![choose](/img/headset-choose.png)
</div>

So, what's the solution? Simple: grab a headset and sail smooth seas! Your neighbors will thank you, the bot will stay sane, and you'll avoid creating an accidental AI soap opera.

## The very simple state engine
we are still in the `./game` directory and we installed the [prerequisites](/setup/prerequisites)

```sh

# start the engine and your conversation
# https://www.youtube.com/watch?v=6079pmcyhNI
#
MAP_FILE=state_normal python ./src/server.py

```