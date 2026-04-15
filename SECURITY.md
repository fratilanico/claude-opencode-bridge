# Security Policy

## Supported scope

This repo is intended for local macOS developer machines running OpenCode and Claude CLI.

## Reporting

If you discover a security issue, do not open a public issue containing secrets, machine paths, or credentials. Report the issue privately to the maintainer channel for the fork or downstream distribution you are using.

## Hard rules for contributors

- never commit `.env` files
- never commit personal `opencode.json` or shell startup files
- never commit access tokens, API keys, cookies, bearer headers, or session stores
- keep examples to placeholders and localhost values only
