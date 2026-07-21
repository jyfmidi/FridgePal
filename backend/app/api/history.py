from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.application.history.service import list_history, undo_activity
from app.auth.service import UserContext


class UndoRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=120)


def build_history_router(session_provider, current_user) -> APIRouter:
    api = APIRouter()

    @api.get("/history")
    def list_events(
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
    ) -> dict[str, list[dict[str, object]]]:
        events = list_history(session, user.user_id, limit)
        return {"events": events}

    @api.post("/history/{event_id}/undo")
    def undo(
        event_id: str,
        payload: UndoRequest,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        try:
            return undo_activity(session, user.user_id, event_id, payload.idempotency_key)
        except ValueError as error:
            session.rollback()
            msg = str(error)
            if msg == "event not found":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from error
            if msg == "event type is not reversible":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg) from error
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg) from error

    return api
