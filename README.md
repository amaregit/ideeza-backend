# IDEEZA - Senior Backend Developer Assessment

This Django backend provides analytics APIs for blog views, top performers, and performance metrics.

## Installation

### Option 1: Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/amaregit/ideeza-backend.git
   cd ideeza
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Run the server:
   ```bash
   python manage.py runserver
   ```

### Option 2: Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/amaregit/ideeza-backend.git
   cd ideeza-backend
   ```

2. Build and run with Docker Compose:
   ```bash
   docker compose up --build
   ```

The application will be available at http://localhost:8000

**Note**: Docker setup uses PostgreSQL as the database. The database data is persisted in a Docker volume.

## APIs

### 1. /analytics/blog-views/

Groups blogs and views by selected object_type.

**Parameters:**
- `object_type`: `country` or `user`
- `range`: `month`, `week`, or `year` (default: `month`)
- Dynamic filters: Support for advanced filtering with operators
  - `field__eq=value` (equals)
  - `field__ne=value` (not equals)
  - `field__in=value1,value2` (in list)
  - `field__contains=value` (contains)
  - `field__icontains=value` (case-insensitive contains)
  - `field__gt=value`, `field__gte=value` (greater than)
  - `field__lt=value`, `field__lte=value` (less than)
  - Examples: `country__eq=Ethiopia`, `user__in=alice,bob`, `title__icontains=django`

**Response:**
```json
[
  {
    "x": "grouping key",
    "y": "number_of_blogs",
    "z": "total_views"
  }
]
```

### 2. /analytics/top/

Returns top 10 based on total views.

**Parameters:**
- `top`: `user`, `country`, or `blog`
- `range`: `month`, `week`, or `year` (default: `month`)
- Dynamic filters: Same advanced filtering support as blog-views API

**Response:**
```json
[
  {
    "x": "name/title",
    "y": "total_views",
    "z": "num_blogs/author_username"
  }
]
```

### 3. /analytics/performance/

Shows time-series performance.

**Parameters:**
- `compare`: `month`, `week`, `day`, or `year` (default: `month`)
- `user`: specific user username (optional)
- Dynamic filters: Same advanced filtering support as other APIs

**Response:**
```json
[
  {
    "x": "period label (num_blogs blogs)",
    "y": "views",
    "z": "growth_percentage"
  }
]
```

## Models

- **Country**: Represents countries.
- **User**: Users with country association.
- **Blog**: Blogs authored by users.
- **View**: Blog views with timestamps.

## Requirements

- Django 5.2.8
- Django REST Framework 3.16.1