# Outstanding work migrated from Beads

These definitions capture the seven Beads that were still `open` or
`in_progress` when tracking moved to GitHub Issues.

Beads (`.beads/`) are retained only as historical archive. Do not claim, update
or close Beads for new work. Create and manage GitHub Issues instead.

## Create the issues

From a machine with `gh` authenticated as a repo collaborator (the cloud-agent
installation token cannot call `createIssue`):

```bash
python3 -m scripts.create_github_issues_from_defs
```

Or run the workflow **Create outstanding GitHub issues from defs** via
`workflow_dispatch`.

The creator is idempotent: it skips any open or closed issue whose title
already matches.
