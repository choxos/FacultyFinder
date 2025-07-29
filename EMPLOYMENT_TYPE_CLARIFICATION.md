# Employment Type Classification in FacultyFinder

## Database Fields

### `full_time` Column (Boolean)
- **`TRUE`** = Full-time employment
- **`FALSE`** = Part-time employment

### `adjunct` Column (Boolean)
- **`TRUE`** = Adjunct faculty
- **`FALSE`** = Regular faculty

## Computed `employment_type` Field

The API automatically computes an `employment_type` string field based on the database values:

| `adjunct` | `full_time` | `employment_type` |
|-----------|-------------|-------------------|
| `TRUE`    | any         | `"adjunct"`       |
| `FALSE`   | `TRUE`      | `"full-time"`     |
| `FALSE`   | `FALSE`     | `"part-time"`     |

## API Response Example

```json
{
  "id": 125,
  "professor_id": 1,
  "faculty_id": "CA-ON-002-00001",
  "name": "Dr. Jane Smith",
  "full_time": true,
  "adjunct": false,
  "employment_type": "full-time"
}
```

## Priority Logic

1. **Adjunct status takes priority** - If `adjunct = TRUE`, employment_type will be `"adjunct"` regardless of `full_time` value
2. **Full-time vs Part-time** - For regular faculty (`adjunct = FALSE`), the `full_time` field determines if they're `"full-time"` or `"part-time"`

This classification helps users quickly understand employment status without needing to interpret boolean flags. 