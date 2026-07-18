**Language / Язык:** [English](../../domains/schema-collections.md) | [Русский](schema-collections.md)

# Schema-коллекции

Операции активного series pack без специализированного semantic handler
обслуживает **schema engine**. Ответы следуют форме контракта и при необходимости
сохраняются в `ov_api_objects`.

Полный каталог — в Web UI или в `contracts/ovirt/<series>/api.json`. Числа
покрытия: [api_coverage.md](../api_coverage.md).

Примеры коллекций из pack (доступность зависит от series): `bookmarks`, `tags`,
`quotas`, `affinitygroups` и другие коллекции Engine, связанные с корнем API.
