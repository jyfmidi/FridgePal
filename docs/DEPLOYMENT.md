# Fridgital Docker Compose Deployment

This is the canonical operations runbook for deploying Fridgital on one self-managed Linux server. Commands assume a clean Git checkout and Docker Compose v2.

Fridgital has no application authentication. Do not expose it to the unrestricted public internet. Direct access through a server IP is supported only when the host or cloud firewall limits port `8080` to trusted source IP addresses.

## 1. Deployment Architecture

```text
trusted browser
    |
    | http://SERVER_IP:8080
    v
app container (FastAPI + built Vue client)
    |
    | private Compose network
    v
MySQL 8.4 container
    |
    v
fridgital-mysql-data named volume
```

Compose runs exactly one application replica. On every application start, Alembic upgrades the schema before Uvicorn starts. MySQL data survives container replacement in the named volume.

## 2. Server Requirements

Required software:

- a current Linux distribution;
- Git;
- Docker Engine with the Compose v2 plugin;
- outbound HTTPS access for Git, image pulls, npm, and Python packages during builds.

A practical starting allocation is 2 vCPU, 4 GB RAM, and at least 10 GB free disk plus room for database growth and backups. This is an operational starting point, not a measured capacity guarantee.

Verify the host before cloning the project:

```bash
git --version
docker --version
docker compose version
docker info
```

All four commands must succeed. Run Docker as a non-root operator who is authorized to control the daemon.

## 3. First Deployment

### 3.1 Obtain the repository

The operator must supply the real repository URL. An agent must not guess it.

```bash
git clone YOUR_REPOSITORY_URL Fridgital
cd Fridgital
```

Record the deployed revision:

```bash
git rev-parse --short HEAD
git status --short
```

The status output should be empty before deployment.

### 3.2 Create the environment file

```bash
cp .env.example .env
chmod 600 .env
openssl rand -hex 24
```

Copy the generated random value into `MYSQL_PASSWORD` in `.env`. Do not paste secrets into shell history, Git, issue trackers, chat, or deployment logs.

Review these settings:

| Variable | Production guidance |
|---|---|
| `COMPOSE_PROJECT_NAME` | Keep `fridgital` and never change it after data exists. |
| `APP_BIND_ADDRESS` | Use `127.0.0.1` for local/VPN proxying. Use `0.0.0.0` only for controlled IP access. |
| `APP_PORT` | Host port, default `8080`. |
| `MYSQL_DATABASE` | Keep `fridgital` unless intentionally migrating an existing installation. |
| `MYSQL_USER` | Dedicated application database user. Do not use `root`. |
| `MYSQL_PASSWORD` | Long, random, URL-safe secret. Required. |
| `RECIPE_PROVIDER_MODE` | Keep `fixture` for deterministic offline recipe data; use `live` only with approved provider credentials. |
| `MINIMAX_API_KEY` | Leave empty in fixture mode. Never expose it to the frontend. |
| `APP_TIMEZONE` | User-observable calendar timezone, for example `Asia/Shanghai`. |
| `APP_DEFAULT_LOCALE` | Initial locale, `en` or `zh-CN`. |
| `SEED_DEMO_DATA` | Keep `true` for the current MVP demo inventory; set `false` for an empty installation. |

For direct server-IP access, set:

```dotenv
APP_BIND_ADDRESS=0.0.0.0
APP_PORT=8080
```

This only publishes the port. It does not add authentication or encryption.

### 3.3 Restrict network access

Before starting with `APP_BIND_ADDRESS=0.0.0.0`, add a host or cloud firewall rule that permits TCP port `8080` only from the user's trusted public IP or private network.

Example for UFW; replace `TRUSTED_CLIENT_IP` before running it:

```bash
sudo ufw allow from TRUSTED_CLIENT_IP to any port 8080 proto tcp
sudo ufw status numbered
```

Do not add a global `8080/tcp ALLOW Anywhere` rule. If the client IP changes frequently, use a private VPN such as Tailscale/WireGuard or keep the loopback binding and add a protected reverse proxy later.

### 3.4 Validate and start

```bash
docker compose config --quiet
docker compose build --pull app
docker compose up -d
docker compose ps
```

Expected state:

- `db` becomes `healthy`;
- `app` becomes `healthy` after migrations and startup;
- no host port is published for MySQL;
- only the configured application address and port are published.

Inspect startup if either service is not healthy:

```bash
docker compose logs --tail=200 db
docker compose logs --tail=200 app
```

### 3.5 Verify the application

From the server:

```bash
curl -fsS "http://127.0.0.1:${APP_PORT:-8080}/api/health"
```

From the trusted client, open:

```text
http://SERVER_IP:8080
```

Then verify Storage loads and refresh one nested route such as `/rescue`. A successful deployment serves both the client and `/api` from the same origin.

## 4. Routine Operations

### Status and health

```bash
docker compose ps
docker compose top
curl -fsS "http://127.0.0.1:${APP_PORT:-8080}/api/health"
```

### Logs

```bash
docker compose logs --tail=100 app db
docker compose logs -f --tail=100 app
```

Do not publish logs without reviewing them for food names, source URLs, operation identifiers, and environment-specific details.

### Restart

```bash
docker compose restart app
docker compose ps
```

Restarting or recreating the application container does not remove MySQL data.

### Stop and start

```bash
docker compose stop
docker compose start
```

## 5. Upgrade Procedure

Run upgrades from the repository root. Do not upgrade without a current database backup.

```bash
git status --short
git rev-parse --short HEAD
```

The status output must be empty. Create a backup using Section 6, then fetch and review the intended revision before switching to it.

```bash
git fetch --all --prune
git log --oneline --decorate -10
git pull --ff-only
docker compose config --quiet
docker compose pull db
docker compose build --pull app
docker compose up -d --remove-orphans
docker compose ps
curl -fsS "http://127.0.0.1:${APP_PORT:-8080}/api/health"
```

`app` runs pending Alembic migrations before accepting traffic. Do not scale `app` beyond one replica with the current startup-migration design.

## 6. Database Backup

Backups are SQL dumps stored outside the Docker volume. Protect them like production data.

```bash
mkdir -p backups
chmod 700 backups
backup_path="backups/fridgital-$(date -u +%Y%m%dT%H%M%SZ).sql"
docker compose exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" exec mysqldump --single-transaction --no-tablespaces --routines --triggers -u "$MYSQL_USER" "$MYSQL_DATABASE"' > "$backup_path"
test -s "$backup_path"
ls -lh "$backup_path"
```

Copy backups to a second machine or protected object store. A backup that only exists on the application server is not sufficient disaster recovery.

Periodically test restoration on a disposable Fridgital deployment. A dump that has never been restored is not a verified backup.

## 7. Database Restore

Restore overwrites or merges data in the selected database. Confirm the target server, project directory, Compose project name, and backup file before continuing. Stop the application to prevent concurrent writes.

```bash
docker compose stop app
docker compose ps
```

Replace `BACKUP_FILE.sql` with the exact reviewed path:

```bash
docker compose exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql -u "$MYSQL_USER" "$MYSQL_DATABASE"' < BACKUP_FILE.sql
docker compose start app
docker compose ps
curl -fsS "http://127.0.0.1:${APP_PORT:-8080}/api/health"
```

Restore a backup with the application revision that created it when schema compatibility is uncertain. Keep the original dump until the UI and representative inventory values are verified.

## 8. Rollback

Application rollback is safe only when the old application understands the current database schema. Alembic migrations may not be backward compatible.

Before rollback:

1. record the current commit;
2. create a database backup;
3. identify the exact known-good commit or tag;
4. decide whether the matching pre-upgrade database backup must also be restored.

After explicit operator approval, switch to the reviewed revision and rebuild:

```bash
git checkout KNOWN_GOOD_COMMIT
docker compose build app
docker compose up -d --remove-orphans
docker compose ps
```

Do not automatically run an Alembic downgrade. Restore the matching database backup when rollback requires the older schema.

## 9. Data Volume and Removal

The persistent volume name is:

```text
fridgital-mysql-data
```

Verify it with:

```bash
docker volume inspect fridgital-mysql-data
```

Normal shutdown retains data:

```bash
docker compose down
```

The following command permanently removes the database volume and all Fridgital data on this server:

```text
docker compose down --volumes
```

Do not run it during normal maintenance. An agent must obtain explicit user authorization immediately before any volume deletion.

## 10. Troubleshooting

### Compose reports a missing MySQL password

Confirm `.env` exists in the repository root and contains a non-empty `MYSQL_PASSWORD`:

```bash
test -f .env
docker compose config --quiet
```

Do not print the whole `.env` file into logs or chat.

### Database never becomes healthy

```bash
docker compose ps
docker compose logs --tail=200 db
docker volume inspect fridgital-mysql-data
```

Common causes are insufficient disk space, an incompatible existing volume, or changed database credentials after initialization. MySQL does not replace an existing volume's users merely because `.env` changed.

### Application exits during startup

```bash
docker compose logs --tail=200 app
docker compose run --rm app alembic current
```

Look for database connectivity, migration, dependency, or environment interpolation errors. Do not bypass migrations to force the server online.

### Server health works but a client cannot connect

```bash
docker compose port app 8000
ss -lnt | grep ':8080'
```

Confirm `APP_BIND_ADDRESS=0.0.0.0`, the configured `APP_PORT`, the host firewall, the cloud firewall/security group, and the client's source IP.

### Frontend loads but API calls fail

```bash
curl -i "http://127.0.0.1:${APP_PORT:-8080}/api/health"
docker compose logs --tail=200 app
```

The production frontend and API are same-origin. Do not configure a separate frontend API URL for the Compose deployment.

## 11. Agent Execution Checklist

An automation agent deploying Fridgital must:

1. confirm it is operating in the intended repository and server;
2. inspect Git status and stop if unreviewed local changes exist;
3. verify Docker and Compose are available;
4. confirm `.env` exists without printing secrets;
5. confirm `COMPOSE_PROJECT_NAME=fridgital` remains stable;
6. confirm the network exposure choice with the operator;
7. run `docker compose config --quiet`;
8. create and verify a database backup before upgrades or rollback;
9. build and start with the documented commands;
10. wait for both services to become healthy;
11. verify `/api/health` and one browser workflow;
12. report the deployed Git commit, published address, service health, and any skipped checks;
13. never delete a volume, restore a database, alter firewall policy, or expose the port globally without explicit user authorization.
