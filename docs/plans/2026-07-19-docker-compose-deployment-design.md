# Docker Compose Deployment Documentation Design

**Status:** Approved on 2026-07-19
**Requirements:** `FR-DEP-001`, `FR-DEP-002`, `NFR-REL-002`, `AC-DEP-01`

## Goal

Make a fresh Linux server deployment understandable and repeatable for both a human operator and an autonomous coding agent, using Docker Compose as the only production deployment path.

## Deployment Boundary

Fridgital remains one private, single-user deployment composed of:

- one `app` container that serves the built Vue client and FastAPI API;
- one MySQL 8.4 container;
- one named Docker volume that holds MySQL data.

The application has no authentication. The safe default is loopback-only binding. Direct access by server IP is supported only when the operator explicitly binds to `0.0.0.0` and restricts port `8080` to trusted source addresses with the server or cloud firewall.

No reverse proxy, certificate service, domain, Vercel configuration, or public-account system is added in this slice.

## Configuration Design

- `compose.yaml` owns service topology, health checks, restart behavior, the named volume, and configurable host binding.
- `.env.example` documents every deployment variable without containing a real secret.
- `.dockerignore` keeps local virtual environments, dependencies, build output, Git data, secrets, and caches out of the Docker build context.
- `Dockerfile` remains a multi-stage frontend/backend build and runs the final application as a non-root user.

The application port is controlled by `APP_BIND_ADDRESS` and `APP_PORT`. The Compose project name is stable so the database volume name remains predictable across upgrades.

## Documentation Design

`docs/DEPLOYMENT.md` is the canonical runbook. It is written in imperative English with explicit working directories, commands, expected results, safety warnings, and recovery paths. It covers:

1. server prerequisites and network assumptions;
2. first deployment from a clean checkout;
3. private-IP access and firewall requirements;
4. health, status, and log inspection;
5. normal upgrades;
6. database backup and restore;
7. application rollback and database compatibility warnings;
8. shutdown/removal semantics;
9. troubleshooting and an agent execution checklist.

The root `README.md` becomes the project entry point rather than a stale pre-implementation brief. It explains the implemented architecture, repository structure, local development, verification commands, and links to the deployment runbook.

## Verification Design

The deployment slice uses the smallest relevant checks:

- `docker compose config --quiet` for configuration interpolation;
- a clean Docker image build when Docker is available;
- Compose health and persistence smoke checks when a local Docker daemon is available;
- existing backend tests and frontend lint/type/build checks for regression protection;
- `git diff --check` and a documentation residue scan.

If the host does not provide Docker, the missing daemon is reported explicitly rather than treating an unrun smoke test as passing.
