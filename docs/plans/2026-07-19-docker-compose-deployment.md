# Docker Compose Deployment Documentation Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Fridgital deployable and operable on a fresh private Linux server through documented Docker Compose commands.

**Architecture:** Keep the existing two-service Compose topology: one multi-stage application image and one MySQL 8.4 service backed by a named volume. Add safe configurable host binding, production-oriented container defaults, and one canonical operations runbook without introducing a reverse proxy or authentication system.

**Tech Stack:** Docker Engine, Docker Compose v2, MySQL 8.4, Python 3.12/FastAPI, Node 22/Vue 3/Vite.

---

### Task 1: Harden the Docker build context and runtime

**Files:**

- Create: `.dockerignore`
- Modify: `Dockerfile`

**Steps:**

1. Exclude Git metadata, `.env`, local databases, virtual environments, dependency directories, build output, test caches, and editor files from the build context.
2. Keep the existing frontend build and Python runtime stages.
3. Add an unprivileged runtime user and run the application under that user.
4. Build the image and expect a successful frontend build and Python package installation.

### Task 2: Make Compose safe and server-configurable

**Files:**

- Modify: `compose.yaml`
- Modify: `.env.example`

**Steps:**

1. Add `restart: unless-stopped` and `init: true` to long-running services where applicable.
2. Bind the application with `${APP_BIND_ADDRESS:-127.0.0.1}:${APP_PORT:-8080}:8000`.
3. Give the MySQL volume a deterministic project-scoped name.
4. Add health-check start periods and keep the application dependent on healthy MySQL.
5. Document safe defaults and the explicit `0.0.0.0` opt-in required for direct server-IP access.
6. Run `docker compose config --quiet` and expect exit code 0 with a populated `.env`.

### Task 3: Write the deployment runbook

**Files:**

- Create: `docs/DEPLOYMENT.md`

**Steps:**

1. Document prerequisites, recommended server baseline, repository checkout, and environment creation.
2. Document first start, status, health, IP access, and firewall restrictions.
3. Document logs, restart, provider configuration, and routine upgrade commands.
4. Document timestamped MySQL backup and controlled restore commands.
5. Document rollback limitations, data-volume ownership, safe shutdown, and destructive removal warnings.
6. Add common failure symptoms with exact diagnostic commands.
7. Add an execution checklist that an agent can follow without inferring missing steps.

### Task 4: Rewrite the project README

**Files:**

- Modify: `README.md`

**Steps:**

1. Replace the stale implementation status with the current MVP state.
2. Retain the product loop and canonical-document authority order.
3. Add an accurate repository tree and component responsibilities.
4. Keep concise local backend/frontend development and verification commands.
5. Make Docker Compose the primary deployment link and summarize the no-auth boundary.

### Task 5: Verify the release documentation

**Files:**

- Modify if needed: `docs/IMPLEMENTATION_PLAN.md`

**Steps:**

1. Run Compose configuration validation.
2. Build and start the stack when Docker is available.
3. Verify `/api/health`, service health, and data persistence across an application restart.
4. Run backend tests, Ruff, and mypy.
5. Run frontend ESLint, vue-tsc, and the Vite production build.
6. Run `git diff --check` and scan for stale statements such as “implementation has not started.”
7. Record any environment-limited check explicitly.
