# Secure AI Coding Challenge

### From prompting to specifying: engineering secure changes to existing code with AI

<!--
REVIEWER NOTE: HTML comments marked VALIDATE are invisible on GitHub. They flag
commands, paths, or outputs that must be confirmed in a fresh Codespace before
this workbook is used live. See DESIGN-REVIEW.md, section E.
-->

You will complete three small missing blocks of real C code taken from open-source projects that once shipped a security vulnerability in exactly that place. Your AI assistant can write each block in seconds. This lab is about everything around those seconds: what you need to understand, write down, and check before the code deserves your trust.

**By the end you will be able to:**

1. Tell the difference between a *prompt* (a request for code) and a *specification* (a verifiable contract for a change).
2. Specify a change to existing code by separating what the code **already establishes**, what the change **must do**, and what it **must never allow**.
3. Use a lightweight threat model to discover requirements nobody wrote down.
4. Use GitHub Spec Kit to carry a specification through a minimal plan and an implementation, reviewing each AI artefact before relying on it.
5. Verify independently and read the results as **evidence, not proof**.

| | Exercise | Project | You will practise | Time |
|---|---|---|---|---|
| 1 | `1065` | file / libmagic | A prompt versus a specification | ~45 min |
| 2 | `910` | Little CMS | Threat modelling first; reviewing the plan | ~50 min |
| 3 | `9847` | file / libmagic | The full loop with less help; reusable guardrails | ~50 min |

Each exercise removes some of the scaffolding from the one before. By Exercise 3, you run the process yourself.

---

## 0. Before you begin

### 0.1 Check your environment

```bash
./workshop-ready
```

Continue when the final line reads:

```text
✓ Workshop environment ready
```

<!-- VALIDATE: public main's workshop-ready currently performs setup and prints
"✓ Workshop environment ready (Spec Kit 1.2.0)". DESIGN-REVIEW.md §E (P0-1)
proposes splitting setup from readiness. Update this line to match. -->

If a check fails, wait a minute for Codespace setup to finish and run it again. If the same check still fails, tell a facilitator which line failed.

### 0.2 Commands

```text
./workshop-ready      confirm the environment is usable
./exercise <id>       load an exercise into exercise.c
./function-test       does the code still behave as expected?
./function-debug      details for a functional failure
./security-test       is the known vulnerability still reproducible?
./security-debug      details for a security failure
```

Every test ends in one of three outcomes:

| Outcome | Meaning |
|---|---|
| `✅ PASS` | The tests that were run did not detect a problem. |
| `❌ FAIL` | The tests detected a problem in **your code**. |
| `⚠️ ERROR` | The platform could not produce a trustworthy result. This is **not** a verdict on your code. Run it again, then tell a facilitator. |

> [!WARNING]
> `./exercise <id>` overwrites `exercise.c`. Copy anything you want to keep before reloading.

### 0.3 Lab rules

These rules apply to you and to your AI agent.

1. **Change only the editable region.** Add code only between `/* ===== YOUR CODE STARTS HERE ===== */` and `/* ===== YOUR CODE ENDS HERE ===== */`.
2. **You run the tests, not the agent.** Never let the agent run `./function-test`, `./security-test`, or the debug commands.
3. **Approve terminal commands deliberately.** Spec Kit's agent skills run small helper scripts under `.specify/scripts/`. Approve those. Deny anything else, especially `docker`, `git`, network tools, and any command that touches the test harness.
4. **Engineer the answer, don't look it up.** Don't consult the upstream projects, their history, or the internet for the missing code.

<details>
<summary>Why these rules?</summary>

Rule 2 exists because whoever generates the code should not also be the one deciding whether it is correct. If an agent can run the security test in a loop, it can tweak code until the one known input stops crashing, which teaches you nothing and proves very little.

Rule 4 mirrors real work: when you change your own codebase, there is no upstream fix to copy. The skill you are building is deriving the right behaviour from the code and its threats.

Some of these rules are also enforced by the environment, but enforcement is defence in depth, not a guarantee. Treat the rules as yours.

</details>

### 0.4 Meet Spec Kit (3 minutes)

[GitHub Spec Kit](https://github.com/github/spec-kit) gives your AI agent a structured process: write a specification, plan against it, break it into tasks, implement, and check for gaps. It has already been set up in this repository with two workshop-specific adaptations:

| File | Purpose |
|---|---|
| `.specify/memory/constitution.md` | The project's principles. Every plan is checked against them. |
| `.specify/templates/overrides/` | A **brownfield** specification template designed for completing a gap inside existing code, rather than building a new product. |

1. Open `.specify/memory/constitution.md` and read it. It is short on purpose.
2. Open Copilot Chat, switch to **Agent** mode, and type `/speckit-`. You should see skills such as `speckit-specify` and `speckit-plan`.

<!-- VALIDATE: skills are listed when typing /speckit- in Copilot Chat Agent
mode in a fresh Codespace (Copilot default skills mode installs them under
.github/skills/speckit-*/SKILL.md). -->

<details>
<summary>The <code>/speckit-</code> skills don't appear</summary>

1. Make sure Copilot Chat is in **Agent** mode.
2. Check that `.github/skills/` contains folders named `speckit-*`.
3. Run **Developer: Reload Window** from the Command Palette.
4. If they're still missing, tell a facilitator. Do **not** run `specify init` yourself. It can overwrite the workshop's templates.

</details>

<details>
<summary>How the test platform works</summary>

The exercises come from **SecRepoBench**, a benchmark of secure code-completion tasks drawn from real open-source C/C++ projects. Each task masks a block of code at the exact location where a historical vulnerability was introduced.

Your code is evaluated in two independent ways inside Docker containers built from reproducible **ARVO** vulnerability environments:

- **Functionality:** the project's own developer-written tests check that your code still behaves correctly.
- **Security:** the proof-of-concept input that originally triggered the vulnerability (found by OSS-Fuzz) is replayed against a build containing your code.

`./security-test` does **not** run a new fuzzing campaign. It replays known inputs. A PASS means those inputs no longer trigger the known failure; it does not mean the code is free of vulnerabilities.

</details>

---

## Exercise 1: A prompt versus a specification

**Exercise:** `1065` · **Goal:** experience the difference between asking for code and specifying a change.

You will complete the same gap twice: once with a plain prompt, and once against a specification you have reviewed. Then you will compare both the code and the evidence.

<details>
<summary>Background: what program is this?</summary>

The open-source **file** command identifies file types by examining their contents. The same capability is available to other programs as the **libmagic** library. This exercise comes from `src/funcs.c`, which holds utility functions used across the project.

Upstream: <https://github.com/file/file>

</details>

### 1.1 Load and read

```bash
./exercise 1065
```

Open `exercise.c` and find the editable region. Don't edit anything yet.

Before you generate anything, make sure you can answer:

- Which function are we completing, and what inputs does it receive?
- What does the code **after** the gap expect to be true?

Use Copilot Chat in **Ask** mode to help you understand unfamiliar C or trace data flow. Don't ask it to write the missing code yet.

<details>
<summary>If this code feels hard to follow, you're not alone</summary>

The risk with AI-assisted coding isn't that AI code is unreadable. It's that **generation can move faster than comprehension**.

In a controlled ICER 2025 study, students working in an unfamiliar codebase with Copilot finished tasks about 35% faster and made 50% more progress, yet reported not understanding how or why the suggestions worked. A 2025 replication found participants passed more tests with Copilot but showed no greater understanding of the legacy code.

Passing tests isn't evidence that you understand the code. Build enough of a mental model to review what the AI produces.

- Shihab et al., ICER 2025: <https://icer2025.acm.org/details/icer-2025-papers/18/The-Effects-of-GitHub-Copilot-on-Computing-Students-Programming-Effectiveness-Effic>
- Qiao et al., 2025: <https://arxiv.org/abs/2511.02922>

</details>

### 1.2 Baseline: just prompt it

Switch Copilot Chat to **Agent** mode and paste:

```text
Complete the missing code in #file:exercise.c.

Add code only between:
/* ===== YOUR CODE STARTS HERE ===== */
and
/* ===== YOUR CODE ENDS HERE ===== */

Do not change anything outside those markers. Preserve the surrounding behaviour and function signatures. Do not run any commands.
```

Read the generated code. Then create a file called `notes.md` in the repository root and write one sentence:

```text
## 1065 baseline
I believe this code guarantees that: ...
```

Write it **before** you test. This is your prediction.

### 1.3 Test the baseline

```bash
./function-test
./security-test
```

Record both results under your prediction in `notes.md`. Then copy the baseline block (everything between the markers) into `notes.md`. You'll compare against it later.

<details>
<summary>The functional test failed</summary>

Run `./function-debug`, then ask the AI to fix only the specific compiler or functional error it reports. Keep the request narrow: don't let it rewrite the surrounding function. A functional PASS is enough to continue, but if you can't get one in about five minutes, record the FAIL and move on. The comparison still works.

</details>

<details>
<summary>Both tests passed</summary>

That's a legitimate outcome, and AI assistants vary. Keep going. The question for you is now: **do you know why it passed?** By the end of this exercise you'll be able to say whether the baseline meets requirements you can name, or passed for reasons you can't explain.

</details>

### 1.4 Reset the gap

```bash
./exercise 1065
```

This restores an empty editable region. You're starting the specification from the existing code, not from a prior AI attempt.

### 1.5 Draft a specification with Spec Kit

In Copilot Chat (**Agent** mode), paste:

```text
/speckit-specify Exercise 1065. Use the short name "ex1065". Specify the missing code between the YOUR CODE STARTS HERE and YOUR CODE ENDS HERE markers in #file:exercise.c as a bounded brownfield change, using the brownfield template. Complete the change boundary, observed context (cite line numbers), required behaviour, non-goals, and open questions. Leave sections 4 and 5 (threat model and security invariants) marked [TO BE COMPLETED BY ENGINEER]. Do not write or suggest code.
```

When the agent asks to run a script under `.specify/scripts/`, approve it. Spec Kit creates a feature folder, typically `specs/001-ex1065/`, containing `spec.md`. Open that file.

<!-- VALIDATE: (1) the short name controls the directory name; (2) the
speckit-specify skill honours the brownfield override template rather than
reverting to the default user-story structure; (3) #file: attachment works
alongside a skill invocation. -->

### 1.6 Review the specification

AI is good at code archaeology. You are accountable for whether it's true. Work through the checks below and edit `spec.md` directly.

| Check | Ask yourself |
|---|---|
| **Boundary** | Does it forbid changes outside the markers and to the function signature? |
| **Observations are facts** | Can you find each cited line? Does each observation describe what the code *does*, not what it *should* do? Mark an observation as verified only after you've checked it. |
| **Required is not observed** | Does each requirement describe something the gap must *add*, rather than something that already happens? |
| **No slogans** | Delete anything you couldn't test or review, such as "handle errors securely" or "follow best practices". |
| **Verifiable** | Does every acceptance criterion say how you would know it holds? |

Keep this table handy. You'll reuse it in every exercise.

### 1.7 Threat model, then write the security invariants

This section is yours. Use the code, your baseline results, and any `./security-debug` output. Answer in `spec.md` section 4:

- **What are we protecting?** What data or state does later code depend on? What goes wrong if it is invalid, stale, or undefined?
- **What can an attacker control?** Which inputs can the file being analysed influence? Can unusual input change whether an operation succeeds, fails, or returns partial results?
- **What must never happen?** What does downstream code assume? Is that assumption guaranteed on every path that reaches it?

Then turn each "must never happen" into a security invariant in section 5, using this shape:

```text
SR-1  If <attacker-influenced condition>, the editable region shall <safe outcome>
      and shall not <unsafe action>.
```

Add at least one **negative** acceptance criterion to section 6 for each invariant, and state how it is verified: `function-test`, `security-test`, `review`, or `not verified`.

<details>
<summary>Hint: focus your analysis</summary>

Look for a value or structure that one operation is expected to populate and another operation later consumes. Ask whether that state is well defined on **every** path that reaches the consumer.

</details>

<details>
<summary>What separates an invariant from a slogan?</summary>

An example from a different domain, a payment rate limiter:

| Slogan | Invariant |
|---|---|
| "Rate limiting must be secure." | "If a request repeats an idempotency key already seen for this user, the limiter shall process it without incrementing the user's count." |

An invariant names a specific condition, a specific outcome, and something observable you could check. A slogan names none of those.

</details>

### 1.8 Implement against the specification

Start a **new** chat in **Agent** mode (so the baseline conversation doesn't bias it). Replace `<your-feature>` with your folder name, then paste:

```text
Implement only the missing code between the markers in #file:exercise.c so that it satisfies every requirement in #file:specs/<your-feature>/spec.md.

Constraints:
- Change nothing outside the markers.
- Make the smallest change that satisfies the specification.
- Do not run commands, tests, or builds.

When finished, reply with a table mapping each FR and SR identifier to the line(s) that satisfy it. List any requirement you found ambiguous or could not satisfy.
```

Check the agent's mapping table against the code yourself. Is every SR really satisfied on every path?

### 1.9 Verify and compare

```bash
./function-test
./security-test
```

Record both results in the **Evidence log** at the bottom of `spec.md`.

Now compare the baseline block in `notes.md` with your new block. For each difference, find the requirement that explains it. **Any difference that no requirement explains is behaviour the AI chose for you.**

If a test fails, decide whether the code broke the spec or the spec missed something, and fix it at the source. Exercise 2 gives you a structured way to do this.

### 1.10 Debrief

1. Before testing the baseline, what did you believe it guaranteed? What was that belief based on?
2. Which line of your spec would most have changed the baseline, had the AI been given it?
3. Which acceptance criteria are not exercised by either test? How could you gain confidence in those?
4. In one sentence: how is your spec different from your baseline prompt?

**Carry forward:** in this exercise the threat model came after a first attempt. In Exercise 2 it comes first, before any code exists.

---

## Exercise 2: Threat model first; review the plan

**Exercise:** `910` · **Goal:** derive the security requirements before any code exists, and review the AI's plan before it writes anything.

There's no baseline this time. You'll also meet two new Spec Kit steps: **clarify** (resolve ambiguity in the spec) and **plan** (a design you must approve).

<details>
<summary>Background: what program is this?</summary>

**Little CMS** is an open-source colour-management engine written in C that converts colours between ICC profiles. ICC profiles are structured binary files that describe how a device or colour space reproduces colour. This exercise comes from `src/cmsio0.c`, which reads profile data.

Upstream: <https://www.littlecms.com/color-engine/>

</details>

### 2.1 Load and read

```bash
./exercise 910
```

Using **Ask** mode for help, make sure you can explain:

- what data is being read;
- which values describe a size, an offset, or a length;
- what happens immediately before and after the gap.

### 2.2 Threat model by hand

Spend five minutes on this **before** asking the AI. Add to `notes.md`:

```text
## 910 threat model
We are protecting: ...
An attacker can control: ...
It must never happen that: ...
```

Treat the ICC profile as untrusted. Which lengths, offsets, tags, or counts come from the file, and which of them reach the gap? Can the file be truncated, malformed, or inconsistent with itself?

<details>
<summary>Hint: focus your analysis</summary>

Look for arithmetic involving a size or length before memory is read or copied. Ask what happens when the untrusted value is smaller, larger, or otherwise inconsistent with what the code expects.

</details>

### 2.3 Get a second opinion

```text
/threat-model #file:exercise.c Focus on the editable region and the data that reaches it. Do not suggest code.
```

<!-- VALIDATE: .github/skills/threat-model/SKILL.md is present and slash-invocable. -->

Compare its answer with yours. What did it find that you missed? What did it claim that isn't actually true in this code? Update your notes, but only with what you have confirmed.

### 2.4 Specify, using your threat model

```text
/speckit-specify Exercise 910. Use the short name "ex910". Specify the missing code between the markers in #file:exercise.c as a bounded brownfield change, using the brownfield template. Cite line numbers for every observation. Use my threat model in #file:notes.md (section "910 threat model") to draft sections 4 and 5, with each security invariant in the form "If <attacker-influenced condition>, the editable region shall <safe outcome> and shall not <unsafe action>". Do not write or suggest code.
```

Review it with the table from step 1.6, plus one new check: **does every SR name a specific attacker-controlled value and a specific safe outcome?**

### 2.5 Clarify

```text
/speckit-clarify Focus on malformed, truncated, and boundary-sized input; what the function must return or leave unchanged on failure; and which existing behaviour must be preserved for valid input.
```

The agent asks up to five questions and writes your answers back into `spec.md`. Answer from the code, not from guesswork. If you don't know an answer, saying so is useful: record it as an open question.

### 2.6 Plan, then review the plan

```text
/speckit-plan This is a bounded brownfield change to one C function in #file:exercise.c. Use the minimal change plan template. Do not create research.md, data-model.md, contracts/, or quickstart.md. Add no new functions, headers, or dependencies, and change nothing outside the editable region. Enumerate every control-flow path through the editable region and map each FR and SR to the paths that satisfy it. Reuse the function's existing error-handling conventions and cite their lines.
```

<!-- VALIDATE: the plan skill honours the overridden plan template and does not
generate the default Phase 0/1 artefacts when told not to. -->

Open `plan.md`. **This is a review gate: nothing gets implemented until you approve it.**

1. Is any SR left without a path that satisfies it?
2. Does the plan touch anything outside the markers or introduce anything new?
3. Does its failure handling match how the surrounding function already fails? Check the cited lines.
4. Is there a path it doesn't list, such as empty, truncated, or exactly-at-the-limit input?

If anything is wrong, fix it **at the source**. Requirement problems go back into `spec.md`; design problems mean editing `plan.md` or re-running `/speckit-plan`. Don't plan to patch the code later instead.

### 2.7 Implement against the spec and plan

Start a new **Agent** chat:

```text
Implement only the missing code between the markers in #file:exercise.c, following #file:specs/<your-feature>/plan.md so that every requirement in #file:specs/<your-feature>/spec.md is satisfied.

Change nothing outside the markers. Do not run commands, tests, or builds.

When finished, map each FR and SR to the line(s) that satisfy it, and list anything in the plan you could not follow.
```

### 2.8 Verify, and triage any failure

```bash
./function-test
./security-test
```

Record the results in the Evidence log. If something failed, classify it before changing anything:

| What you see | Most likely cause | Fix it in |
|---|---|---|
| `⚠️ ERROR` | Platform problem; no verdict | Nothing. Re-run, then tell a facilitator |
| Function FAIL: doesn't compile | Implementation | The code |
| Function FAIL: wrong behaviour | The spec missed a behaviour to preserve, **or** the code deviated from it | Check the FRs, then fix the spec or the code |
| Security FAIL: code violates an SR | Implementation deviated from the spec | The code |
| Security FAIL: code satisfies every SR | **The spec is incomplete.** The threat model missed something | Threat model → spec → plan → code |

Use `./security-debug` to locate *where* things went wrong, not to copy a fix. Express what you learn as a requirement first, then regenerate.

### 2.9 Optional experiment: an agent will follow a flawed spec

If you finish early:

1. Copy your current implementation into `notes.md`.
2. Cut section 5 (security invariants) from `spec.md` and paste it into `notes.md`.
3. In a new chat, re-run the implementation prompt from 2.7.
4. Compare the result with your saved implementation. Did the agent add the protection anyway? If it did, would a reviewer be able to tell *why* that code is there?
5. Restore section 5 and your implementation.

### 2.10 Debrief

1. Which requirement came from *your* threat model rather than the AI's first draft, or the other way round?
2. What did you change in the plan before implementation, and what would have happened if you hadn't?
3. If a test failed, was it a spec gap or an implementation deviation? How did you tell?
4. Which invariant would transfer to a parser in your own work?

<details>
<summary>After you finish: how SecRepoBench classifies this exercise</summary>

SecRepoBench classifies exercise 910 as **CWE-122: Heap-based Buffer Overflow**. Did your threat model point at that class of failure before you saw this?

</details>

**Carry forward:** your requirements now live in a spec, not a prompt, but every principle still had to be restated each time. Exercise 3 makes the reusable parts part of the project.

---

## Exercise 3: Run the loop yourself; make it reusable

**Exercise:** `9847` · **Goal:** run the full specification-driven loop with minimal guidance, and decide which knowledge belongs in which layer of the project.

<details>
<summary>Background: what program is this?</summary>

This exercise returns to **file / libmagic**. `src/is_json.c` decides whether a file's contents are JSON (RFC 8259) by parsing untrusted bytes.

Upstream: <https://github.com/file/file>

</details>

### 3.1 Load, and tour the guardrails

```bash
./exercise 9847
```

This repository already contains several layers that shape how AI works here. Open each file briefly and decide: is it **advisory** (it shapes what the AI sees) or **enforced** (it constrains what can happen)?

| Layer | File | What it does | Advisory or enforced? |
|---|---|---|---|
| Constitution | `.specify/memory/constitution.md` | Principles every plan is checked against | ? |
| Specification | `specs/*/spec.md` | The contract for one change | ? |
| Path instructions | `.github/instructions/c-security.instructions.md` | Applied automatically when editing C files | ? |
| Skill | `.github/skills/threat-model/SKILL.md` | A repeatable procedure the AI can load | ? |
| Custom agent | `.github/agents/security-reviewer.agent.md` | A reviewer restricted to read and search tools | ? |
| Hook | `.github/hooks/workshop-guardrails.json` | Runs before each agent tool call; can deny it | ? |
| Tests | `./function-test`, `./security-test` | Independent evidence about the code | ? |

<!-- VALIDATE: each of these files is committed and present. Agent hooks are a
VS Code preview feature and may be disabled by policy. -->

<details>
<summary>Compare your answers</summary>

Only the custom agent's tool restriction and the hook **constrain** the AI. The constitution, spec, instructions, and skill are context: they make good behaviour more likely, and GitHub itself notes that Copilot may not follow custom instructions the same way every time. The tests are independent of the AI, which is what makes them evidence. They only cover what they exercise, though.

</details>

### 3.2 Run the loop

This time, you write the specification request. Use your experience from Exercises 1 and 2. Approve only `.specify/scripts/` commands throughout.

**Specify.** Complete the skeleton in your own words:

```text
/speckit-specify Exercise 9847. Use the short name "ex9847". Specify the missing code between the markers in #file:exercise.c as a bounded brownfield change. <Describe the boundary and what the gap must do.> Use this threat model for sections 4 and 5:
- We are protecting: ...
- An attacker can control: ...
- It must never happen that: ...
Do not write or suggest code.
```

<details>
<summary>Hint: focus your threat model</summary>

The bytes being inspected are untrusted. Focus on the relationship between the current read position and the end of valid input.

</details>

Review the spec with the table from step 1.6. Run `/speckit-clarify` if anything is ambiguous.

**Plan.** Write your own constraints, reusing what worked in 2.6, then review `plan.md` with the four plan-gate questions.

```text
/speckit-plan <your constraints>
```

**Tasks.** For a change this small, keep the task list tiny:

```text
/speckit-tasks At most five tasks. No setup, polish, or test-writing tasks. The final task is: stop and hand over to the engineer for independent verification.
```

**Analyse.** A read-only consistency check across spec, plan, and tasks:

```text
/speckit-analyze
```

If it reports a requirement with no task, or a task with no requirement, fix the artefact that owns the problem and run it again.

**Implement.**

```text
/speckit-implement
```

**Converge.** The agent checks its own implementation against the artefacts and appends any missing work to `tasks.md`:

```text
/speckit-converge
```

If it appends tasks, run `/speckit-implement` and `/speckit-converge` again. Converge is useful, but remember what it is: **the AI assessing its own work.**

### 3.3 Independent review

Select the **security-reviewer** agent in Copilot Chat's agent picker, then paste:

```text
Review the code between the markers in #file:exercise.c against the security invariants in #file:specs/<your-feature>/spec.md. For each SR, list every control-flow path through the editable region and state whether the invariant holds, citing lines. Do not suggest code.
```

### 3.4 Verify

```bash
./function-test
./security-test
```

Then fill in this comparison in `notes.md`:

| Source | Verdict | What it is based on |
|---|---|---|
| `/speckit-converge` | | |
| security-reviewer agent | | |
| `./function-test` + `./security-test` | | |
| **Your judgement** | | |

If they disagree, which do you trust and why? Use the triage table from 2.8 for any failure.

### 3.5 Test a guardrail

Ask the agent (in **Agent** mode, default agent):

```text
Run ./security-test and tell me the result.
```

If hooks are enabled, the tool call should be blocked by the workshop policy. If you're asked to approve it instead, **deny it**, and notice what that means: in your environment, this rule was advisory and you were the enforcement.

<details>
<summary>Security note: hooks are code too</summary>

Hooks run shell commands with the same permissions as VS Code. Review hook scripts before enabling them, keep them minimal, and don't store secrets in them. If an agent can edit its own hook configuration, the boundary is much weaker, so treat guardrail files as security-sensitive code.

</details>

### 3.6 Make the lesson reusable

Add one principle to the constitution: something you learned today that would apply to **any** change in this repository, not just this exercise.

```text
/speckit-constitution Add one principle: <your principle>. Keep all existing principles unchanged. Increment the version and record the amendment.
```

<!-- VALIDATE: speckit-constitution "keeps dependent templates in sync". Confirm
it does not rewrite .specify/templates/overrides/. If it does, instruct
participants to edit constitution.md directly instead. -->

Your principle must not mention exercise-specific names, variables, or code. A useful test: **would it have changed the baseline in Exercise 1 if it had been in place then?**

<details>
<summary>Too specific vs. reusable</summary>

| Too specific | Reusable |
|---|---|
| "Check the length variable in the JSON parser before indexing." | "Every specification for code that reads untrusted input must state, for each read, what bounds it and what happens when the bound is violated." |

</details>

### 3.7 Debrief

1. Which knowledge belonged in the **spec** (this change only), and which in the **constitution** or **instructions** (every change)?
2. Which rules did you want **enforced** rather than merely stated? Where would you enforce them in your own pipeline?
3. Where did the AI help most: understanding, specifying, planning, implementing, or reviewing? Where did it need you most?
4. What evidence would you require before approving an AI-generated change to a parser in your own codebase?

<details>
<summary>After you finish: how SecRepoBench classifies this exercise</summary>

SecRepoBench classifies exercise 9847 as **CWE-122: Heap-based Buffer Overflow**.

</details>

---

## Wrap-up: the brownfield secure change loop

You've used the same loop three times, with less help each time:

```text
 Bound ──► Observe ──► Threat model ──► Specify ──► Plan the minimum
                                           ▲                │
                                           │                ▼
                 Feed back  ◄──  Verify independently  ◄──  Generate + review
```

| Step | The question it answers |
|---|---|
| **Bound** | What exactly may change, and what must not? |
| **Observe** | What does the existing code already establish and expect? (Facts, with evidence.) |
| **Threat model** | What can an attacker control, and what must never happen? |
| **Specify** | What must the change do, what must it never allow, and how will we know? |
| **Plan the minimum** | Which paths exist, and does each requirement have one that satisfies it? |
| **Generate + review** | Does the code satisfy the spec, line by line, path by path? |
| **Verify independently** | What does evidence from outside the AI say? |
| **Feed back** | Was a failure a spec gap or an implementation deviation? Fix it at the source, and promote lasting lessons into the constitution. |

**Three things to take back to your own codebase:**

1. **A prompt asks for code. A specification is a contract you can check code against.** It's only as good as the understanding and threat model behind it.
2. **In existing code, most of the spec is already there.** Your job is to extract it honestly (observed), add what's missing (required), and state what must never happen (invariants).
3. **The generator is not the verifier.** AI self-checks, AI reviewers, and tests are different kinds of evidence. Passing tests means the tested cases didn't fail. Your judgement decides whether that's enough.

---

## Reference

<details>
<summary>Using a different AI assistant</summary>

Spec Kit's skills are configured for GitHub Copilot in this Codespace. The process transfers to any assistant:

1. Start a clean conversation and provide **only** `exercise.c`, `.specify/memory/constitution.md`, and the template in `.specify/templates/overrides/spec-template.md`.
2. Ask it to fill in the template for the editable region, leaving the threat model and invariants for you.
3. Review it with the table in step 1.6, write the invariants yourself, then ask for an implementation against the completed spec.
4. Paste only the code between the markers back into `exercise.c` and run the tests yourself.

In real projects, follow your organisation's rules before sending source code to an external AI service.

</details>

<details>
<summary>Troubleshooting</summary>

| Symptom | Try this |
|---|---|
| `specify: command not found` in a terminal | Open a **new** terminal. If it persists, tell a facilitator; you don't need the `specify` CLI for the exercises, only the chat skills. |
| Spec Kit creates a feature folder with an unexpected name | That's fine. Use whatever folder it created. |
| The agent edits code outside the markers | Reload the exercise (copy your code first), then repeat the prompt. Point out the boundary in the spec. |
| The agent tries to run tests, `docker`, or `git` | Deny it. Remind it of the constitution's verification principle. |
| `⚠️ ERROR` from a test | Re-run once. If it repeats, tell a facilitator. It's not a verdict on your code. |
| You lost your code by reloading an exercise | Check `notes.md` and your chat history. |

</details>

<details>
<summary>Further reading</summary>

- GitHub Spec Kit: <https://github.com/github/spec-kit>
- Adopting Spec Kit in an existing project: <https://github.github.io/spec-kit/guides/existing-projects.html>
- Easy Approach to Requirements Syntax (EARS), the "If …, the system shall …" pattern used for invariants: <https://alistairmavin.com/ears/>
- SecRepoBench: <https://huggingface.co/datasets/ai-sec-lab/SecRepoBench>
- GitHub Copilot customization reference: <https://docs.github.com/en/copilot/reference/customization-cheat-sheet>
- VS Code agent hooks: <https://code.visualstudio.com/docs/agent-customization/hooks>

</details>
