from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import APP_TITLE, APP_VERSION, BASE_DIR
from app.db import Base, SessionLocal, engine, get_db
from app.routers import admin, analytics, chat
from app.services.chatbot_service import refresh_engine, seed_faqs_if_needed

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_faqs_if_needed(db)
        refresh_engine(db)
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin-portal", response_class=HTMLResponse)
def admin_portal(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/health")
def health(db: Session = Depends(get_db)):
    _ = db.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(analytics.router)
