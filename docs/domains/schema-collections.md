**Language / Язык:** [English](schema-collections.md) | [Русский](../ru/domains/schema-collections.md)

# Schema collections

Operations declared in the active series pack that do not have a specialized
semantic handler are served by the **schema engine**. Responses follow the
contract shape and persist into `ov_api_objects` where applicable.

Browse the full catalog in the Web UI or open
`contracts/ovirt/<series>/api.json`. Coverage numbers:
[api_coverage.md](../api_coverage.md).

Examples of pack-backed entry points (availability depends on series):
`bookmarks`, `tags`, `quotas`, `affinitygroups`, and other Engine collections
linked from the API root.
