# Privacy

What data, if any, is collected when you visit `superpowers.zsl.dev` and when you use the ZSL Superpowers plugin itself.

## This site

`superpowers.zsl.dev` is a static documentation site hosted on GitHub Pages. It contains no forms, sign-ups, comments, analytics, or advertising. We do not set any first-party cookies and do not track visitors.

GitHub serves the site and may log standard request metadata (IP, user-agent, requested URL) under their own infrastructure logging — see [GitHub's Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement) for what they retain and for how long.

The HTTPS certificate is issued automatically by Let's Encrypt; this is a standard certificate-authority interaction with no user-data implications.

## The plugin

The `zsl` plugin you install via `/plugin install zsl@zsl-superpowers` runs entirely inside your local Claude Code session. The skills do not phone home, do not collect telemetry, and do not transmit any data to ZunoSmartLabs. They operate on the files in your repo and the conversation in your Claude Code session — both of which stay between you and Anthropic per your existing Claude Code agreement.

The [`timesheet`](skills.md#timesheet) skill reads your local Claude Code session histories from `~/.claude/projects/` to summarise recent work. That data never leaves your machine; the skill writes nothing back to those files.

## Source code

Everything that runs locally is open source at [github.com/ZunoSmartLabs/zsl-superpowers](https://github.com/ZunoSmartLabs/zsl-superpowers). You can audit any skill's behaviour before invoking it.

## Changes to this policy

If this policy changes materially, we'll bump the "Last updated" date below and note significant changes in the repo's commit history.

## Contact

Questions about privacy or the plugin's behaviour: open an issue at [github.com/ZunoSmartLabs/zsl-superpowers/issues](https://github.com/ZunoSmartLabs/zsl-superpowers/issues).

_Last updated: 9 May 2026._
