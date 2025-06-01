import logging
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from typing import Any, Dict


logger = logging.getLogger(__name__)

Base = declarative_base()

class BaseModel(Base):
    """
    Abstract base class for all SQLAlchemy models in the application.
    Provides common fields like primary key ID, creation timestamp, and update timestamp.
    Integrates SignalDispatcher to emit events related to model lifecycle (specifically validation).
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def validate(self) -> None:
        """
        Placeholder method for model validation.
        Subclasses should override this method to implement specific validation logic
        before saving or updating an instance.
        Should raise a ValidationError or similar exception if validation fails.
        Emits 'model_pre_validate' signal before any validation logic runs.
        """
        from lback.core.signals import dispatcher
        model_name = self.__class__.__name__
        model_id = getattr(self, 'id', 'N/A')
        logger.debug(f"BaseModel validate method called for {model_name} id={model_id}.")
        dispatcher.send("model_pre_validate", sender=self, model_instance=self, model_name=model_name, model_id=model_id)
        logger.debug(f"Signal 'model_pre_validate' sent for {model_name} id={model_id}.")

        pass


    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the model instance."""
        return f"<{self.__class__.__name__} id={getattr(self, 'id', 'N/A')}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the model instance.
        Note: This is a basic implementation and might not handle relationships or complex types well.
        Consider using a dedicated serialization library for more complex scenarios.
        """
        return {c.key: getattr(self, c.key) for c in self.__mapper__.columns}

