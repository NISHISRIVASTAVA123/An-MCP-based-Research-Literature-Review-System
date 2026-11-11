"""FastAPI routes for Search Strategy generation and inspection."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.services.persistence.database import get_db
from backend.app.services.persistence.repositories import (
    ResearchRequestRepository,
    StrategyRepository,
)
from backend.app.services.planner.strategy_generator import strategy_planner
from backend.app.schemas.search import (
    SearchStrategyResponse,
    SearchStrategyUpdate,
)

router = APIRouter(prefix="/api/research-requests", tags=["Search Strategy"])


@router.post("/{request_id}/strategy", response_model=SearchStrategyResponse, status_code=status.HTTP_201_CREATED)
def generate_strategy(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Generates and persists a structured academic search strategy for a research request."""
    req_repo = ResearchRequestRepository(db)
    strat_repo = StrategyRepository(db)

    req = req_repo.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Research request not found.")

    questions = [q.question_text for q in req.questions]
    dbs = req.preferred_databases or ["openalex", "semantic_scholar", "crossref", "arxiv"]

    # Generate strategy plan
    plan = strategy_planner.generate(
        topic=req.topic,
        objective=req.objective,
        domain=req.domain,
        research_questions=questions,
        preferred_databases=dbs,
    )

    strategy = strat_repo.create_or_update(
        request_id=req.id,
        concepts=plan["concepts"],
        keywords=plan["keywords"],
        synonyms=plan["synonyms"],
        query_combinations=plan["query_combinations"],
        queries=plan["queries"],
    )

    return strategy


@router.get("/{request_id}/strategy", response_model=SearchStrategyResponse)
def get_strategy(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves the current search strategy and queries for a research request."""
    strat_repo = StrategyRepository(db)
    strategy = strat_repo.get_by_request_id(request_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="No search strategy found for this request. Generate one first.")
    return strategy


@router.put("/{request_id}/strategy", response_model=SearchStrategyResponse)
def update_strategy(
    request_id: str,
    payload: SearchStrategyUpdate,
    db: Session = Depends(get_db),
):
    """Allows user to inspect, modify keywords, and edit database-specific search queries."""
    strat_repo = StrategyRepository(db)
    strategy = strat_repo.get_by_request_id(request_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Search strategy not found.")

    # Update metadata fields if provided
    if payload.concepts is not None:
        strategy.concepts = payload.concepts
    if payload.keywords is not None:
        strategy.keywords = payload.keywords
    if payload.synonyms is not None:
        strategy.synonyms = payload.synonyms
    if payload.query_combinations is not None:
        strategy.query_combinations = payload.query_combinations

    # Update queries if provided
    if payload.queries is not None:
        queries_data = [q.model_dump() for q in payload.queries]
        strat_repo.update_queries(strategy.id, queries_data)
    else:
        db.commit()

    return strat_repo.get_by_request_id(request_id)

