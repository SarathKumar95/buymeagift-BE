
# Backend Code Structure

## Overview

The backend follows a modular architecture.

Each business domain is organized into an independent
module.

Shared technical components are maintained inside
the infrastructure layer.

The goal is to maintain separation of concerns,
reusability and maintainability.

## Directory Structure

backend/src/

    modules/
        user/
            router.py
            schemas.py
            models.py
            service.py
            crud.py

        billing/
            router.py
            schemas.py
            models.py
            service.py
            crud.py

    infrastructure/
        config/
        database/
        auth/
        cache/
        storage/
        observability/

    workers/

    api.py
    main.py

## 1. Modules

Each module represents a business domain.

Examples:
- user
- billing
- videos
- subscriptions

### router.py

Responsibility:
- Define HTTP endpoints.
- Handle request and response lifecycle.
- Inject dependencies.
- Delegate operations to service.py.

Must NOT:
- Contain business logic.
- Execute database queries directly.
- Handle complex workflows.

### schemas.py

Responsibility:
- Define Pydantic request schemas.
- Define response schemas.
- Validate incoming data.

Must NOT:
- Contain database models.
- Contain business logic.

### models.py

Responsibility:
- Define SQLAlchemy ORM models.
- Represent database tables and relationships.

Must NOT:
- Contain API request/response schemas.
- Handle HTTP operations.

### service.py

Responsibility:
- Implement business logic.
- Coordinate repository operations.
- Coordinate infrastructure dependencies.
- Handle business workflows.

Must NOT:
- Depend on HTTP Request or Response objects.
- Return HTTP-specific responses.
- Directly manage API routing.

### crud.py

Responsibility:
- Handle database queries.
- Perform create, read, update and delete operations.
- Encapsulate database access.

Must NOT:
- Implement business rules.
- Handle HTTP requests.

## 2. Infrastructure

Contains shared technical components used across
multiple business modules.

### config/
Application configuration and environment settings.

### database/
Database connections, sessions and shared
database configuration.

### auth/
Shared authentication and authorization mechanisms.

### cache/
Redis connections and caching utilities.

### storage/
Object storage integrations such as MinIO.

### observability/
Logging, metrics and tracing configuration.

## 3. Workers

Contains background processing components.

Examples:
- Video transcoding
- Background indexing
- Scheduled jobs

Workers should reuse existing services and
infrastructure instead of duplicating business logic.

## 4. Application Entry Points

### api.py
- Import and mount module routers.
- Configure API-level routing.

### main.py
- Create the FastAPI application.
- Configure application lifespan.
- Initialize and shut down shared resources.
