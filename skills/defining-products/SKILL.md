---
name: defining-products
description: Use when rough ideas, scattered decisions, notes, or incomplete requirements leave product definition, product boundaries, usage, form, value propositions, constraints, or conflicts unclear.
---

# Defining Products

Create the smallest definition complete for its decision or handoff. Questions close gaps, not quotas.

## Quick Start

- “Define from these notes.” Inspect, clarify blockers, return Markdown.
- “Output now.” Return **Draft**; list assumptions, missing information, and decisions.
- “Save to `docs/product.md`.” Save only there after target checks.

## Frame and Classify

Establish intended decision/handoff, lifecycle stage, audience, and detail as needed; judge completeness accordingly.

Classify statements as **Supported claim** (evidence and provenance), **Decision** (authorized choice), **Assumption** (provisional; validate), or **Open question** (missing choice/evidence). Never promote inference, examples, or convention to a decision or import unrelated workspace context.

## Analyze Gaps

Check relevant dimensions adaptively: users/roles/buyer/decision-maker; problem/context/outcome/value propositions; usage/form/capabilities/primary flow; boundaries/non-goals/dependencies/constraints/exceptions; conflicts/assumptions/open decisions/validation.

These are diagnostic prompts, not mandatory headings. Permit reasoned **N/A**. Never use a fixed questionnaire/outline. Add relevant domain checks: child safety, AI failures, hardware environment, regulated boundaries, enterprise roles.

Do not ask questions answered by current authoritative sources; verify uncertain freshness or authority. Rank gaps by decision impact, uncertainty, then reach. Ask the smallest useful set, highest first, while material gaps remain.

## Resolve Conflicts

Show conflicting claims, sources, consequences. Without delegation, ask the user to choose, establish authority, or defer; never silently resolve. With explicit delegation, recommend/select and record rationale plus **Decision** status. Delegation covers only the specified decision, not unrelated decisions. Keep other proposals labeled **Assumptions/recommendations**; material ones block **Final** until confirmed or separately delegated. Apply corrections; reclassify and revisit dependencies.

## Gate Final

A blocker is an unresolved item that may materially change user, value, form, core flow, scope, feasibility, safety/compliance, or handoff decision.

Final covers every relevant dimension above. Record reasoned **N/A** only when omission could look like a gap. Low-impact uncertainty may remain only with an owner and validation action. Never call output **Final** with blockers. Early output is **Draft** and lists assumptions, missing information, and required decisions.

## Generate and Deliver

Generate only useful Markdown sections. Follow user language, audience, and detail. Separate supported claims, decisions, assumptions, and open questions.

Default to in-chat Markdown. Create/save only for a requested file operation and target. Use forward slashes. Existing targets require explicit overwrite approval; an explicit update/replace request counts. Backup does not.

## Common Mistakes

- Freezing plausible details under urgency.
- Blocking final on customer/monetization gaps that cannot materially change direction.
- Inventing architecture, schedules, non-goals, or workspace facts.
- Saving chat-only output or treating backup as overwrite approval.

## Software Example

Input: “AI incident summaries for enterprises; notes conflict on automatic publishing.”

Treat audience/AI as supported claims and as Decisions only when chosen by an authorized source. Surface the conflict; ask who approves and what failure behavior is required because roles/flow change. Draft until blockers resolve; cover enterprise roles, flow, AI-failure boundaries, dependencies, validation, and non-goals. Invent neither pricing nor deployment.
