---
name: upload
description: Project packaging and upload: package the repository as a zip when the task ends, with a truthful, verifiable delivery report (project architecture, tasks completed, features implemented, tool call count, elapsed time). Use when the user asks to package a project, upload deliverables, or generate a delivery report.
disable-model-invocation: true
---

# Project Packaging and Upload

Package the project repository when the task ends, producing a deliverable, verifiable zip archive.

## Quick Start

1. Confirm the task has ended and the repository is in a deliverable state
2. Package the repository as a zip (exclude non-deliverable content such as dependencies and caches: node_modules, __pycache__, .venv)
3. Include the delivery report inside the archive, and inform the user when packaging is done

## Workflow

### 1. Package the Code

- Package the repository as a zip when the first task ends
- The archive must contain the delivery report

### 2. Delivery Report Requirements

The delivery report must include:

- Project architecture
- Which tasks were completed
- What features were implemented
- Tool call count
- Elapsed time

**Truthfulness requirement**: the information above must be guaranteed truthful. If an item cannot be guaranteed truthful, leave it blank rather than fabricate it. When producing the final output, inform the user of this (state which items were omitted and why).

### 3. Initial Prompt

Attach the initial prompt of the task (the user's original task description, verbatim) to the delivery report, as the baseline for comparing delivery scope.

### 4. Confirm Scoring Dimensions and Criteria

After packaging, confirm with the user the scoring dimensions and criteria to be used for the subsequent evaluation; only proceed to the project review workflow (see the `zc-review` skill) after confirmation.

## Notes

- Data in the delivery report (tool call count, elapsed time) must come from actual session/log records, never estimates or fabrication
- Before packaging, confirm no keys, credentials, or other sensitive files are included in the archive
