# Secure Vibe Coding Workshop

## Participant Workbook

### How this platform works

This workshop is built on **SecRepoBench**, a benchmark of real secure code-completion tasks from open-source C/C++ projects.

SecRepoBench evaluates generated code in two separate ways:

- **Functionality** — developer-written unit tests check whether the code still behaves correctly.
- **Security** — vulnerabilities originally discovered through **OSS-Fuzz** are reproduced with their proof-of-concept inputs.

SecRepoBench describes this directly:

> “The generated code is compiled with the full repository and evaluated on two dimensions: correctness using developer-written unit tests and security using Proof-of-Concept exploits from OSS-Fuzz.”

The workshop runs those builds and tests inside **Docker containers** based on reproducible ARVO vulnerability environments. ARVO describes its dataset as providing vulnerabilities in a form that can be:

> “consistently rebuilt, triggered, and analyzed across versions.”

A useful distinction: the workshop does **not** run a full fuzzing campaign every time you press `./security-test`. OSS-Fuzz already found the original vulnerability. The security test rebuilds your code and replays the known adversarial input to see whether the vulnerability can still be triggered.

## Before you begin

While the Codespace prepares, follow the facilitator's opening briefing or read **How this platform works** above.

Before starting Exercise 1, confirm that the Python environment, Docker runtime, test harness, and all three workshop images are ready:

```bash
./workshop-ready
```

Continue when you see:

```text
✓ Workshop environment ready
```

If a check fails, wait for Codespaces setup to finish and run the command again. If it still fails, use the failed check to troubleshoot before starting the exercises.

### Commands

```bash
./workshop-ready      # confirm the environment is ready
./exercise <id>       # load an exercise
./function-test       # test expected behaviour
./function-debug      # investigate a functional failure
./security-test       # test the security property
./security-debug      # investigate a security failure
```

> **Task:** only add a code snippet between:

```c
/* ===== YOUR CODE STARTS HERE ===== */

/* ===== YOUR CODE ENDS HERE ===== */
```

The goal is to have AI complete a function or part of the codebase—not rewrite everything.

---

# Exercise 1 — Does working code mean secure code?

**Exercise:** `1065`

**Goal:** establish a baseline for AI-generated code.

You will ask AI to complete a missing block of real open-source C code. First make it work. Then test security separately.

<details>
<summary><strong>Background — what program are we working on?</strong></summary>

This exercise comes from the open-source **file / libmagic** project.

The `file` command identifies file types. Its upstream README describes it as the standard Unix `file(1)` implementation and says:

> “It knows the 'magic number' of several thousands of file types.”

The project also exposes the same capability as the `libmagic` library so other applications can identify file types programmatically.

The code in this exercise comes from `src/funcs.c`, which contains utility functions used by the project.

**Upstream:** https://github.com/file/file

</details>

## 1. Load the exercise

```bash
./exercise 1065
```

Open:

```text
exercise.c
```

Read the function containing:

```c
/* ===== YOUR CODE STARTS HERE ===== */

/* ===== YOUR CODE ENDS HERE ===== */
```

Do not edit anything yet.

### Checkpoint — understand before you generate

Before prompting AI to write code, can you explain:

- What function are we completing?
- What inputs does it receive?
- What output or state does the surrounding code expect?

You do **not** need to understand the entire project. You may use AI to explain the existing code, trace the data flow, or clarify unfamiliar C. Do not ask it to write the missing implementation yet.

<details>
<summary><strong>If this code feels hard to follow, you are probably not alone</strong></summary>

The risk with AI-assisted coding is not that AI-generated code is inherently unreadable. It is that **generation can move faster than comprehension**.

A controlled ICER 2025 study of 10 undergraduate computer science students working in an unfamiliar codebase found that Copilot users completed tasks **34.9% faster** and made **50% more solution progress**. Yet the researchers also reported:

> “students reported concerns about not understanding how or why Copilot suggestions work”

A follow-up study found a similar performance–comprehension gap:

> “participants passed more test cases with Copilot, but did not demonstrate greater understanding of the legacy codebase.”

**Takeaway:** passing tests is not evidence that you understand the generated code. Use AI to help explain unfamiliar code, but build enough of your own mental model to review what the model generates.

Research:

- Shihab et al., *The Effects of GitHub Copilot on Computing Students' Programming Effectiveness, Efficiency, and Processes in Brownfield Coding Tasks*, ICER 2025: https://icer2025.acm.org/details/icer-2025-papers/18/The-Effects-of-GitHub-Copilot-on-Computing-Students-Programming-Effectiveness-Effic
- Qiao et al., *Comprehension-Performance Gap in GenAI-Assisted Brownfield Programming: A Replication and Extension*, 2025: https://arxiv.org/abs/2511.02922

</details>

---

## 2. Ask AI to complete the code

Use GitHub Copilot or another AI assistant.

For this first attempt, **do not give it security requirements**.

Use:

> Complete the missing code in `exercise.c`.
>
> Add code only between:
>
> `/* ===== YOUR CODE STARTS HERE ===== */`
>
> and
>
> `/* ===== YOUR CODE ENDS HERE ===== */`
>
> Do not change anything outside those markers. Preserve the surrounding behaviour and function signatures.

### Using another AI

You may use ChatGPT, Claude, Gemini, or another assistant.

1. Download or copy `exercise.c`.
2. Start a clean conversation.
3. Upload **only `exercise.c`**.
4. Use the prompt above.
5. Paste only the generated implementation back between the markers.

> In real projects, follow your organisation's rules before sending source code or data to an external AI service.

---

## 3. Test functionality

```bash
./function-test
```

### If it passes

Continue to **Step 4**.

### If it fails

Run:

```bash
./function-debug
```

Use the diagnostic output to revise the implementation.

Repeat until:

```text
FUNCTIONAL TEST: PASS
```

<details>
<summary><strong>Stuck?</strong></summary>

Keep the task narrow.

Ask the AI to fix the specific compiler or functional error shown by `./function-debug`.

Do not ask it to rewrite the surrounding function.

</details>

---

## 4. Test security

A functional PASS answers only the first question.

Now test the same implementation against the known security case:

```bash
./security-test
```

Record the result before changing anything.

If it fails:

```bash
./security-debug
```

### Checkpoint

You now have two independent results:

| Question | Result |
|---|---|
| Does the code work? | Functional test |
| Does it preserve the security property? | Security test |

Do not jump directly to a patch.

---

## 5. Threat model the missing code

Use the code and diagnostic information you already have.

You may use your AI assistant to help **understand** the code at this stage. Ask it to explain data flow, state, control flow, or unfamiliar C constructs. Use that analysis to answer the questions below before asking for a fix.

Answer these three questions.

### What are we protecting?

Identify the property that must remain trustworthy.

Ask:

- What data or state does later code depend on?
- What would go wrong if that state were invalid, stale, or undefined?

Write:

> **We are protecting:** ______________________________________

### What can an attacker control?

Identify the trust boundary.

Ask:

- Which inputs can ultimately be influenced by the file or data being analysed?
- Can unusual input change whether an operation succeeds, fails, or returns partial information?
- Which control-flow paths depend on that input?

Write:

> **An attacker can control:** _________________________________

### What must never happen?

Do not write code yet.

State the invariant.

Ask:

- What does downstream code assume has already happened?
- Is that assumption guaranteed on every relevant path?
- What must be true before downstream code uses the result?

Write:

> **It must never happen that:** ______________________________

<details>
<summary><strong>Hint — focus your analysis</strong></summary>

Look for a value or structure that one operation is expected to populate and another operation later consumes.

Ask whether that state is guaranteed to be well-defined on every path that reaches the consumer.

</details>

---

## 6. Turn the threat model into a requirement

Write **one clear security requirement**.

A good requirement describes the property the code must preserve, not the exact C statement you want AI to write.

Use this structure if useful:

> Before __________________ is used, the implementation must guarantee __________________ on every relevant control-flow path.

Your requirement:

> _____________________________________________________________

---

## 7. Give the requirement to AI

Now start a **new AI conversation** if practical.

Provide `exercise.c` and your security requirement.

Use:

> Complete only the editable region in `exercise.c`.
>
> Preserve the existing behaviour and surrounding code.
>
> Security requirement:
>
> **[paste your requirement]**
>
> Make the smallest change that satisfies both the functional behaviour and this requirement.

Paste the implementation back into `exercise.c`.

---

## 8. Verify both properties

Run:

```bash
./function-test
./security-test
```

Your target is:

```text
FUNCTIONAL TEST: PASS
SECURITY TEST: PASS
```

If either fails, use the matching debug command. If the security test fails, revise the **security requirement**—not only the code—then ask AI to generate another snippet. Repeat until both tests pass.

---

## 9. Debrief

Before moving on, answer:

1. Did the first AI-generated implementation pass the functional test?
2. Did it pass the security test?
3. What security assumption was missing from the original prompt?
4. Did the explicit requirement change the generated code?
5. Which result gave you stronger evidence: the AI's explanation or the tests?

### Carry forward

Exercise 1 introduced the loop:

```text
Generate → Functional test → Security test → Threat model → Requirement → Retest
```

**Exercise 2 will move the threat model earlier — before we depend on a security test to tell us what we forgot.**

---

# Exercise 2 — Define security before coding

**Exercise:** `910`

**Goal:** identify the security requirement before AI writes the code.

In Exercise 1, the security test exposed an assumption after generation. This time, find the assumption first.

<details>
<summary><strong>Background — what program are we working on?</strong></summary>

This exercise comes from **Little CMS**, an open-source colour management engine written in C.

Little CMS says it:

> “implements fast transforms between ICC profiles.”

ICC profiles are structured binary files used to describe colour behaviour across devices and colour spaces. This exercise is in `src/cmsio0.c`, code that reads profile information.

SecRepoBench classifies this exercise as **CWE-122: Heap-based Buffer Overflow**.

**Upstream:** https://www.littlecms.com/color-engine/

**SecRepoBench:** https://huggingface.co/datasets/ai-sec-lab/SecRepoBench

</details>

## 1. Load the exercise

```bash
./exercise 910
```

Open `exercise.c`.

Read the missing region and enough surrounding code to understand it. You may use AI to help explain the code, trace data flow, or identify unfamiliar C constructs.

Make sure you can explain:

- what data is being read;
- which values describe size, offset, or length;
- what happens before and after the missing region.

Use AI for **understanding**, not generation, at this stage. Do not ask it to write the missing code yet.

---

## 2. Threat model first

Answer the same three questions from Exercise 1.

### What are we protecting?

Ask:

- What memory or parser state must remain valid?
- What would happen if a malformed profile changed a size or offset assumption?

Write:

> **We are protecting:** ______________________________________

### What can an attacker control?

Treat the ICC profile as untrusted input.

Ask:

- Which lengths, offsets, tags, or types originate from the profile?
- Which of those values reach the missing code?
- Can the file be truncated, malformed, or internally inconsistent?

Write:

> **An attacker can control:** _________________________________

### What must never happen?

Ask:

- Which memory operation depends on attacker-influenced values?
- What must be true before that operation is safe?
- What should happen when the input violates that assumption?

Write:

> **It must never happen that:** ______________________________

<details>
<summary><strong>Hint — focus your analysis</strong></summary>

Look for arithmetic involving a size or length before memory is read or copied.

Ask what happens when the untrusted value is smaller, larger, or otherwise inconsistent with what the code expects.

</details>

---

## 3. Write the security requirements

Turn the threat model into **two or three requirements**.

Keep them implementation-independent.

Example structure:

> Before using an attacker-controlled size or offset, the code must validate that the operation remains within the available data.

Write your requirements:

> **1.** ______________________________________________________
> **2.** ______________________________________________________
> **3.** ______________________________________________________

---

## 4. Give the requirements to AI

Use Copilot or another AI assistant.

Start a clean conversation if practical.

Prompt:

> Complete only the editable region in `exercise.c`.
>
> Preserve the surrounding behaviour and function signatures.
>
> Security requirements:
>
> 1. [requirement]
> 2. [requirement]
> 3. [requirement]
>
> Make the smallest change that satisfies the functional behaviour and these requirements.

Paste only the implementation between the markers.

---

## 5. Test functionality

```bash
./function-test
```

If it fails:

```bash
./function-debug
```

Fix the functional issue without weakening the requirements.

---

## 6. Test security

```bash
./security-test
```

If it fails:

```bash
./security-debug
```

Do not immediately patch the failing line.

Return to the threat model and ask:

- Which assumption did we miss?
- Was a requirement too vague?
- Does the requirement cover every relevant control-flow path?

Revise the requirement, then ask AI to revise the implementation.

Retest:

```bash
./function-test
./security-test
```

Target:

```text
FUNCTIONAL TEST: PASS
SECURITY TEST: PASS
```

---

## 7. Debrief

1. What security property did you identify before generation?
2. Did the requirements change the implementation AI produced?
3. Did the security test reveal an assumption the threat model missed?
4. Which requirement would be useful again in another parser?

### Carry forward

The requirements helped, but they still lived in a prompt.

**Exercise 3 moves reusable security knowledge into the development environment so the next AI interaction can inherit it.**

---

# Exercise 3 — Make the environment carry security

**Exercise:** `9847`

**Goal:** move from one-off security prompts to reusable Copilot guidance and enforceable agent guardrails.

<details>
<summary><strong>Background — what program are we working on?</strong></summary>

This exercise returns to **file / libmagic**.

The project README describes `src/is_json.c` as the component that:

> “knows about JavaScript Object Notation format (RFC 8259).”

The code parses untrusted file contents to decide whether data is JSON. SecRepoBench classifies this exercise as **CWE-122: Heap-based Buffer Overflow**.

**Upstream:** https://github.com/file/file

**SecRepoBench:** https://huggingface.co/datasets/ai-sec-lab/SecRepoBench

</details>

## 1. Load the exercise

```bash
./exercise 9847
```

Open `exercise.c`.

Do not ask AI to complete it yet.

---

## 2. Threat model the parser

Keep this short.

### What are we protecting?

> **We are protecting:** ______________________________________

### What can an attacker control?

The bytes being inspected are untrusted.

> **An attacker can control:** _________________________________

### What must never happen?

Focus on the relationship between the current read position and the end of valid input.

> **It must never happen that:** ______________________________

Write one or two security requirements from those answers.

> **1.** ______________________________________________________
> **2.** ______________________________________________________

---

## 3. Add repository-wide Copilot instructions

Create:

```text
.github/copilot-instructions.md
```

GitHub describes repository custom instructions as guidance that applies to requests made in the context of the repository.

Add a small set of reusable rules. For example:

```markdown
# Secure coding requirements

- Treat external file and network data as untrusted.
- Identify the trust boundary before changing parser or memory-handling code.
- Validate attacker-influenced sizes, offsets, indexes, counts, and parser state before memory access or arithmetic.
- Preserve defined state on success and failure paths.
- Fail safely on malformed or truncated input.
- Never weaken tests or security checks to obtain a passing result.
```

Do not put the answer to any workshop exercise in this file.

GitHub notes:

> “Copilot may not always follow your custom instructions in exactly the same way every time they are used.”

Instructions improve context. They are not an enforcement boundary.

---

## 4. Add C-specific instructions

Create:

```text
.github/instructions/c-security.instructions.md
```

Add:

```markdown
---
applyTo: "**/*.{c,h}"
---

# C security checks

Before editing C code that processes untrusted input:

- identify the valid start and end of each buffer;
- validate before dereference, indexing, copying, or size arithmetic;
- consider empty, truncated, malformed, and boundary-sized inputs;
- keep every observable value initialized on every relevant path;
- preserve existing validation and error handling.
```

Repository-wide instructions carry broad expectations. Path-specific instructions add rules only where they apply.

---

## 5. Generate the code with the environment in place

Open a fresh Copilot Chat session.

Use a short prompt:

> Complete only the editable region in `exercise.c`. Follow the repository instructions. Preserve the surrounding behaviour.

Before accepting the code, ask:

> What trust boundary and security invariant did you apply?

Then paste or accept only the missing code.

---

## 6. Verify

```bash
./function-test
./security-test
```

If either fails, use:

```bash
./function-debug
./security-debug
```

Update the requirement or implementation and retest.

---

## 7. Package threat modelling as a reusable skill

Repository instructions are best for short rules that apply broadly.

A **skill** is useful for a repeatable workflow that Copilot should load when relevant.

Create:

```text
.github/skills/threat-model/SKILL.md
```

Add:

```markdown
---
name: threat-model
description: Derive security requirements before changing code that crosses a trust boundary.
---

When code processes external or attacker-controlled input:

1. State what we are protecting.
2. State what an attacker can control.
3. State what must never happen.
4. Identify assumptions that depend on attacker-controlled state.
5. Turn material assumptions into explicit security requirements.
6. Identify how each requirement will be verified.
7. Only then propose a code change.
```

GitHub describes agent skills as:

> “folders of instructions, scripts, and resources that Copilot can load when relevant.”

Now ask Copilot:

> Threat model `exercise.c` before reviewing the implementation.

Compare its output with your own threat model.

---

## 8. Add a read-only security reviewer

Create:

```text
.github/agents/security-reviewer.agent.md
```

Add:

```markdown
---
name: security-reviewer
description: Review code against trust boundaries and explicit security requirements.
tools: ["read", "search"]
---

Review the code in scope.

1. Identify the trust boundary.
2. Identify attacker-controlled state.
3. State the security invariant.
4. Check whether every relevant path preserves it.
5. Identify unsafe assumptions.
6. Recommend verification steps.

Do not edit files or execute commands.
```

GitHub's custom-agent reference says:

> “The `tools` list filters the set of tools that are made available to the agent.”

The reviewer can inspect and search, but it cannot edit code or execute shell commands.

Use the custom agent to review `exercise.c`.

Then run the real tests yourself.

---

## 9. Add an agent hook

> **VS Code Agent Hooks are currently Preview.** They may also be disabled by organisation policy.

Instructions ask the model to behave a certain way. A `PreToolUse` hook can make a decision **before** a tool runs.

Create:

```text
.github/hooks/security.json
```

Add:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": ".github/hooks/block-dangerous.sh",
        "timeoutSec": 5
      }
    ]
  }
}
```

Create:

```text
.github/hooks/block-dangerous.sh
```

Add:

```bash
#!/bin/bash
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input')
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // empty')

if [ "$TOOL_NAME" = "runTerminalCommand" ] &&
   echo "$COMMAND" | grep -qE '(WORKSHOP_BLOCK_ME|rm[[:space:]]+-rf|git[[:space:]]+push)'; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"Blocked by workshop security policy"}}'
  exit 0
fi

echo '{"continue":true}'
```

Make it executable:

```bash
chmod +x .github/hooks/block-dangerous.sh
```

VS Code says a `PreToolUse` hook can:

> “Block dangerous operations, require approval, modify tool input”

### Test the hook safely

Ask Copilot Agent mode to run:

```bash
echo WORKSHOP_BLOCK_ME
```

The hook should deny the tool call.

Do **not** test the guardrail with an actually destructive command.

<details>
<summary><strong>Security note — hooks are code too</strong></summary>

VS Code warns:

> “Hooks execute shell commands with the same permissions as VS Code.”

Review hook scripts before enabling them. Keep them least-privileged, validate their input, and do not store secrets in them.

If the agent can edit its own hook scripts, that also weakens the boundary. Treat guardrail configuration as security-sensitive code.

</details>

---

## 10. Final verification

Return to the actual coding task.

Run:

```bash
./function-test
./security-test
```

Then ask the security-reviewer agent to review the final implementation.

Compare three forms of evidence:

| Layer | What it gives you |
|---|---|
| Instructions / skill | Better security context |
| Restricted agent / hook | Reduced agent capability or blocked actions |
| Functional + security tests | Evidence about the generated code |

---

## 11. Debrief

1. Which security knowledge belonged in the immediate prompt?
2. Which rules were reusable enough for repository instructions?
3. Which workflow was better represented as a skill?
4. Which actions should be restricted rather than merely discouraged?
5. Which security properties still require deterministic tests?

### Final takeaway

AI guidance and agent guardrails can improve the development environment.

They do not replace verification.

Keep the loop:

```text
Threat model → Requirements → AI context → Guardrails → Functional test → Security test
```

---

<details>
<summary><strong>Codespaces / VS Code Copilot capabilities used in this workbook</strong></summary>

| Capability | Repository location | VS Code support |
|---|---|---|
| Repository instructions | `.github/copilot-instructions.md` | Supported |
| Path-specific instructions | `.github/instructions/*.instructions.md` | Supported |
| Agent skills | `.github/skills/<name>/SKILL.md` | Supported |
| Custom agents | `.github/agents/*.agent.md` | Supported |
| Agent hooks | `.github/hooks/*.json` | Preview |

Current GitHub documentation also lists prompt files and MCP servers as supported in VS Code. They are not required for these three exercises.

**Documentation checked:** 2026-09-04.

References:

- https://docs.github.com/en/copilot/reference/customization-cheat-sheet
- https://docs.github.com/en/copilot/reference/custom-instructions-support
- https://docs.github.com/en/copilot/concepts/prompting/response-customization
- https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- https://docs.github.com/en/copilot/reference/custom-agents-configuration
- https://code.visualstudio.com/docs/agent-customization/hooks

</details>
