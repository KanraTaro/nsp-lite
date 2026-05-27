# Known Issues And Platform Hardening

This document records known platform-level hardening work. It is not a claim
that the items below are implemented.

## Action Result Semantics

NSPL needs one authoritative result contract across Entry, Web, RohTalk,
ChatOps, AutoRoh, and domain bridges. Results should distinguish queued,
delivered, executed, rejected, failed, and timeout or unknown outcomes so
agents and control surfaces cannot mistake an unconfirmed action for success.

## ChatOps Reliability Fields

ChatOps task schema and command surfaces include `priority`, `timeout_sec`, and
`retries_max`. The worker does not yet fully enforce those operational
semantics. Until that is addressed, they should not be treated as end-to-end
reliability guarantees.

## Entry Consolidation

`Core/NSPL/Entry` is the canonical direction for command surfaces.
`Core/NSPL/SkillCLI` and `Core/NSPL/GUICLI` remain compatibility shims.
Internal callers should migrate gradually toward Entry/Core-owned invocation
contracts rather than adding new architecture to compatibility packages.

## Filesystem Concurrency

NodeCTX provides durable and atomic file writes. Mutable read-modify-write
flows still need stronger lost-update and concurrent-writer discipline before
they can support broader multi-process or remote-control use confidently.

## Model And Backend Expansion

The current runtime is Ollama-first. Future model profiles should be
backend-aware and validate model inventory and required capabilities before
starting an agent workflow.

## Web Security

Web status and control surfaces are currently local/development oriented.
Remote exposure needs authentication, authorization and capability policy, and
safe network-binding defaults before it should be treated as a deployment
surface.

## Demo And Product Surface

The stale root `demo.py` ChatOps proof has been removed. Current demonstration
paths should focus on the Web Status app, RohTalk and AutoRoh workflows, and
DST Director through RohBridge.
