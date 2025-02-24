import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from fastapi import Request
from yookassa import Payment as YookassaPayment, Refund
from yookassa.domain.notification import WebhookNotification

from app.infrastructure.repository.repository import UserRepository, PaymentRepository, ProductRepository
from app.infrastructure.schedulers import scheduler
from app.presentation.payment_router import BuyProductsDTO, ProductDTO
from app.services.telegram.telegram_service import TelegramService


class PaymentService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.telegram_service = TelegramService()
        self.payment_repository = PaymentRepository()
        self.product_repository = ProductRepository()

    async def make_payment(self, payload: BuyProductsDTO):
        initiator = await self.user_repository.find_user_by_id(id=payload.initiator_id)

        if initiator is None:
            raise HTTPException(status_code=404, detail='user not found')

        total_sum = await self.calculate_total_sum(payload.products)

        payment = YookassaPayment.create(
            {
                "amount": {
                    "value": total_sum,
                    "currency": "RUB"
                },
                "payment_method_data": {
                    "type": "bank_card"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://1847-38-180-0-43.ngrok-free.app/payment/success"
                },
                "capture": True
            })
        await self.payment_repository.save_payment(initiator.id, payment.id)

        return payment.confirmation.confirmation_url

    async def calculate_total_sum(self, products_dto: list[ProductDTO]) -> float:
        total_sum = 0
        for dto in products_dto:
            product = await self.product_repository.get_product_by_id(id=dto.product_id)
            if product is None:
                raise HTTPException(status_code=404, detail='product with id ' + dto.id + ' not found')
            total_sum += product.price * dto.amount
        return total_sum

    async def refund_payment(self, payment_id: str):
        try:
            payment = YookassaPayment.find_one(payment_id)
        except:
            raise HTTPException(status_code=404, detail='your payment not found')

        if not payment.refundable:
            raise HTTPException(status_code=403, detail="your payment not refundable")

        return Refund.create({
            "amount": {
                "value": payment.amount.value,
                "currency": "RUB"
            },
            "payment_id": payment_id
        })

    async def cancel_payment(self, payment_id: str):
        try:
            payment = YookassaPayment.find_one(payment_id)
        except:
            raise HTTPException(status_code=404, detail='your payment not found')

        unique_key = str(uuid.uuid4())

        if payment.status == "waiting_for_capture":
            response = YookassaPayment.cancel(payment_id, unique_key)
            return response.json()
        else:
            message = (
                f"Платёж {payment_id} не может быть отменён, так как его статус: {payment.status}. "
                f"Вы можете оформить возврат, если платёж уже завершён.")

            raise HTTPException(status_code=403, detail=message)

    async def get_payment(self, payment_id):
        try:
            payment = YookassaPayment.find_one(payment_id)
        except:
            raise HTTPException(status_code=404, detail='your payment not found')

        return payment

    async def retry_payment(self, payment_id: str, user_id: str):
        try:
            payment_info = YookassaPayment.find_one(payment_id)
            payment_method_id = payment_info.payment_method.id
            value = payment_info.amount.value

            payment = YookassaPayment.create({
                "amount": {
                    "value": value,
                    "currency": "RUB"
                },
                "capture": True,
                "payment_method_id": payment_method_id,
                "description": "Автоматический платёж по подписке"
            })

            await self.payment_repository.save_payment(user_id, payment.id)
        except Exception as e:
            print(f"Ошибка при повторном выполнении платежа {payment_id}: {e}")

    async def handle_payment_status(self, request: Request):
        try:
            event_json = await request.json()
            notification = WebhookNotification(event_json)
            payment_id = notification.object.id
            amount = notification.object.amount.value
            payment = await self.payment_repository.find_payment_by_id(payment_id)
            initiator = await self.user_repository.find_user_by_id(payment.user_id)

            if notification.event == "payment.succeeded":
                return await self.handle_sucess(amount, initiator, payment_id)

            elif notification.event == "payment.canceled":
                return await self.handle_error(amount, initiator, notification, payment_id)

            else:
                raise HTTPException(status_code=400, detail="Invalid event")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def handle_error(self, amount, initiator, notification, payment_id):
        cancellation_reason = notification.object.cancellation_details.reason
        retry_time = datetime.now() + timedelta(days=1)
        scheduler.add_job(self.retry_payment, 'date', run_date=retry_time, args=[payment_id, initiator.id])
        await self.telegram_service.send_message(initiator.tg_id,
                                                 f"Платеж будет повторен через сутки. Причина: {cancellation_reason} ")
        return {"message": "Платеж будет повторно проведен через сутки", "payment_id": payment_id,
                "amount": amount}

    async def handle_sucess(self, amount, initiator, payment_id):
        retry_time = datetime.now() + timedelta(days=30)
        await self.telegram_service.send_message(initiator.tg_id, "Платеж выполнился")
        scheduler.add_job(self.retry_payment, 'date', run_date=retry_time, args=[payment_id, initiator.id])
        return {"message": "Payment succeeded", "payment_id": payment_id, "amount": amount}
