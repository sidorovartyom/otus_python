from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from domain.services import WarehouseService
from infrastructure.orm import Base
from infrastructure.repositories import SqlAlchemyProductRepository, SqlAlchemyOrderRepository
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from infrastructure.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def main():
    session = SessionFactory()
    product_repo = SqlAlchemyProductRepository(session)
    order_repo = SqlAlchemyOrderRepository(session)

    uow = SqlAlchemyUnitOfWork(session)

    warehouse_service = WarehouseService(product_repo, order_repo)
    with uow:
        new_product = warehouse_service.create_product(name="test1", quantity=1, price=100)
        uow.commit()
        print(f"create product: {new_product}")

        # Создаем еще один товар
        product2 = warehouse_service.create_product(name="test2", quantity=5, price=200)
        uow.commit()
        print(f"create product: {product2}")

        # Создаем заказ с товарами
        order = warehouse_service.create_order(products=[new_product, product2])
        uow.commit()
        print(f"create order: {order}")

        # Получаем список всех товаров
        all_products = product_repo.list()
        print(f"Total products: {len(all_products)}")

        # Получаем список всех заказов
        all_orders = order_repo.list()
        print(f"Total orders: {len(all_orders)}")


if __name__ == "__main__":
    main()
