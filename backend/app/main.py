from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.matches import router as matches_router
from app.routers.postings import router as postings_router
from app.routers.resumes import router as resumes_router

app = FastAPI(title="역량 기반 채용공고 매칭 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(postings_router)
app.include_router(resumes_router)
app.include_router(matches_router)


@app.get("/")
def root():
    return {"message": "역량 기반 채용공고 매칭 API"}


@app.get("/health")
def health():
    return {"status": "ok"}
