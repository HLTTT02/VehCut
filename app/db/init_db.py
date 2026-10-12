"""Development bootstrap: create SQLAlchemy tables for local Docker testing."""
import app.entities  # noqa: F401
from app.db.base import Base
from app.db.session import engine

def main() -> None:
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    main()

