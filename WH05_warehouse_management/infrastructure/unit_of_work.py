from domain.unit_of_work import UnitOfWork

class SqlAlchemyUnitOfWork(UnitOfWork):

    def __init__(self, session):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, traceback):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass
