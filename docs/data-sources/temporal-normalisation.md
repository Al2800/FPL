# Temporal normalisation

Every acquired value is wrapped in the source-neutral schema at
`control/schemas/data/temporal-observation.json` before it can become a feature.
The envelope preserves event, publication, observation, ingestion, effective and
finalisation timestamps separately. Missing source timestamps remain `null`.

## Availability policy

`control/policies/source-availability.yaml` is the versioned authority for deriving
`available_at`. A source and field must have an exact policy entry; unknown pairs
fail closed. `latest_of` takes the conservative maximum of its named timestamps.
Any permitted fallback is named in `when_missing`. For example, missing FPL news
publication time remains missing while the policy uses `ingested_at` as the
decision-safe bound. It is never silently replaced by `observed_at`.

All supplied timestamps must contain a timezone. Normalisation stores them in UTC,
requires `ingested_at >= observed_at`, and assigns a deterministic content hash.

## Point-in-time views

`observations_as_of(records, cutoff)` applies the inclusive rule
`available_at <= cutoff`, then selects the latest eligible observation for each
source, field and canonical entity. The operation is deterministic under input
reordering. A correction whose effective time is old but whose observation or
ingestion time is after the cutoff therefore cannot change the earlier view.

Add a policy entry and contract fixture before admitting a new source field. Do
not add a permissive global default: the absence of policy is a governance error.
