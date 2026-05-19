# ==============================================================================
# FastAPI Application Entry Point
# ==============================================================================

from fastapi import FastAPI

from app.config import settings
from app.routers import categories, products

app = FastAPI(
    title=settings.app_name,
    description="A product catalog API with S3 file storage, deployed to AWS.",
    version="1.0.0",
)


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for monitoring and deployment verification."""
    return {"status": "healthy", "environment": settings.environment}


app.include_router(categories.router)
app.include_router(products.router)
