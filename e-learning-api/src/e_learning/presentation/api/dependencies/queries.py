"""Câblage des ports de lecture vers leurs adaptateurs SQLAlchemy."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from e_learning.application.catalog.queries import CatalogQueryPort
from e_learning.application.learning.queries import LearningQueryPort
from e_learning.application.usage.queries import UsageQueryPort
from e_learning.infrastructure.persistence.catalog.queries import SqlAlchemyCatalogQueryService
from e_learning.infrastructure.persistence.learning.queries import SqlAlchemyLearningQueryService
from e_learning.infrastructure.persistence.usage.queries import SqlAlchemyUsageQueryService
from e_learning.presentation.api.dependencies.session import SessionDep


def get_catalog_queries(session: SessionDep) -> CatalogQueryPort:
    return SqlAlchemyCatalogQueryService(session)


def get_learning_queries(session: SessionDep) -> LearningQueryPort:
    return SqlAlchemyLearningQueryService(session)


def get_usage_queries(session: SessionDep) -> UsageQueryPort:
    return SqlAlchemyUsageQueryService(session)


CatalogQueryDep = Annotated[CatalogQueryPort, Depends(get_catalog_queries)]
LearningQueryDep = Annotated[LearningQueryPort, Depends(get_learning_queries)]
UsageQueryDep = Annotated[UsageQueryPort, Depends(get_usage_queries)]
