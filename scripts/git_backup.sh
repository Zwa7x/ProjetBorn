#!/bin/bash
# scripts/git_backup.sh
set -e
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"
ts=$(date -u +"%Y%m%dT%H%M%SZ")
mkdir -p backups
cp data/app_data.db backups/app_data_${ts}.db
git add backups/app_data_${ts}.db
git commit -m "Backup DB ${ts}" || echo "No changes to commit"
git push origin main
