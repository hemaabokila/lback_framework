from sqlalchemy import create_engine, inspect, Column, String, Float, Integer, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from lback.models import Base

class Migration:
    def __init__(self, config):
        self.engine = create_engine(config['DATABASE']['URL'])
        self.Session = sessionmaker(bind=self.engine)

    def apply(self, models):
        inspector = inspect(self.engine)

        with self.Session() as session:
            applied_migrations = self.get_applied_migrations(session)

            for model in models:
                table_name = model.__tablename__

                if table_name not in applied_migrations:
                    self.create_table(model)
                    self.record_migration(session, table_name)
                    print(f"Migration applied for table {table_name}.")
                else:
                    print(f"Migration for table {table_name} has already been applied.")

    def create_table(self, model):
        try:
            model.__table__.create(bind=self.engine, checkfirst=True)
            print(f"Table {model.__tablename__} created.")
        except SQLAlchemyError as e:
            print(f"Error creating table {model.__tablename__}: {e}")

    def get_applied_migrations(self, session):
        return {row.migration_name for row in session.query(MigrationRecord).all()}

    def record_migration(self, session, table_name):
        migration_record = MigrationRecord(migration_name=table_name)
        session.add(migration_record)
        session.commit()

    def rollback(self, table_name):
        with self.Session() as session:
            try:
                session.execute(f"DROP TABLE IF EXISTS {table_name}")
                session.commit()
                self.remove_migration_record(session, table_name)
                print(f"Rollback migration for table {table_name}.")
            except SQLAlchemyError as e:
                print(f"Error rolling back migration for table {table_name}: {e}")

    def remove_migration_record(self, session, table_name):
        session.execute('DELETE FROM migrations WHERE migration_name = ?', (table_name,))
        session.commit()

class MigrationRecord(Base):
    __tablename__ = 'migrations'

    id = Column(Integer, primary_key=True)
    migration_name = Column(String, nullable=False, unique=True)
    applied_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MigrationRecord(id={self.id}, name={self.migration_name}, applied_at={self.applied_at})>"
