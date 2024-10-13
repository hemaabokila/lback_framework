from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class Session:
    def __init__(self, database_url='sqlite:///:memory:', echo=False):
        self.engine = create_engine(database_url, echo=echo)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self.create_tables()

    def create_tables(self):
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tables created successfully.")
        except exc.SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")

    def get_session(self):
        session = self.Session()
        return session

    def close_session(self, session):
        if session:
            session.close()
            self.Session.remove()
            logger.info("Session closed successfully.")

    def execute_transaction(self, func):
        session = self.get_session()
        try:
            result = func(session)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise e
        finally:
            self.close_session(session)

    def drop_tables(self):
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped successfully.")
        except exc.SQLAlchemyError as e:
            logger.error(f"Error dropping tables: {e}")

    def reset_database(self):
        self.drop_tables()
        self.create_tables()
        logger.info("Database reset successfully.")

    def add_entry(self, model_instance):
        return self.execute_transaction(lambda session: session.add(model_instance))

    def delete_entry(self, model_instance):
        return self.execute_transaction(lambda session: session.delete(model_instance))

    def update_entry(self, model_instance):
        return self.execute_transaction(lambda session: session.merge(model_instance))

    def get_all_entries(self, model):
        session = self.get_session()
        try:
            return session.query(model).all()
        finally:
            self.close_session(session)

    def get_entry_by_id(self, model, entry_id):
        session = self.get_session()
        try:
            return session.query(model).get(entry_id)
        finally:
            self.close_session(session)

    def query(self, model):
        session = self.get_session()
        return session.query(model)

    def commit(self, session):
        session.commit()

    def rollback(self, session):
        session.rollback()
