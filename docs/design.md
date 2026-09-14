# Design

## Business rules

- Product
    - Belongs to a category (any level, not just leaf categories)
    - Create
        - Validate title length
        - Validate Image URL length and URL format if present
        - Validate unique SKU
        - Validate positive price/free and known currency
        - Validate category reference
        - Created At = Updated At = now
        - Concurrency measures out of scope
    - Read
        - Additional `price_display` is returned as decimal string + currency
        - Search functionality is part of this and includes products matching
            - a certain title (partial match; min 3 chars)
            - a certain SKU (full match)
            - price range
            - category (exact and children)
        - Other fields returned verbatim
    - Update
        - Validations same as create
        - Updated At = now
        - Concurrency measures out of scope
    - Delete
        - Soft-deletion out of scope
        - No reference checks needed
        - Concurrency measures out of scope

- Category
    - Belongs to one parent category OR is top level
    - Has many child categories
    - Has many products
    - Create
        - Validate name length
        - Validate name + parent combo uniqueness
        - Created At = Updated At = now
        - Concurrency measures out of scope
    - Read
        - Fields returned verbatim
    - Update
        - Validations same as create
        - Validate no cycles (Django level check)
        - Updated At = now
        - Concurrency measures out of scope
    - Delete
        - Soft-deletion out of scope
        - Prevent deletion if:
            - products are already present within
            - child categories are already present
        - Concurrency measures out of scope

## API endpoints

| method   | path                       | request                                                                                                         | response / errors                                                     |
|----------|----------------------------|-----------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| `GET`    | `/api/v1/products/`        | query params: `title`, `sku`, `price_cents_min`, `price_cents_max`, `category`, `limit`, `offset`, all optional | 200 paginated list, order by id; 400 invalid query param              |
| `POST`   | `/api/v1/products/`        | `title`, `description?`, `image_url?`, `sku`, `price_cents`, `currency?`, `category_id`                         | 201 created; 400 validation (including category not found)            |
| `GET`    | `/api/v1/products/{id}/`   | -                                                                                                               | 200; 404 not found                                                    |
| `PUT`    | `/api/v1/products/{id}/`   | same fields as create                                                                                           | 200 updated; 400 validation; 404 not found                            |
| `PATCH`  | `/api/v1/products/{id}/`   | any fields                                                                                                      | same as update                                                        |
| `DELETE` | `/api/v1/products/{id}/`   | -                                                                                                               | 204; 404 not found                                                    |
| `GET`    | `/api/v1/categories/`      | -                                                                                                               | 200 full list, order by id (not paginated)                            |
| `POST`   | `/api/v1/categories/`      | `name`, `parent_id?`                                                                                            | 201 created; 400 validation                                           |
| `GET`    | `/api/v1/categories/{id}/` | -                                                                                                               | 200; 404 not found                                                    |
| `PUT`    | `/api/v1/categories/{id}/` | same as create                                                                                                  | 200 updated; 400 validation (including detected cycle); 404 not found |
| `PATCH`  | `/api/v1/categories/{id}/` | any fields                                                                                                      | same as update                                                        |
| `DELETE` | `/api/v1/categories/{id}/` | -                                                                                                               | 204; 404 not found; 409 category has products or children             |

**Product example**:

```json
{
  "id": 101,
  "title": "Лаврак Филе Прясно",
  "description": "Пресен лаврак, ~520g",
  "image_url": "https://example.com/images/lavrak-file.jpg",
  "sku": "FIS-LAV-FIL-001",
  "price_cents": 1383,
  "price_display": "13.83",
  "currency": "EUR",
  "category_id": 12,
  "created_at": "2026-09-14T10:00:00Z",
  "updated_at": "2026-09-14T10:00:00Z"
}
```

**Category example**:

```json
{
  "id": 12,
  "name": "Филета",
  "parent_id": 5,
  "created_at": "2026-09-01T08:00:00Z",
  "updated_at": "2026-09-01T08:00:00Z"
}
```

## Entities & fields

**Product**

| field       | type         | constraints & notes                                                          |
|-------------|--------------|------------------------------------------------------------------------------|
| id          | bigint       | primary key, autogenerated; not null; exposed in API URL                     |
| title       | varchar(255) | indexed, not null; min 3 chars (app-level check); partial match search       |
| description | text         | not null                                                                     |
| image_url   | text         | null OR min 3 chars and URL format (app-level check)                         |
| sku         | varchar(255) | unique, indexed; not null; min 3 chars (app-level check); exact match search |
| price_cents | int          | not null; indexed; `>= 0`                                                    |
| currency    | varchar(3)   | not null; default "EUR"                                                      |
| category_id | bigint       | FK, indexed, not null, any level                                             |
| created_at  | timestamptz  | not null; default now(); in UTC                                              |
| updated_at  | timestamptz  | not null; default now() on insert; in UTC                                    |

**Category**

| field      | type         | constraints & notes                                                 |
|------------|--------------|---------------------------------------------------------------------|
| id         | bigint       | primary key, autogenerated; not null; exposed in API URL            |
| name       | varchar(255) | unique name & parent combo; not null; min 3 chars (app-level check) |
| parent_id  | bigint       | FK, indexed (selfreferencing); no cycles; null = top level          |
| created_at | timestamptz  | not null; default now(); in UTC                                     |
| updated_at | timestamptz  | not null; default now() on insert; in UTC                           |
