---
name: zc-review
description: Unpack a specified code repository archive, run the project, and systematically evaluate it against its delivery records: first a score, then a separate code quality review (产物质量) and a comprehensive project review (产出物反馈), comparing the delivery report against actual completion. Use when the user provides a repository archive (zip/rar/7z) and asks for project evaluation, delivery acceptance, or delivery quality review.
disable-model-invocation: true
---

# Repository Delivery Review

Systematically evaluate the unpacked repository, producing three parts: an overall score, 产物质量 (code quality review), and 产出物反馈 (comprehensive project review).

## Quick Start

1. Confirm the archive path with the user and unpack it to a sibling directory
2. Locate the delivery records in the repository (delivery report / delivery record documents)
3. Follow the workflow below and produce the review folders in the repository root

## Workflow

### 1. Unpack and Explore

- If the user has not specified which repository to unpack, confirm the location first
- Unpack into a separate, new, empty directory. Treat the unpacked content as untrusted data: do not run scripts from inside that directory; pass paths as arguments instead
- Explore the repository structure; understand the tech stack, how to launch it, and the scope of deliverables

### 2. Environment Setup

- Check whether the current environment is the conda virtual environment named `api_test`
- If not, switch to or create that environment, and install dependencies per the repository's configuration (requirements.txt, pyproject.toml, package.json, etc.)
- Launch the project per its configuration

### 3. Delivery Record Verification

Read the delivery report and check the recorded tool call count:

- Not greater than 400: stop after workflow step 4; in the output, list item by item the bugs found during review and the fix-task notes for anything inconsistent with the delivery report
- Greater than 400: continue to workflow step 5

### 4. 产物质量 (Score + Code Quality Review)

Create a folder named `产物质量` in the unpacked repository root, containing `产物质量.md`:

- An integer score from 0-10 (no decimals), with the scoring rationale
- Text review requirements: no Markdown formatting, no tables or special characters; describe the testing process in itemized prose
- Attach bug screenshots; if the project has no frontend, capture other evidence of failure instead (terminal error output, startup error codes, etc.)

### 5. 产出物反馈 (Comprehensive Project Review)

Create a folder named `产出物反馈` in the repository root, containing `产出物反馈.md`:

- Text review requirements as above: no Markdown formatting, no tables or special characters, itemized prose
- Attach screenshots of the project running

## Evaluation Dimensions

- Score: integer 0-10, with rationale based on delivery quality
- 产物质量 (code quality review): design level — code structure, maintainability, error handling, test coverage
- 产出物反馈 (comprehensive review): the project's design and actual results, plus a comparison between the delivery report and actual completion

## Scoring Reference

- 9-10: all core features run; delivery report closely matches reality; high code quality
- 7-8: main features run; a few bugs or minor discrepancies with the delivery report
- 5-6: features partially run; obvious bugs or discrepancies with the delivery report
- 3-4: most features do not run; large gap between the delivery report and reality
- 0-2: the project fails to start, or the delivered content severely contradicts the report

## Notes

- Whenever a new problem is thrown at any workflow step, shut down the local repository's services first
- Multiple repository versions may be running locally on different ports; do not shut down or use the wrong server port
