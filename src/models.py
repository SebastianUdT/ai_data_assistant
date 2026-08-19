from pydantic import BaseModel


class Customer(BaseModel):
    name: str
    email: str
    purchase_amount: float