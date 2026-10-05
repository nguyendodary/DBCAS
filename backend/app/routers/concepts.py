from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentAccount
from ..models import Account
from ..schemas import ConceptGraphResult
from ..services import concept_graph_service

router = APIRouter(prefix="/concepts", tags=["concepts"])


@router.get("/graph", response_model=ConceptGraphResult)
def get_concept_graph(
    _: Account = CurrentAccount,
    db: Session = Depends(get_db),
):
    """The prerequisite skill graph: every concept node with its direct
    prerequisite ids, plus the raw prerequisite→dependent edge list."""
    return concept_graph_service.concept_graph(db)
