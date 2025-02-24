from sqlalchemy.future import select
from typing import Optional

from app.domain import models
from app.infrastructure.db.CreateSession import get_db


class UserRepository:
    async def find_user_by_id(self, id: int) -> Optional[models.User]:
        async for db in get_db():
            result = await db.execute(select(models.User).filter(models.User.id == id))
            user = result.scalars().first()
            return user


class ProductRepository:
    async def get_product_by_id(self, id: int) -> Optional[models.Product]:
        async for db in get_db():
            result = await db.execute(select(models.Product).filter(models.Product.id == id))
            product = result.scalars().first()
            return product

class PaymentRepository:
    async def find_payment_by_id(self, id: str) -> Optional[models.Payment]:
        async for db in get_db():
            result = await db.execute(select(models.Payment)
                                      .filter(models.Payment.id == id))
            payment = result.scalars().first()
            return payment

    async def save_payment(self, initiator_id: int, payment_id: str) -> None:
        async for db in get_db():
            new_payment = models.Payment(id=payment_id, user_id=initiator_id)
            db.add(new_payment)
            await db.commit()
