---
title: RAG-OS
description: A vendor-neutral blueprint for building a self-hosted, always-on personal AI OS, plus a runnable starter. A DIY alternative to Letta, mem0, Hermes Agent, and AutoGPT.
---

**Build your own always-on AI agent that dispatches coding tasks across your repositories, maintains its own git-Markdown knowledge base, and runs on hardware you own.** RAG-OS is a vendor-neutral blueprint you paste into any coding agent (Claude Code, Codex, Cursor, an agent SDK, or a plain API loop), and it builds the system with you, asking at every design decision.

[Read the build guide](https://github.com/csnyder256/RAG-OS/blob/main/BUILD-GUIDE.md) &nbsp;&middot;&nbsp; [Run the starter](https://github.com/csnyder256/RAG-OS/tree/main/starter) &nbsp;&middot;&nbsp; [GitHub repository](https://github.com/csnyder256/RAG-OS)

![RAG-OS architecture](https://raw.githubusercontent.com/csnyder256/RAG-OS/main/images/architecture.png)

## What it is

It is not a framework to install. It is a compiled architecture: twelve pillars, a security model, nineteen hard-won failure modes to design against, and a milestone build order where every step is proven with real output before it counts as done. The founding rule is that durable state lives in files and a database, the brains are ephemeral sessions, and a small kernel coordinates everything and holds zero model context. Nothing a model remembers survives a single session, so a crash, a restart, or a model downgrade loses no durable state.

## What you get

- An always-on kernel: a supervised background process (watchdog, heartbeat, internal cron) that holds no model context.
- An orchestrator that talks to you and decides, plus ephemeral workers that do real edits inside a repository and never talk to you.
- A git-Markdown knowledge base the agent maintains as a librarian, with index-first retrieval and hybrid keyword plus vector search.
- A budget governor, a capability-based model registry across vendors, and a security model where a permission hook checks every tool call.
- A runnable, stdlib-only starter for the first two milestones.

## How it compares

None of the individual ideas here are new. Almost every piece exists as a more mature product or library. The value is having all of them as one owned, transparent, always-on system.

| Project | What it is | How RAG-OS relates |
|---|---|---|
| Hermes Agent | Open-source always-on agent | Closest comparable; RAG-OS goes further on hybrid retrieval and a git-Markdown librarian. |
| Letta / MemGPT | Stateful-agent runtime with tiered memory | The closest cousin on memory; RAG-OS wraps a whole OS around the memory core. |
| mem0 | Drop-in memory API | Simpler and more mature at user memory; a plausible substitute for the memory layer. |
| Anthropic base (Claude Agent SDK, memory tool) | Primitives for agent memory and hooks | RAG-OS is the assembled system the base does not give you. |
| Devin | Autonomous software engineer | The commercial version of the worker-dispatch layer. |
| AutoGPT / BabyAGI | The original goal-loop agents | The naive ancestors, without supervision, memory discipline, or security. |

## FAQ

**Is this just RAG with extra steps?** The write side is not RAG: the agent externalizes new lessons into the wiki, deduplicates them, and retires superseded facts on a schedule so the base does not rot.

**Does a Markdown wiki beat a vector database?** You use both. The Markdown is the source of truth because it is auditable and portable across models; the vector index is a rebuildable cache over it (hybrid BM25 plus vector, fused with reciprocal rank fusion).

**An autonomous agent with repository write access sounds dangerous.** Every tool call is checked in code, path fences are normalized against traversal and symlink tricks, dangerous actions need a one-time approval code, and anything the agent reads is treated as data rather than instructions.

**Isn't this lock-in?** The model layer is behind aliases in one config file across vendors, and the harness is a swappable seam, so you can move between an SDK, a CLI, and local models.

## Get started

Paste [BUILD-GUIDE.md](https://github.com/csnyder256/RAG-OS/blob/main/BUILD-GUIDE.md) into your coding agent and say: "Help me build this. Follow the agent protocol at the top." It asks you at every fork, so the result matches your machine, your budget, and your risk tolerance.

If RAG-OS is useful to you, a [star](https://github.com/csnyder256/RAG-OS) helps other people find it.
