import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def test_unit_of_work_initialization():
    # Arrange
    session = Mock(spec=Session)
    
    # Act
    uow = SqlAlchemyUnitOfWork(session)
    
    # Assert
    assert uow.session == session


def test_unit_of_work_enter_exit_success():
    # Arrange
    session = Mock(spec=Session)
    uow = SqlAlchemyUnitOfWork(session)
    
    # Act
    with uow as context_uow:
        assert context_uow == uow
    
    # Assert
    session.commit.assert_called_once()
    session.rollback.assert_not_called()


def test_unit_of_work_enter_exit_with_exception():
    # Arrange
    session = Mock(spec=Session)
    uow = SqlAlchemyUnitOfWork(session)
    
    # Act & Assert
    with pytest.raises(ValueError):
        with uow:
            raise ValueError("Test exception")
    
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_unit_of_work_commit():
    # Arrange
    session = Mock(spec=Session)
    uow = SqlAlchemyUnitOfWork(session)
    
    # Act
    uow.commit()
    
    # Assert
    session.commit.assert_called_once()


def test_unit_of_work_rollback():
    # Arrange
    session = Mock(spec=Session)
    uow = SqlAlchemyUnitOfWork(session)
    
    # Act
    uow.rollback()
    
    # Assert
    session.rollback.assert_called_once() 