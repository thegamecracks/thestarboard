# Real-Time Starboard

This document is here for future design decisions to make the bot more effective
at scaling.
As of now, the [current implementation](/src/thestarboard/cogs/stars/events.py)
updates messages in real-time without concern for conflicting events or rate-limits,
and no principles below are implemented.

## Worker Queue

Whenever events are received that warrant a starboard message being
sent/updated/deleted, it should go to a set of jobs.
A job set can be created for each channel to increase concurrency while
more easily staying within rate-limits.
A worker should be created for each channel to handle those jobs.

Each job should contain the following information:
- `message_id`: Uniquely identifies a job.
- `operation`: The operation that the job does (send / edit / delete)
- `data`: Any extra data needed for that operation to complete.

## Collisions

When two jobs collide by their message ID, one job should come out.
Here are how different job permutations should be handled:

- `send` + `send`: The older job should be overwritten.
- `edit` + `edit`: Data should be merged into one edit job.
- `edit` + `delete`: The older job should be overwritten.
- `delete` + `edit`: The newer job should be discarded.
- `delete` + `delete`: The older job should be overwritten.

When merging data, jobs are assumed to be up-to-date at time of creation and
idempotent. As such, the newer job's data should be preferred for resolving
conflicts.

## Race Conditions

Worker assignment/termination should be locked to ensure a worker does not
exit as a new job comes in. This can be done with a synchronous set.

Jobs should not be updated if they are already being processed as undoing it
would be more difficult. This can be done by popping jobs from the set when
they are being processed. Two jobs can only be merged before one of them
gets processed.

## Batching Message Deletions

Up to 100 messages less than two weeks old can be bulk-deleted in one API call
for increased efficiency. However, the likelihood of more than one starboard
message being deleted at a time is unlikely when running jobs in real-time.
Regardless, this is left here as a future concern.

## Reducing API Calls

discord.py will manage rate-limits for us, but workers could be slowed down
to increase the likelihood of jobs being merged, and therefore reducing
redundant API calls.

## Persistency

As of now, workloads are expected to be small so persistency is not a concern.
However if the bot is to scale, a message queue would be very ideal for
handling jobs across bot downtime.
