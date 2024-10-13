from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.orm import validates
from datetime import datetime
from lback.models import BaseModel

class Product(BaseModel):
    __tablename__ = 'products'
    
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    sku = Column(String, nullable=False, unique=True) 
    category = Column(String, nullable=True) 
    image_url = Column(String, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow) 
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 

    @validates('price')
    def validate_price(self, key, value):
        if value < 0:
            raise ValueError("Price must be a positive value.")
        return value

    @validates('quantity')
    def validate_quantity(self, key, value):
        if value < 0:
            raise ValueError("Quantity must be a non-negative integer.")
        return value

    @validates('sku')
    def validate_sku(self, key, value):
        if not value:
            raise ValueError("SKU cannot be empty.")
        return value

    def update_quantity(self, amount):
        if self.quantity + amount < 0:
            raise ValueError("Quantity cannot be negative.")
        self.quantity += amount

    def apply_discount(self, discount_percentage):
        if not (0 <= discount_percentage <= 100):
            raise ValueError("Discount percentage must be between 0 and 100.")
        discount_amount = (self.price * discount_percentage) / 100
        self.price -= discount_amount

    @classmethod
    def get_fields(cls):
        return {column.name: str(column.type) for column in cls.__table__.columns}

    def __repr__(self):
        return (f"<Product(id={self.id}, name={self.name}, price={self.price}, "
                f"quantity={self.quantity}, sku={self.sku}, category={self.category})>")
