# Database design

MySQL database `expense_tracker`, two tables (InnoDB, utf8mb4).

**categories**: `id` (PK, auto increment), `name` (VARCHAR 50, unique, not null), `description` (VARCHAR 255, null), `created_at`.

**expenses**: `id` (PK), `title` (VARCHAR 100), `amount` (DECIMAL(10,2), CHECK amount > 0), `expense_date` (DATE), `category_id` (FK -> categories.id, ON DELETE RESTRICT), `notes` (VARCHAR 500, null), `created_at`. Indexes on `expense_date` and `category_id`.

Relationship: one category has many expenses. A category with expenses cannot be deleted.

Rules enforced twice (in the web application and in the database): positive amount, required fields, valid category.
