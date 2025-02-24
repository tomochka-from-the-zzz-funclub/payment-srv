from pydantic import BaseModel, Field
from typing import List
from fastapi import APIRouter, Request
from app.services.yookassa.payment_service import PaymentService

# Pydantic Models
class ProductDTO(BaseModel):
    product_id: int = Field(..., gt=0, description="Must be a positive integer")
    amount: int = Field(..., gt=0, description="Must be a positive integer")

class BuyProductsDTO(BaseModel):
    initiator_id: int = Field(..., gt=0, description="Must be a positive integer")
    products: List[ProductDTO] = Field(..., min_items=1, description="Must be a non-empty list of products")

class ProcessPaymentDTO(BaseModel):
    payment_id: str = Field(..., min_length=1)

class Amount(BaseModel):
    value: float = Field(..., description="The amount of money")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code (e.g., USD, EUR)")

class BaseInfo(BaseModel):
    id: str = Field(..., description="Unique identifier for the payment information")
    status: str = Field(..., description="Current status of the payment")
    paid: bool = Field(..., description="Indicates whether the payment has been completed")
    amount: Amount = Field(..., description="Details of the payment amount and currency")

class PaymentNotification(BaseModel):
    type: str = Field(..., description="Type of the notification")
    event: str = Field(..., description="Specific event that occurred")
    object: BaseInfo = Field(..., description="Payment information associated with the notification")

# FastAPI Router
payment = APIRouter()
payment_svc = PaymentService()

@payment.post('/make')
async def make_payment(payload: BuyProductsDTO):
    return await payment_svc.make_payment(payload)

@payment.post('/refund')
async def refund_payment(payload: ProcessPaymentDTO):
    return await payment_svc.refund_payment(payload.payment_id)

@payment.post('/cancel')
async def cancel_payment(payload: ProcessPaymentDTO):
    return await payment_svc.cancel_payment(payload.payment_id)

@payment.get('/')
async def get_payment(payload: ProcessPaymentDTO):
    return await payment_svc.get_payment(payload.payment_id)

@payment.get('/success')
async def success():
    return "Вы успешно оплатили свои покупки, теперь отдыхайте"

@payment.post("/finalize")
async def handle_payment_success(request: Request):
    return await payment_svc.handle_payment_status(request)
