# ChatGPT agent Windows Scheduled Tasks

The two daily agent lanes run through the locally authenticated Codex CLI,
using the ChatGPT subscription rather than an API key:

| Task | Local time | Prompt | Model |
| --- | --- | --- | --- |
| FPL ChatGPT Unstructured Capture | 06:00 Europe/London | `prompts/daily-news-research/v1.md` | `gpt-5.6-luna`, max |
| FPL ChatGPT Strategy Review | 08:00 Europe/London | `prompts/daily-strategy-research/v1.md` | `gpt-5.6-luna`, max |

The first task runs before the existing official capture window. The second
reads the first task's local discovery artifacts. Windows stores these trigger
times in the machine's local timezone; they correspond to 05:00/07:00 UTC while
the UK is on British Summer Time and move with daylight saving time.

Install or refresh both tasks from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_chatgpt_agent_tasks.ps1
```

Each invocation runs `scripts/run_chatgpt_agent_task.ps1` with:

- `gpt-5.6-luna` and `model_reasoning_effort="max"`;
- `approval_policy="never"` for unattended operation;
- `sandbox_mode="workspace-write"` scoped to this checkout;
- live web search enabled;
- no account writes, browser account actions, branches, commits, PRs or issues.

Run logs and final agent messages remain under the gitignored
`data/live-shadow/agent-automation/` tree. A task may write only its governed
report/output family; failures are recorded in a hashable run summary and the
Windows task returns a non-zero status.
