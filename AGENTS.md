
# AGENTS.md

# Backend Engineering Instructions

## 1. Project Architecture

Follow the architecture and folder responsibilities
defined in `CODE_STRUCTURE.md`.

The project follows a modular architecture with
separation of concerns.

Every module must maintain clear boundaries between:

- HTTP handling
- Request/response validation
- Business logic
- Database access

## 2. Separation of Concerns

Follow these rules strictly:

### Router
- Handle HTTP requests and responses.
- Define routes, status codes and dependencies.
- Validate input through Pydantic schemas.
- Delegate business logic to the service layer.
- Do not write database queries here.

### Schemas
- Define request and response structures.
- Use Pydantic models.
- Do not put business logic here.

### Models
- Define SQLAlchemy database models.
- Represent database storage structures.
- Do not put API request/response validation here.

### Service
- Contain business logic.
- Coordinate repositories and infrastructure.
- Must not depend on FastAPI HTTP objects.
- Must not directly handle HTTP responses.

### CRUD / Repository
- Handle database operations.
- Encapsulate queries and persistence logic.
- Do not implement business rules.
- Do not handle HTTP requests or responses.

## 3. Infrastructure Rules

- Shared infrastructure belongs in `infrastructure/`.
- Database connections must be managed centrally.
- Reuse existing authentication, caching and storage
  implementations.
- Do not duplicate infrastructure components inside
  individual modules.

## 4. Development Rules

Before implementing a feature:

1. Inspect the existing project structure.
2. Read the relevant architecture documentation.
3. Identify existing reusable components.
4. Prepare an implementation plan.
5. Identify affected modules and dependencies.

During implementation:

- Follow existing naming conventions.
- Use dependency injection where appropriate.
- Use async database operations consistently.
- Avoid unnecessary abstractions.
- Avoid introducing duplicate functionality.
- Do not modify unrelated modules.

## 5. Testing

- Write tests for new functionality.
- Cover success and failure scenarios.
- Run relevant existing tests after modifications.
- Do not modify tests merely to make an implementation pass.
- Mention what all cases was tested for the functionality and what was expected

## 6. Documentation

- Update API documentation when contracts change.
- Update CODE_STRUCTURE.md when the architecture changes.
- Explain significant architectural decisions.
- Report deviations from documented standards.

## 7. Important Constraints

Do not introduce a new architectural pattern
without explaining why it is necessary.

If an existing implementation violates these rules,
identify the issue and propose a refactoring plan
before making structural changes.
