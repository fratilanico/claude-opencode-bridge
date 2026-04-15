---
name: opencode-first-party-claude-bridge
description: Use when OpenCode Anthropic is authenticated but still behaves like a third-party usage lane, when full interactive OpenCode is required instead of a single-turn wrapper, or when OpenCode session continuity needs to be preserved through local Claude CLI resume.
---

# OpenCode First-Party Claude Bridge

## Overview

This pattern moves the Anthropic transport boundary out of OpenCode and into a local bridge daemon backed by Claude CLI.

## Use this when

- OpenCode Anthropic auth is present but the live path still fails or is billed as a third-party lane
- you need full OpenCode interaction, not just `opencode run` one-shot usage
- you need explicit fixed-session continuity through `claude --resume`

## Do not use this when

- the only problem is a broken plugin import or package mismatch
- the issue is simply missing Claude CLI auth
- you need a cross-platform solution before macOS is proven

## Key pattern

1. Point OpenCode Anthropic provider config at localhost.
2. Keep a non-empty dummy API key because OpenCode expects one.
3. Map OpenCode session ids to stable Claude session ids on disk.
4. Use explicit `--session` continuity tests, not `--continue`, when proving resume behavior.

## Difference from plugin-native auth

- Plugin-native auth fixes OpenCode from inside the client.
- This bridge fixes the transport path from outside the client.

## Verification

- `bash scripts/doctor.sh`
- `bash scripts/smoke-session.sh saffron`
