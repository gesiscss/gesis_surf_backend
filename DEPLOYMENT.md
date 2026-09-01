# Deployment Guide

This guide describes how to deploy the GESIS Surf backend on a single AWS EC2 instance using Docker Compose, PostgreSQL on EBS, Nginx, and Let's Encrypt HTTPS.

## Target Setup

- AWS EC2 Ubuntu instance, for example `t3.large`
- 100 GB EBS `gp3` volume, encrypted
- Elastic IP attached to the EC2 instance
- Route53 domain or subdomain pointing to the Elastic IP
- Docker Compose stack:
  - Django API/uWSGI
  - PostgreSQL
  - Redis
  - Celery worker
  - Elasticsearch
  - Logstash
  - Nginx proxy
  - Certbot

## AWS Prerequisites

### EC2 Security Group

Allow only these inbound rules:

```text
22    SSH    your public IP only, e.g. 92.209.184.166/32
80    HTTP   0.0.0.0/0
443   HTTPS  0.0.0.0/0
```

Do not expose these publicly:

```text
5432  PostgreSQL
5555  Flower
5601  Kibana
9200  Elasticsearch
5044  Logstash
9600  Logstash monitoring
```

### Elastic IP

Attach an Elastic IP to the EC2 instance. Use this IP for DNS records so the browser extension endpoint does not change after EC2 stop/start.

### DNS

In Route53, create an `A` record:

```text
surfcollect-gr.net -> EC2 Elastic IP
```

For a test subdomain, use:

```text
test.surfcollect-gr.net -> EC2 Elastic IP
```

The value used in `.env` must match the DNS name that users and the extension will call.

## Server Preparation

SSH into EC2 and update the server:

```bash
sudo apt update
sudo apt upgrade -y
```

Install Git:

```bash
sudo apt install -y git
```

Install Docker and the Docker Compose plugin:

```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Allow the current user to run Docker:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker --version
docker compose version
git --version
```

Optional server firewall:

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
sudo ufw status
```

Install unattended security updates:

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

## Application Deployment

Clone the backend repository:

```bash
git clone YOUR_REPO_URL
cd gesis_surf_backend
```

Create the production environment file:

```bash
nano .env
```

Example:

```env
DB_NAME=gesis_surf
DB_USER=gesis_user
DB_PASSWORD=replace-with-a-strong-password
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=0
DOMAIN=surfcollect-gr.net
ACME_DEFAULT_EMAIL=admin@example.com
MAINTENANCE_MODE=0
```

Generate a Django secret key if needed:

```bash
openssl rand -base64 48
```

Protect the `.env` file:

```bash
chmod 600 .env
```

Validate the Compose config:

```bash
docker compose -f docker-compose.deploy.yaml config
```

Start database and support services:

```bash
docker compose -f docker-compose.deploy.yaml up -d db redis elasticsearch logstash
```

Run database migrations as a one-off command:

```bash
docker compose -f docker-compose.deploy.yaml run --rm app python manage.py migrate
```

Seed selector configuration for the extension:

```bash
docker compose -f docker-compose.deploy.yaml run --rm app python manage.py seed_selector_configs --force
```

Start the backend, Celery worker, and proxy:

```bash
docker compose -f docker-compose.deploy.yaml up -d app celery_worker_1 proxy
```

## HTTPS Setup

Before requesting the certificate, confirm:

- `DOMAIN` in `.env` is correct
- DNS points to the EC2 Elastic IP
- EC2 security group allows inbound port `80`
- EC2 security group allows inbound port `443`
- The `proxy` container is running

Request the first Let's Encrypt certificate:

```bash
docker compose -f docker-compose.deploy.yaml run --rm certbot /opt/certify-init.sh
```

Restart the proxy so it loads the new certificate:

```bash
docker compose -f docker-compose.deploy.yaml restart proxy
```

Check services:

```bash
docker compose -f docker-compose.deploy.yaml ps
docker compose -f docker-compose.deploy.yaml logs -f app
```

Test in a browser:

```text
https://surfcollect-gr.net/api/docs/
https://surfcollect-gr.net/api/schema/
https://surfcollect-gr.net/admin/
```

The root URL `/` may not show an application page. Use the API docs, schema, or admin URLs for health checks.

## Changing Domain

If changing from a test subdomain to the root domain:

1. Update Route53:

   ```text
   surfcollect-gr.net -> EC2 Elastic IP
   ```

2. Update `.env`:

   ```env
   DOMAIN=surfcollect-gr.net
   ```

3. Recreate containers that depend on the domain:

   ```bash
   docker compose -f docker-compose.deploy.yaml up -d --force-recreate app celery_worker_1 proxy
   ```

4. Request a certificate for the new domain:

   ```bash
   docker compose -f docker-compose.deploy.yaml run --rm certbot /opt/certify-init.sh
   docker compose -f docker-compose.deploy.yaml restart proxy
   ```

## Routine Deployments

After the first deployment, use this manual flow:

```bash
cd gesis_surf_backend
git pull
docker compose -f docker-compose.deploy.yaml build app celery_worker_1
docker compose -f docker-compose.deploy.yaml run --rm app python manage.py migrate
docker compose -f docker-compose.deploy.yaml run --rm app python manage.py seed_selector_configs --force
docker compose -f docker-compose.deploy.yaml up -d app celery_worker_1 proxy
docker compose -f docker-compose.deploy.yaml ps
docker compose -f docker-compose.deploy.yaml logs -f app
```

If static files or proxy config changed, restart the proxy:

```bash
docker compose -f docker-compose.deploy.yaml restart proxy
```

## Useful Commands

View running services:

```bash
docker compose -f docker-compose.deploy.yaml ps
```

View API logs:

```bash
docker compose -f docker-compose.deploy.yaml logs -f app
```

View proxy logs:

```bash
docker compose -f docker-compose.deploy.yaml logs -f proxy
```

View database logs:

```bash
docker compose -f docker-compose.deploy.yaml logs -f db
```

Restart the app:

```bash
docker compose -f docker-compose.deploy.yaml restart app
```

Open a shell in the app container:

```bash
docker compose -f docker-compose.deploy.yaml run --rm app sh
```

Run Django management commands:

```bash
docker compose -f docker-compose.deploy.yaml run --rm app python manage.py createsuperuser
docker compose -f docker-compose.deploy.yaml run --rm app python manage.py check --deploy
```

## Monitoring Tools

Flower is optional and is behind the `monitoring` Compose profile. It is bound to localhost only:

```bash
docker compose -f docker-compose.deploy.yaml --profile monitoring up -d flower
```

Do not expose Flower publicly. If remote access is needed, use SSH tunneling:

```bash
ssh -L 5555:127.0.0.1:5555 ubuntu@YOUR_EC2_IP
```

Then open:

```text
http://127.0.0.1:5555
```

Kibana is defined in Compose but not published to the internet. Keep it internal unless you add authentication and strict network controls.

## Backups

EBS is persistent storage, but it is not a backup. Before collecting real production data, add at least one of:

- EBS snapshots
- `pg_dump` backups uploaded to S3

Example local database dump:

```bash
mkdir -p backups
docker compose -f docker-compose.deploy.yaml exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "backups/gesis_surf_$(date +%Y%m%d_%H%M%S).sql.gz"
```

For S3 backups, attach an EC2 instance role with permission to write to one backup bucket, then upload the dump with the AWS CLI. This does not require app code changes.

### S3 Upload Setup

The S3 bucket used for Greek deployment dumps is:

```text
gesis-surf-greek-dumps
```

Install the AWS CLI on EC2 if it is not already installed:

```bash
sudo apt update
sudo apt install -y awscli
aws --version
```

The EC2 instance should use an IAM instance role with write access to this bucket. Avoid storing long-lived AWS access keys on the server.

Minimum S3 permissions for the EC2 instance role:

```text
s3:ListBucket on arn:aws:s3:::gesis-surf-greek-dumps
s3:GetObject on arn:aws:s3:::gesis-surf-greek-dumps/*
s3:PutObject on arn:aws:s3:::gesis-surf-greek-dumps/*
```

Add these values to `.env`:

```env
S3_BUCKET=gesis-surf-greek-dumps
S3_PREFIX=
AWS_REGION=eu-central-1
```

Test full DB backup generation:

```bash
chmod +x scripts/export-full-backup.sh
./scripts/export-full-backup.sh
```

Test S3 sync:

```bash
chmod +x scripts/sync-dumps-to-s3.sh
./scripts/sync-dumps-to-s3.sh
```

The S3 layout is:

```text
s3://gesis-surf-greek-dumps/data-dumps/
s3://gesis-surf-greek-dumps/backups/
```

## Analyst Access And Data Dumps

### Recommended Access Model

Keep PostgreSQL private. Do not open port `5432` in the EC2 security group.

Use one of these controlled access paths:

- Daily table dumps copied to the GESIS analysis server
- SSH tunnel for temporary read-only database access
- SFTP/SCP access to a dump directory on EC2

AWS IAM users do not create Linux users inside the EC2 server and do not create PostgreSQL users. There are three separate user layers:

```text
AWS IAM user       -> AWS console/API permissions
Linux server user  -> SSH/SFTP access to EC2
PostgreSQL user    -> database permissions
```

For analysts, prefer data dumps. For people who need live queries, create read-only PostgreSQL users and require SSH tunneling.

### Create Linux Users For Dump Access

Create one Linux user per person who needs server file access:

```bash
sudo adduser analyst1
sudo adduser analyst2
sudo usermod -aG docker analyst1
sudo usermod -aG docker analyst2
```

Only add users to the `docker` group if they must run Docker commands. Docker group access is powerful and effectively gives root-level control on the server. For dump download only, do not add them to the Docker group.

Create a shared dump directory:

```bash
sudo mkdir -p /srv/gesis-surf/dumps
sudo groupadd gesis-analysts
sudo usermod -aG gesis-analysts analyst1
sudo usermod -aG gesis-analysts analyst2
sudo chgrp -R gesis-analysts /srv/gesis-surf/dumps
sudo chmod 2770 /srv/gesis-surf/dumps
```

### Create Read-Only PostgreSQL Users

Run this from the project directory on EC2:

```bash
docker compose -f docker-compose.deploy.yaml exec db psql -U "$DB_USER" -d "$DB_NAME"
```

Then create a read-only role:

```sql
CREATE ROLE readonly;
GRANT CONNECT ON DATABASE gesis_surf TO readonly;
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;
```

Create one database user per analyst:

```sql
CREATE USER analyst1 WITH PASSWORD 'replace-with-strong-password';
CREATE USER analyst2 WITH PASSWORD 'replace-with-strong-password';
GRANT readonly TO analyst1;
GRANT readonly TO analyst2;
```

If the database name is not `gesis_surf`, replace it in the SQL above.

### Query Through SSH Tunnel

Keep PostgreSQL private and tunnel it through SSH:

```bash
ssh -L 15432:127.0.0.1:15432 ubuntu@YOUR_EC2_IP
```

The current Compose file does not publish PostgreSQL to localhost. If live read-only querying is required, add a localhost-only PostgreSQL port mapping:

```yaml
db:
  ports:
    - "127.0.0.1:15432:5432"
```

Then recreate the database container:

```bash
docker compose -f docker-compose.deploy.yaml up -d db
```

Analysts can connect locally through the tunnel:

```bash
psql -h 127.0.0.1 -p 15432 -U analyst1 -d gesis_surf
```

### Daily Table Dumps

This repo includes a helper script:

```bash
scripts/export-data-dump.sh
```

By default it exports these application tables:

```text
core_user
core_globalsession
core_window
core_tab
core_tab_domains
core_domain
core_click
core_scroll
```

Run it from the project directory:

```bash
chmod +x scripts/export-data-dump.sh
./scripts/export-data-dump.sh
```

The script writes a PostgreSQL custom-format dump into:

```text
data-dumps/
```

To export specific tables:

```bash
./scripts/export-data-dump.sh core_domain core_click core_scroll
```

To write dumps into a shared directory:

```bash
OUTPUT_DIR=/srv/gesis-surf/dumps ./scripts/export-data-dump.sh
```

Restore or inspect the dump on another PostgreSQL server:

```bash
pg_restore --list gesis_surf_tables_YYYYMMDD_HHMMSS.dump
pg_restore -d target_database gesis_surf_tables_YYYYMMDD_HHMMSS.dump
```

### Automate Dumps And S3 Uploads

Add a cron job on EC2:

```bash
crontab -e
```

Example analytics export every 12 hours:

```cron
0 */12 * * * cd /home/ubuntu/gesis_surf_backend && ./scripts/export-data-dump.sh >> /home/ubuntu/gesis_surf_backend/data-dumps/dump.log 2>&1
```

Example full recovery backup once per day at 02:30:

```cron
30 2 * * * cd /home/ubuntu/gesis_surf_backend && ./scripts/export-full-backup.sh >> /home/ubuntu/gesis_surf_backend/backups/backup.log 2>&1
```

Example S3 sync after each analytics dump:

```cron
15 */12 * * * cd /home/ubuntu/gesis_surf_backend && ./scripts/sync-dumps-to-s3.sh >> /home/ubuntu/gesis_surf_backend/data-dumps/s3-sync.log 2>&1
```

Example S3 sync after the daily full backup:

```cron
45 2 * * * cd /home/ubuntu/gesis_surf_backend && ./scripts/sync-dumps-to-s3.sh >> /home/ubuntu/gesis_surf_backend/backups/s3-sync.log 2>&1
```

The sync script uploads both local folders:

```text
data-dumps/ -> s3://gesis-surf-greek-dumps/data-dumps/
backups/    -> s3://gesis-surf-greek-dumps/backups/
```

It uses `aws s3 sync`, so already uploaded files are not uploaded again unless changed.

Delete local dump and backup files older than 7 days:

```cron
0 3 * * * find /home/ubuntu/gesis_surf_backend/data-dumps -type f -name "*.dump" -mtime +7 -delete
5 3 * * * find /home/ubuntu/gesis_surf_backend/backups -type f -name "*.dump" -mtime +7 -delete
```

This cleanup only deletes local EC2/EBS files. Configure an S3 Lifecycle rule on the bucket if S3 objects should also expire automatically.

### Existing Production Pattern

An existing production command may look like:

```bash
sudo docker exec -e PGPASSWORD='...' "$(sudo docker ps -qf name=surf_pgbouncer)" ...
```

That pattern means production is likely querying through a `surf_pgbouncer` container instead of directly through the Postgres container. This repository's current EC2 deployment does not include PgBouncer. If daily live queries become frequent, add PgBouncer later and expose it only through localhost plus SSH tunnel, not publicly.

## Data Reset Before Production

If testers used the production URL and the database must be cleared before real production, take a backup first:

```bash
docker compose -f docker-compose.deploy.yaml exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "pre_reset_$(date +%Y%m%d_%H%M%S).sql.gz"
```

Then decide whether to truncate application tables, recreate the database volume, or run a project-specific cleanup command. Do not remove the Docker volume unless you are certain all data can be deleted.

## Troubleshooting

### 502 Bad Gateway

Nginx is reachable, but the Django app is not.

Check:

```bash
docker compose -f docker-compose.deploy.yaml ps
docker compose -f docker-compose.deploy.yaml logs -f app
docker compose -f docker-compose.deploy.yaml logs -f proxy
```

Common causes:

- `app` container is restarting
- migrations failed
- Elasticsearch is not available
- uWSGI did not start
- proxy was not restarted after certificate creation

### Certbot Stuck at "Waiting for proxy..."

Start or inspect the proxy:

```bash
docker compose -f docker-compose.deploy.yaml up -d app proxy
docker compose -f docker-compose.deploy.yaml ps
docker compose -f docker-compose.deploy.yaml logs proxy
```

Then rerun:

```bash
docker compose -f docker-compose.deploy.yaml run --rm certbot /opt/certify-init.sh
```

### Certbot Fails Domain Validation

Check:

- DNS points to the EC2 Elastic IP
- Port `80` is open in the EC2 security group
- `DOMAIN` in `.env` exactly matches the DNS record
- No other process is using port `80`

### Public IP Changed

Use an Elastic IP. If not using one, update DNS whenever the EC2 public IP changes.

## Deployment Pipeline

Start with manual deployment until the process is stable. A simple future pipeline can:

1. Run tests and lint on push to `prod`
2. SSH into EC2
3. Pull latest code
4. Build app images
5. Run migrations
6. Restart containers

Do not automate production deployment until backups, rollback, and environment secrets are handled.
