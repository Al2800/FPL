#!/usr/bin/env bash
# Portable installer for the deadline-aware capture dispatcher (ticket 04).
# Reuses scripts/run_deadline_capture_dispatch.py unchanged. Does not store secrets.
set -euo pipefail

METHOD="${1:-cron}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="${PYTHON_PATH:-${REPO_ROOT}/.venv/bin/python}"
DISPATCHER="${REPO_ROOT}/scripts/run_deadline_capture_dispatch.py"
TASK_LAUNCHER="${REPO_ROOT}/scripts/run_deadline_capture_task.sh"
CONFIG="${REPO_ROOT}/config/data_sources/2026-27-capture-scheduler.json"
FIXTURE="${REPO_ROOT}/tests/fixtures/fpl-bootstrap-scheduler.json"
UNIT_NAME="fpl-deadline-capture"
CRON_MARK="# FPL Deadline-Aware Capture"

if [[ ! -x "${PYTHON_PATH}" && ! -f "${PYTHON_PATH}" ]]; then
  echo "Python interpreter missing: ${PYTHON_PATH}" >&2
  exit 1
fi
for path in "${DISPATCHER}" "${CONFIG}" "${FIXTURE}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Required scheduler path is missing: ${path}" >&2
    exit 1
  fi
done

# Installation must remain offline: prove planner wiring against a static fixture first.
"${PYTHON_PATH}" "${DISPATCHER}" \
  --config "${CONFIG}" \
  --dry-run \
  --bootstrap-fixture "${FIXTURE}" \
  --now '2026-08-20T17:30:00Z' >/dev/null

mkdir -p "${REPO_ROOT}/scripts"
cat > "${TASK_LAUNCHER}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
ROOT="${REPO_ROOT}"
PYTHON="${PYTHON_PATH}"
exec "\${PYTHON}" "\${ROOT}/scripts/run_deadline_capture_dispatch.py" \\
  --config "\${ROOT}/config/data_sources/2026-27-capture-scheduler.json" \\
  --python "\${PYTHON}"
EOF
chmod +x "${TASK_LAUNCHER}"

case "${METHOD}" in
  cron)
    existing="$(crontab -l 2>/dev/null || true)"
    filtered="$(printf '%s\n' "${existing}" | grep -v "${CRON_MARK}" || true)"
    {
      printf '%s\n' "${filtered}"
      echo "*/15 * * * * ${TASK_LAUNCHER} ${CRON_MARK}"
    } | crontab -
    echo "Installed cron entry for ${UNIT_NAME}. Evidence and scheduler state were not modified."
    ;;
  systemd)
    UNIT_DIR="${HOME}/.config/systemd/user"
    mkdir -p "${UNIT_DIR}"
    cat > "${UNIT_DIR}/${UNIT_NAME}.service" <<EOF
[Unit]
Description=FPL Deadline-Aware Capture dispatcher
After=default.target

[Service]
Type=oneshot
ExecStart=${TASK_LAUNCHER}
WorkingDirectory=${REPO_ROOT}
EOF
    cat > "${UNIT_DIR}/${UNIT_NAME}.timer" <<EOF
[Unit]
Description=FPL Deadline-Aware Capture every 15 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
Persistent=true
Unit=${UNIT_NAME}.service

[Install]
WantedBy=timers.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now "${UNIT_NAME}.timer"
    echo "Installed systemd user timer ${UNIT_NAME}.timer. Evidence and scheduler state were not modified."
    ;;
  *)
    echo "Usage: $0 [cron|systemd]" >&2
    exit 2
    ;;
esac
