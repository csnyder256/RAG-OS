# Contributing

Thanks for helping improve this blueprint. It is a living architecture document, and the best contributions make it more useful to someone building their own system.

## Good contributions

- A worked example of one milestone on a specific stack. Name the frontend, the harness, the model vendor, and the database, and show the proof that the milestone works.
- A decision fork the guide missed, written as a question plus two to four concrete options with trade-offs.
- A failure mode for the anti-patterns section, generalized from a real incident, with the fix.
- Corrections, clarifications, tighter wording, or a translation.

## How to contribute

1. Open an issue describing the change you have in mind, or
2. Fork the repo, edit `BUILD-GUIDE.md` or the `README.md`, and open a pull request.

## Ground rules

- Keep everything vendor-neutral and free of personal or proprietary details. The guide should work for any builder on any stack.
- Preserve the agent protocol contract: the guide instructs the reader's coding agent to stop and ask the user at every decision fork. New decisions should be added as `▶ ASK` forks, not baked-in choices.
- Match the existing tone: plain, direct, honest about trade-offs, no hype.
