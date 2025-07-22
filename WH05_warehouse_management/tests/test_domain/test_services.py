from unittest.mock import Mock
from domain.services import WarehouseService
from domain.models import Product, Order


def test_create_product():
    # Arrange
    product_repo = Mock()
    order_repo = Mock()
    service = WarehouseService(product_repo, order_repo)
    
    # Act
    product = service.create_product(name="Тест", quantity=10, price=100.0)
    
    # Assert
    assert product.name == "Тест"
    assert product.quantity == 10
    assert product.price == 100.0
    product_repo.add.assert_called_once_with(product)


def test_create_order():
    # Arrange
    product_repo = Mock()
    order_repo = Mock()
    service = WarehouseService(product_repo, order_repo)
    products = [
        Product(id=1, name="Товар1", quantity=5, price=100.0),
        Product(id=2, name="Товар2", quantity=3, price=200.0)
    ]
    
    # Act
    order = service.create_order(products=products)
    
    # Assert
    assert len(order.products) == 2
    assert order.products[0].name == "Товар1"
    assert order.products[1].name == "Товар2"
    order_repo.add.assert_called_once_with(order)
