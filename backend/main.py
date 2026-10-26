from contextlib import asynccontextmanager
import os
import sqlite3
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend.database import (
    add_fact,
    add_rule,
    create_review,
    decide_review,
    get_policy,
    get_review,
    initialize_database,
    list_reviews,
)
from backend.rules_engine import review_content


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="BrandLens API",
    description="Explainable brand governance and content review",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(
    os.environ.get(
        "BRANDLENS_FRONTEND_DIST",
        str(Path(__file__).resolve().parent.parent / "frontend" / "dist"),
    )
)


class ReviewRequest(BaseModel):
    title: str = Field(default="Untitled draft", max_length=120)
    content: str = Field(..., min_length=1, max_length=20000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Draft content cannot be blank.")
        return value


class PolicyTermRequest(BaseModel):
    term: str = Field(..., min_length=1, max_length=120)

    @field_validator("term")
    @classmethod
    def term_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Banned terms must contain at least two characters.")
        return value


class PolicyFactRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)

    @field_validator("text")
    @classmethod
    def fact_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 8:
            raise ValueError("Approved facts must contain at least eight characters.")
        return value


class ReviewDecisionRequest(BaseModel):
    decision: Literal["approved", "changes_requested"]
    note: str = Field(default="", max_length=1000)


@app.get("/", response_model=None)
def home() -> dict[str, str] | FileResponse:
    index_file = FRONTEND_DIST / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {"message": "BrandLens API is running", "status": "success"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/policy")
def policy() -> dict[str, list[dict[str, str]]]:
    return get_policy()


@app.post("/api/policy/rules", status_code=201)
def create_policy_rule(request: PolicyTermRequest) -> dict[str, str]:
    try:
        return add_rule(request.term)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="That banned term already exists.") from error


@app.post("/api/policy/facts", status_code=201)
def create_policy_fact(request: PolicyFactRequest) -> dict[str, str]:
    try:
        return add_fact(request.text)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="That approved fact already exists.") from error


@app.post("/api/reviews", status_code=201)
def submit_review(request: ReviewRequest) -> dict[str, Any]:
    policy_data = get_policy()
    result = review_content(
        request.content,
        banned_terms=policy_data["rules"],
        approved_facts=policy_data["facts"],
    )
    review = create_review(
        request.title,
        request.content,
        result["findings"],
    )
    review["review_note"] = result["review_note"]
    return review


@app.get("/api/reviews")
def reviews() -> dict[str, list[dict[str, Any]]]:
    return {"reviews": list_reviews()}


@app.get("/api/reviews/{review_id}")
def review_detail(review_id: int) -> dict[str, Any]:
    review = get_review(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return review


@app.patch("/api/reviews/{review_id}/decision")
def review_decision(
    review_id: int, request: ReviewDecisionRequest
) -> dict[str, Any]:
    review = decide_review(review_id, request.decision, request.note)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return review


@app.post("/review")
def legacy_review(request: ReviewRequest) -> dict[str, Any]:
    policy_data = get_policy()
    return review_content(
        request.content,
        banned_terms=policy_data["rules"],
        approved_facts=policy_data["facts"],
    )


if FRONTEND_DIST.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIST, html=True),
        name="frontend",
    )
