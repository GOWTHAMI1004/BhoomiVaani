import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api import routes_lands, routes_ai, routes_claims, routes_documents, routes_investigate
from app.services.land_service import land_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bhoomivaani")

app = FastAPI(
    title="BhoomiVaani API",
    description="AI-powered Voice-First Land Intelligence and Legal Awareness Platform for Indian Land Buyers",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for seamless development and codespaces
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(routes_lands.router)
app.include_router(routes_ai.router)
app.include_router(routes_claims.router)
app.include_router(routes_documents.router)
app.include_router(routes_investigate.router)

@app.get("/api/health")
def health_check():
    stats = land_service.get_stats()
    return {
        "status": "healthy",
        "service": "BhoomiVaani API",
        "version": "1.0.0",
        "mock_mode": settings.mock_mode,
        "default_language": settings.default_language,
        "gnani_models": {
            "stt": "Gnani Prisma v2.5",
            "reasoning": "Gnani Evon v3.3 30B (gnani-evon-v3.3-30b-a3b)",
            "tts": "Gnani Timbre v2.5"
        },
        "database": {
            "total_properties": stats.get("total_properties", 0),
            "clean_properties": stats.get("clean_document_examples", 0),
            "risk_flagged_properties": stats.get("risk_flagged_properties", 0)
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception at {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting BhoomiVaani backend server on {settings.backend_host}:{settings.backend_port}")
    uvicorn.run("app.main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
