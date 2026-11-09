# M1 deployment unit: pending wavelet linkage

Status: locally implemented and awaiting deployment validation, not an enabled
feature. This document covers only the B3-B4 domain resolver and periodic Celery
task. It is not the full M1 deployment plan.

## Current state

- B1-B2 are implemented locally: optional `domain_session_id`, server-stamped
  owner UUID in `user_id`, and initial `link_status` metadata.
- A valid, owned `domain_id` produces `linked`; a blank ID with a session hint
  produces `pending`. Blank ID without a hint remains unclassified.
- B3's resolver and B4's task are implemented in
  [linkage.py](app/wavelets/linkage.py) and [tasks.py](app/wavelets/tasks.py).
- The Beat schedule is gated by `WAVELET_LINKAGE_ENABLED=1`; it is disabled by
  default. No scheduler or worker has been deployed by this change.
- No historical documents have been migrated or repaired.

## Goal and boundaries

Wavelets can arrive before their Domain record. The current extension's
10-second wait cannot guarantee that the Domain is available in time.

Store the wavelet immediately, then attach the Domain UUID asynchronously when
the corresponding visit arrives. `domain_id` remains the permanent analysis
join key; `domain_session_id` is only a resolution hint.

This unit must not:

- Repair historical orphans or infer missing ownership/session hints.
- Create synthetic Domain records.
- Guess a relationship from a URL alone or search another participant's data.
- Change extension privacy rules.
- Deploy or merge changes to dev, main, or production as part of implementation.

## Mandatory enablement prerequisite

Verify that the extension sends exactly the same time-extended,
visit-specific `domain_session_id` on the Domain and its wavelets. Generate the
visit time once and reuse it; independently generated timestamps will not match.

Backend metadata support does not establish this extension contract. Do not
enable periodic resolution until the contract is verified end to end.

Masked records, such as `only_host`, can still have a valid Domain UUID.
Do not interpret masking as proof that linking is forbidden. The inspected
extension blocks private/full-deny wavelets before submission.

## Execution unit

One periodic task, registered as `wavelets.tasks.resolve_pending_wavelets`.
Do not enqueue a separate retry chain for every wavelet.

| Component | Responsibility |
|---|---|
| B3 resolver | Look up Domain UUID by owner UUID and exact session hint |
| Celery worker | Execute bounded resolution batches |
| Celery Beat | Enqueue the task periodically |
| Shared lock | Prevent overlapping runs, including retries |

Initial implementation defaults:

- Schedule: every 60 seconds.
- Batch limit: 500 documents per run.
- Resolution window: five minutes from server-generated `created_at`.
- Periodic scheduling: disabled until the prerequisite and acceptance checks pass.
- Batch time budget: 80 seconds; Celery soft/hard limits: 100/120 seconds.
- Redis ownership-token lease: 180 seconds, renewed before each document update.
- Transient dependency errors: at most three Celery retries with 5/10/20-second
  delays. Scheduled messages expire after 60 seconds to limit stale queue buildup.

The lease uses the Redis instance configured by `CELERY_BROKER_URL` (the
`CELERY_BROKER` environment variable). PostgreSQL and Elasticsearch are used via
the existing Django and Elasticsearch connections. No new dependencies are added.

The existing [Celery configuration](app/app/celery.py) autodiscovers application
tasks. [Staging Compose](docker-compose.staging.yaml) has an explicit worker
command but no Beat service. [Deployment Compose](docker-compose.deploy.yaml)
declares a worker-named service without an explicit Celery command; verify its
actual entrypoint/command rather than assuming it runs a worker. Neither file
currently declares a Beat service.

M1 integration must explicitly configure worker execution and exactly one Beat
scheduler with shared broker/database/Elasticsearch connectivity. Do not start a
second Beat instance alongside an existing external scheduler.

## Resolver and task behavior

1. Select only documents explicitly marked `pending` in the known wavelet
   index families, including relevant previous monthly indices.
2. Require a valid owner UUID, nonblank session hint, and usable `created_at`.
   Log malformed pending documents explicitly; do not silently guess defaults.
3. Resolve using `Domain.user_id` (the owner UUID foreign key, not the separate
   GESIS login identifier) plus exact `domain_session_id`.
4. Exactly one match: conditionally stamp `domain_id` and `link_status=linked`
   on that document, using its original index and document ID.
5. No match before the deadline: leave pending for another scheduled run.
6. No match after the deadline: make a final successful lookup, then
   conditionally set `link_status=expired`.
7. Multiple matches: never select an arbitrary record. Report ambiguity.
   The initial conservative resolver leaves it pending until the deadline and
   then expires it after a final check. The roadmap's interval/latest-start-time
   tie-break is a separate rule to implement and test explicitly, not an implicit
   ordering fallback.

Expired means this bounded repair window ended without a safe match; it does not
prove that a Domain can never arrive later. Automatic reconsideration of expired
documents is outside this unit.

Do not restrict selection to documents created within the last five minutes.
Older pending documents need a final lookup after outages. Bound the work per run
instead, and ensure batch ordering/pagination does not repeatedly select the same
unresolved documents while starving the remainder. Include month-boundary tests.

The implementation sorts by `updated_at` oldest first and updates it after each
attempt, including malformed records. This rotates bounded batches without a
persisted cursor. `created_at` is never changed, so rotation cannot extend the
resolution deadline. Malformed pending records remain pending and are reported;
they are not falsely expired without usable metadata.

## Failure handling and concurrency

- Database/Elasticsearch connection failures are operational errors, not missing
  Domain records. Log and retry transient failures with bounded backoff; never
  expire a document solely because a dependency was unavailable.
- Check every Elasticsearch update result, including bulk item failures.
- Make updates conditional on unchanged pending state, blank `domain_id`, and
  unchanged owner/session metadata, or use optimistic concurrency with a reread.
  Never overwrite a relationship established by another execution.
- The shared lock must use an ownership token, bounded lifetime, and safe
  owner-only release. Set a task execution bound consistent with the lock
  lifetime; a stale run must not overlap a replacement after lock expiry.
- Prevent queued duplicate sweeps from accumulating when execution is slow.
- Report examined, linked, still-pending, expired, ambiguous, malformed, and
  failed counts. Avoid logging wavelet contents or full session hints/URLs.

## Automated coverage and remaining M1 acceptance checks

- [x] One owned exact match returns its UUID; another user's matching hint does not.
- [x] Missing and ambiguous matches are distinguished without arbitrary selection.
- [x] Wavelet first, Domain later: pending becomes linked on a later task run.
- [x] Deadline passes with no Domain: final lookup occurs before expiry.
- [x] Dependency failures cause retry/failure reporting, not false expiry.
- [x] Retry or duplicate task execution cannot overwrite an existing relationship.
- [x] Lock contention skips overlapping work; lock ownership/release is verified.
- [x] Batch overflow makes progress across pending documents.
- [x] Original-index updates and unbounded-by-date selection cover prior months.
- [x] Legacy documents without pending status remain untouched.
- [x] Malformed pending documents are reported without blocking healthy documents.
- [x] All LLM/social index mappings and stored linkage metadata are verified.
- [ ] Extension shares the same visit-specific hint on both payloads.
- [ ] Worker registers the task; a single Beat instance schedules it.
- [ ] Observe a controlled pending-to-linked example and summary counts on staging.

Local validation uses the isolated-index/lock integration tests in
[test_linkage.py](app/wavelets/tests/test_linkage.py), alongside the intake/BOLA
tests in [test_wavelets_domain_id.py](app/wavelets/tests/test_wavelets_domain_id.py).
These exercise PostgreSQL, Elasticsearch, and Redis without dispatching a
production-wide sweep. Task autodiscovery and the enabled/disabled Beat
configuration can be checked without starting Beat or submitting work.

## M1 activation and rollback

1. Ship the reviewed backend code with scheduling disabled.
2. Apply/verify mapping additions on indices eligible for new pending writes.
   Mapping changes do not populate historical document values.
3. Confirm worker/broker/Elasticsearch connectivity and task registration.
4. Verify the coordinated extension contract and run one controlled task manually.
5. Enable the single Beat schedule and monitor batch progress, errors, and expiry.

Enable the schedule by setting `WAVELET_LINKAGE_ENABLED=1` on the Beat process
and restarting it after acceptance. Worker commands are `celery -A app worker
-l info`; the single scheduler command is `celery -A app beat -l info`. Integrate
these with the M1 service manager rather than assuming a worker-named container
runs the correct command.

For a controlled manual execution in the configured Django environment:

```python
from wavelets.tasks import resolve_pending_wavelets

result = resolve_pending_wavelets.delay()
```

Manual dispatch does not require the Beat enablement flag; operators must verify
the extension prerequisite before doing it. The flag gates scheduling, not
individual task execution. This task does not run merely because code is loaded.

To roll back automation, disable this task's schedule and prevent queued copies
from running; let active work finish or stop it through the deployment's
controlled procedure. Keep optional mapping fields and already-correct UUID
links. Do not delete documents, rebuild indices, or roll back unrelated workers.
Pending documents can remain stored while the repair mechanism is disabled.

This handoff does not authorize deployment, extension edits, commits, or pushes.
