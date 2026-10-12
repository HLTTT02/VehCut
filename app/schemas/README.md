# API DTO and validation guide

DTOs in this folder are Pydantic contracts for API input/output. They are separate from SQLAlchemy entities in app/entities.

1. Why DTO differs from Entity

An entity maps database columns, relationships, and persistence lifecycle. A DTO defines only public API fields and their validation/serialization rules. Keeping them separate prevents accidental exposure of internal columns or relationships, and permits API contracts to evolve independently from database schema.

2. Why validate before Service

FastAPI validates a request DTO while binding controller arguments. Invalid input never reaches the service, so business code can assume basic type, range, and allowed-value invariants. This reduces defensive checks and prevents invalid jobs from being persisted or enqueued.

3. HTTP 422 on validation failure

When a controller declares a Pydantic model, such as:
    def create_job(payload: ProcessVideoRequest): ...

FastAPI parses and validates the JSON before invoking the function. A confidence_threshold above 1, negative padding, zero min_clip_duration, or unsupported vehicle class raises RequestValidationError automatically. FastAPI returns HTTP 422 with a detail array naming the invalid field and validation reason. Controllers do not need try/except for ordinary DTO validation errors.

