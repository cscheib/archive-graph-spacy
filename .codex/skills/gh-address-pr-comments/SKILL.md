---
name: gh-address-pr-comments
description: "Address GitHub pull request review feedback end to end: inspect review comments and threads, map them to local code or docs changes, validate fixes, push follow-up commits, reply when useful, and resolve review threads. Use when the user asks to 'address all PR comments', 'review PR comments', 'resolve PR feedback', or otherwise wants GitHub review discussions handled on an existing PR."
---

# GitHub PR Review Comments

## Overview

Use this skill to take a PR from "has review feedback" to "feedback addressed and threads resolved." Prefer repository evidence first, then GitHub thread data, then minimal replies that point reviewers to the fix.

## Workflow

1. Identify the target PR and current branch.
2. Fetch unresolved review threads and regular PR comments with `gh`.
3. Classify each thread:
   - requires code or doc change
   - requires explanation only
   - already fixed in current branch and only needs resolution
   - stale or superseded by later changes
4. Make the required local changes before resolving anything.
5. Run the smallest meaningful validation first, then broader validation if the touched area warrants it.
6. Commit and push follow-up fixes.
7. Reply on the PR only when a short note adds useful reviewer context.
8. Resolve review threads after the fix is pushed and verified.
9. Re-check thread state so the user gets a definitive result.

## Gather Review State

Prefer GitHub CLI over browser-only inspection.

- Use `gh pr view <number> --comments` for top-level discussion context.
- Use GraphQL via `gh api graphql` to fetch review threads, including:
  - thread id
  - path
  - line or diff context when available
  - `isResolved`
  - comment bodies and URLs
- When the request is "address comments," focus on unresolved review threads first.
- Keep a local mapping from thread id to planned action so fixes and resolutions stay synchronized.

## Apply Fixes

Read the cited files before editing. Do not trust the comment in isolation if the code has moved.

- For code review findings:
  - implement the minimal correct fix
  - add or update tests when behavior changes or a bug is fixed
  - keep wording, naming, and error messages aligned with the repository's conventions
- For doc review findings:
  - prefer portable relative links over machine-local paths
  - fix the referenced file directly rather than layering redundant notes elsewhere
- For security or SQL-construction comments:
  - validate untrusted inputs early
  - quote or escape only after validation, not instead of validation

## Validate Before Resolve

- Run targeted tests first when the change is localized.
- Run the broader required suite when repository rules require it or when shared code paths changed.
- If validation cannot run, do not silently resolve the thread. State the blocker to the user and, if appropriate, on the PR.

## Comment and Resolve

Use a PR reply only when it adds signal. Good cases:
- the fix is non-obvious
- the thread asked a question and needs an explicit answer
- the final implementation intentionally differs from the literal suggestion

Keep replies short: what changed, where, and what was validated.

Resolve threads only after the fix is present on the PR branch. For GitHub review threads, use the thread id with a GraphQL `resolveReviewThread` mutation.

If the user explicitly says "by address I mean resolve them," still confirm locally that the issues are already fixed or obsolete before resolving.

## Final Check

Before reporting completion:
- verify the branch is pushed
- verify the working tree state
- re-fetch thread status and confirm the remaining unresolved count
- summarize the exact validations run
- call out any comments intentionally left open and why

## Guardrails

- Do not resolve threads that still require code or doc changes.
- Do not claim a comment is fixed without citing the changed file or commit.
- Do not amend or rewrite history unless the user explicitly asks.
- Do not discard unrelated local changes while addressing review feedback.
- When `gh` network calls fail under sandbox restrictions, rerun them with escalation rather than skipping resolution.
