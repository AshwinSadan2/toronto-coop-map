SYSTEMS DESIGN AGENT — README
==============================

WHAT THIS IS
------------
A thinking partner that turns your fuzzy idea into a real system plan BEFORE
you start building. It interviews you through 5 stages (outcome, inputs,
logic, output, edges) and produces two files:

  1. plan.md       — a structured spec you can use as context for building
  2. diagram.html  — a visual flowchart of your system (open in any browser)

The whole thing takes about 15-20 minutes.

Why bother? Because most people hand Claude a weak one-line prompt and end up
with something brittle that breaks the moment it hits real data. This step
prevents that.


HOW TO USE IT
-------------
1. Open your terminal.

2. Navigate into this folder:
     cd path/to/this/folder

3. Start Claude Code:
     claude

4. Say hello. Literally type:
     hello

5. The agent will take it from there. Answer its questions honestly and
   specifically — the more specific you are, the better your plan will be.

TIP: Use speech-to-text. Talk to it like you'd talk to a smart colleague
who's never heard your idea before. It's faster and you'll give better
answers than if you type.


WHAT HAPPENS AT THE END
-----------------------
When the agent has enough information, it will:

  - Play back its understanding of your system and ask you to confirm
  - Write plan.md with the full spec
  - Generate diagram.html with a visual flow of your system

Open diagram.html in your browser to see the visual. Keep plan.md handy —
you'll feed it into a fresh Claude Code session when you're ready to build.


GOOD ANSWERS vs. BAD ANSWERS
----------------------------
Bad:  "I want to automate outbound."
Good: "When a Series B SaaS company posts a VP of Sales job, I want the
       system to find the hiring manager's email and draft a personalized
       outbound message I can review before sending."

The agent will push you for specifics. Let it. That's the point.


IF YOU GET STUCK
----------------
Ask Claude first, ask your instructor second.

If the agent goes off-track, just tell it: "Let's back up to stage [X]."
It will reset and continue.
