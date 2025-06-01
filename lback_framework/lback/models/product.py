import logging
from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.orm import validates
from typing import Any, Dict, Optional

from .base import BaseModel

from lback.core.signals import dispatcher

logger = logging.getLogger(__name__)

class Product(BaseModel):
    """
    Represents a product in the inventory.
    Inherits common fields from BaseModel.
    Includes validation rules for product attributes using SQLAlchemy @validates.
    Integrates SignalDispatcher to emit events related to product-specific actions.
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    sku = Column(String, nullable=False, unique=True, index=True)
    category = Column(String, nullable=True, index=True)
    image_url = Column(String, nullable=True)


    @validates('price')
    def validate_price(self, key: str, value: Any) -> float:
        """
        Validate that the price is a non-negative float.
        SQLAlchemy @validates are called before session flush/commit.
        'model_pre_validate' signal is emitted by BaseModel.validate() before these run.
        Specific validation failure signals could be added here if needed,
        but might be overly granular.
        """
        if value is None:
             logger.error("Validation failed for price: Value is None.")
             raise ValueError("Price cannot be None.")
        if not isinstance(value, (int, float)):
             logger.error(f"Validation failed for price '{value}': Not a number.")
             raise ValueError("Price must be a number.")
        if value < 0:
            logger.error(f"Validation failed for price '{value}': Negative value.")
            raise ValueError("Price must be a positive value.")
        return float(value)

    @validates('quantity')
    def validate_quantity(self, key: str, value: Any) -> int:
        """
        Validate that the quantity is a non-negative integer.
        SQLAlchemy @validates are called before session flush/commit.
        'model_pre_validate' signal is emitted by BaseModel.validate() before these run.
        Specific validation failure signals could be added here if needed.
        """
        if value is None:
             logger.error("Validation failed for quantity: Value is None.")
             raise ValueError("Quantity cannot be None.")
        if not isinstance(value, int):
             try:
                 value = int(value)
             except (ValueError, TypeError):
                  logger.error(f"Validation failed for quantity '{value}': Not an integer.")
                  raise ValueError("Quantity must be an integer.")

        if value < 0:
            logger.error(f"Validation failed for quantity '{value}': Negative value.")
            raise ValueError("Quantity must be a non-negative integer.")
        return value

    @validates('sku')
    def validate_sku(self, key: str, value: Optional[str]) -> str:
        """
        Validate that the SKU is not empty.
        SQLAlchemy @validates are called before session flush/commit.
        'model_pre_validate' signal is emitted by BaseModel.validate() before these run.
        """
        if not value or not isinstance(value, str) or len(value.strip()) == 0:
            logger.error("Validation failed for SKU: Value is empty.")
            raise ValueError("SKU cannot be empty.")
        return value.strip()

    @validates('name')
    def validate_name(self, key: str, value: Optional[str]) -> str:
        """
        Validate that the name is not empty.
        SQLAlchemy @validates are called before session flush/commit.
        'model_pre_validate' signal is emitted by BaseModel.validate() before these run.
        """
        if not value or not isinstance(value, str) or len(value.strip()) == 0:
            logger.error("Validation failed for name: Value is empty.")
            raise ValueError("Name cannot be empty.")
        return value.strip()

    @validates('category')
    def validate_category(self, key, value):
        """
        Placeholder for category validation.
        SQLAlchemy @validates are called before session flush/commit.
        'model_pre_validate' signal is emitted by BaseModel.validate() before these run.
        """
        return value

    @validates('image_url')
    def validate_image_url(self, key, value):
        """
        Placeholder for image_url validation.
        SQLAlchemy @validates are called before session flush/commit.
        'model_pre_validate' signal is emitted by BaseModel.validate() before these run.
        """
        return value


    def update_quantity(self, amount: int):
        """
        Updates the product quantity by a specified amount.
        Raises ValueError if the resulting quantity would be negative.
        Emits 'product_quantity_updated' signal on success.
        Emits 'product_quantity_update_failed' signal on failure.

        Args:
            amount: The integer amount to add to the current quantity (can be positive or negative).
        """
        product_id = getattr(self, 'id', 'N/A')
        product_name = getattr(self, 'name', 'N/A')
        original_quantity = self.quantity
        new_quantity = self.quantity + amount

        logger.info(f"Attempting to update quantity for product '{product_name}' (ID: {product_id}) by {amount}. Original: {original_quantity}, New proposed: {new_quantity}.")

        try:
            if new_quantity < 0:
                 logger.warning(f"Attempted to update quantity for product '{product_name}' (ID: {product_id}) to negative value ({new_quantity}).")
                 dispatcher.send("product_quantity_update_failed", sender=self, product=self, amount=amount, original_quantity=original_quantity, proposed_quantity=new_quantity, error_type="negative_quantity")
                 logger.debug(f"Signal 'product_quantity_update_failed' (negative_quantity) sent for product '{product_name}'.")
                 raise ValueError("Resulting quantity cannot be negative.")

            self.quantity = new_quantity
            logger.info(f"Updated quantity for product '{product_name}' (ID: {product_id}) by {amount}. New quantity: {self.quantity}")
            dispatcher.send("product_quantity_updated", sender=self, product=self, amount=amount, original_quantity=original_quantity, new_quantity=self.quantity)
            logger.debug(f"Signal 'product_quantity_updated' sent for product '{product_name}'.")

        except ValueError as e:
            raise e
        except Exception as e:
            logger.exception(f"Unexpected error updating quantity for product '{product_name}' (ID: {product_id}): {e}")
            dispatcher.send("product_quantity_update_failed", sender=self, product=self, amount=amount, original_quantity=original_quantity, proposed_quantity=new_quantity, error_type="exception", exception=e)
            logger.debug(f"Signal 'product_quantity_update_failed' (exception) sent for product '{product_name}'.")
            raise


    def apply_discount(self, discount_percentage: float):
        """
        Applies a percentage discount to the product price.
        Raises ValueError if the discount percentage is invalid.
        Emits 'product_discount_applied' signal on success.
        Emits 'product_discount_application_failed' signal on failure.

        Args:
            discount_percentage: The discount percentage (0 to 100).
        """
        product_id = getattr(self, 'id', 'N/A')
        product_name = getattr(self, 'name', 'N/A')
        original_price = self.price

        logger.info(f"Attempting to apply {discount_percentage}% discount to product '{product_name}' (ID: {product_id}). Original price: {original_price}.")

        try:
            if not (0 <= discount_percentage <= 100):
                logger.warning(f"Attempted to apply invalid discount percentage ({discount_percentage}) for product '{product_name}' (ID: {product_id}).")
                dispatcher.send("product_discount_application_failed", sender=self, product=self, discount_percentage=discount_percentage, original_price=original_price, error_type="invalid_percentage")
                logger.debug(f"Signal 'product_discount_application_failed' (invalid_percentage) sent for product '{product_name}'.")
                raise ValueError("Discount percentage must be between 0 and 100.")

            discount_factor = 1 - (discount_percentage / 100)
            self.price *= discount_factor
            self.price = round(self.price, 2)

            logger.info(f"Applied {discount_percentage}% discount to product '{product_name}' (ID: {product_id}). New price: {self.price}")
            dispatcher.send("product_discount_applied", sender=self, product=self, discount_percentage=discount_percentage, original_price=original_price, new_price=self.price)
            logger.debug(f"Signal 'product_discount_applied' sent for product '{product_name}'.")

        except ValueError as e:
            raise e
        except Exception as e:
            logger.exception(f"Unexpected error applying discount for product '{product_name}' (ID: {product_id}): {e}")
            dispatcher.send("product_discount_application_failed", sender=self, product=self, discount_percentage=discount_percentage, original_price=original_price, error_type="exception", exception=e)
            logger.debug(f"Signal 'product_discount_application_failed' (exception) sent for product '{product_name}'.")
            raise


    @classmethod
    def get_fields(cls) -> Dict[str, str]:
        """
        Returns a dictionary of column names and their SQLAlchemy types for this model.
        Useful for introspection, e.g., in generic admin views.
        # No signals here, as this is a static introspection method.
        """
        return {column.name: str(column.type) for column in cls.__table__.columns}

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the Product instance."""
        return (f"<Product(id={getattr(self, 'id', 'N/A')}, name='{getattr(self, 'name', 'N/A')}', price={getattr(self, 'price', 'N/A')}, "
                f"quantity={getattr(self, 'quantity', 'N/A')}, sku='{getattr(self, 'sku', 'N/A')}', category='{getattr(self, 'category', 'N/A')}')>")
