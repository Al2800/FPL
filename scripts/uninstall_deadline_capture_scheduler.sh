#!/usr/bin/env bash
# Remove portable deadline-capture scheduler registration without deleting evidence.
set -euo pipefail

METHOD="${1:-cron}"
UNIT_NAME="fpl-deadline-capture"
CRON_MARK="# FPL Deadline-Aware Capture"

case "${METHOD}" in
  cron)
    existing="$(crontab -l 2>/dev/null || true)"
    if ! printf '%s\n' "${existing}" | grep -q "${CRON_MARK}"; then
      echo "No FPL deadline-capture cron entry is registered."
      exit 0
    fi
    printf '%s\n' "${existing}" | grep -v "${CRON_MARK}" | crontab -
    echo "Removed FPL deadline-capture cron entry. No evidence artifacts or scheduler state were deleted."
    ;;
  systemd)
    UNIT_DIR="${HOME}/.config/systemd/user"
    if systemctl --user is-enabled "${UNIT_NAME}.timer" >/dev/null 2>&1 \
      || systemctl --user is-active "${UNIT_NAME}.timer" >/dev/null 2>&1; then
      systemctl --user disable --now "${UNIT_NAME}.timer" >/dev/null 2>&1 || true
    fi
    rm -f "${UNIT_DIR}/${UNIT_NAME}.service" "${UNIT_DIR}/${UNIT_NAME}.timer"
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    echo "Removed ${UNIT_NAME} systemd user units. No evidence artifacts or scheduler state were deleted."
    ;;
  *)
    echo "Usage: $0 [cron|systemd]" >&2
    exit 2
    ;;
esac
