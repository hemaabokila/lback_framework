Models & Database
=================

Lback Framework supports database integration using SQLAlchemy as the ORM.

You define your data models as Python classes inheriting from SQLAlchemy's declarative base.

    .. code-block:: python

        # courses/models.py
        from datetime import datetime
        from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
        from lback.models.base import BaseModel
        
        class Course(BaseModel):
            __tablename__ = 'courses'
        
            id = Column(Integer, primary_key=True, autoincrement=True)
            name = Column(String(200), nullable=False)
            description = Column(String)
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, onupdate=datetime.utcnow)
            image_path = Column(String(255), nullable=True)
            slug = Column(String(255), unique=True, nullable=True)
        
            def __str__(self):
                return self.name
        
            # ... relationships and other models
        
Database sessions are typically managed and provided to Views and other components via the SQLAlchemy Middleware and Dependency Injection.