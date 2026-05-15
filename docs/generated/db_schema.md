<!-- AUTO-GENERATED — DO NOT EDIT -->
<!-- Source: models.py + alembic/versions/ -->
<!-- Generator: scripts/gen_db_schema.py -->
<!-- Last regenerated against git HEAD: a7e973e / alembic latest: e25c80289a9c -->

# DB Schema (Generated)

> 本檔由 `scripts/gen_db_schema.py` 從 `models.py + alembic/versions/` 自動產生。
> **不要人工編輯**。修改 `models.py` 或 alembic migration 後再次執行（或由 pre-commit hook 自動觸發）。

**最新 Alembic revision**：`e25c80289a9c`

---

## `instances`

| Column | Type | Nullable | PK | Unique | Index | FK |
|---|---|---|---|---|---|---|
| `id` | `INTEGER` | no | ✓ |  | ✓ |  |
| `sop_instance_uid` | `VARCHAR(255)` | yes |  | ✓ | ✓ |  |
| `file_path` | `VARCHAR(500)` | no |  |  |  |  |
| `study_instance_uid` | `VARCHAR(255)` | no |  |  |  | → `studies.study_instance_uid` |
| `series_instance_uid` | `VARCHAR(255)` | yes |  |  | ✓ | → `series.series_instance_uid` |
| `created_at` | `DATETIME` | yes |  |  |  |  |

## `patients`

| Column | Type | Nullable | PK | Unique | Index | FK |
|---|---|---|---|---|---|---|
| `id` | `INTEGER` | no | ✓ |  | ✓ |  |
| `patient_id` | `VARCHAR(255)` | no |  | ✓ | ✓ |  |
| `created_at` | `DATETIME` | yes |  |  |  |  |

## `series`

| Column | Type | Nullable | PK | Unique | Index | FK |
|---|---|---|---|---|---|---|
| `id` | `INTEGER` | no | ✓ |  | ✓ |  |
| `series_instance_uid` | `VARCHAR(255)` | no |  | ✓ | ✓ |  |
| `study_instance_uid` | `VARCHAR(255)` | no |  |  |  | → `studies.study_instance_uid` |
| `created_at` | `DATETIME` | yes |  |  |  |  |

## `studies`

| Column | Type | Nullable | PK | Unique | Index | FK |
|---|---|---|---|---|---|---|
| `id` | `INTEGER` | no | ✓ |  | ✓ |  |
| `study_instance_uid` | `VARCHAR(255)` | no |  | ✓ | ✓ |  |
| `patient_id` | `VARCHAR(255)` | no |  |  |  | → `patients.patient_id` |
| `modality` | `VARCHAR(50)` | yes |  |  |  |  |
| `created_at` | `DATETIME` | yes |  |  |  |  |

---

_Generated 4 tables._
