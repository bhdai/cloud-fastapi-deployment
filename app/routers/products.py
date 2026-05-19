# ==============================================================================
# Product CRUD Router + Image Upload
# ==============================================================================

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Product
from app.s3_service import delete_file_from_s3, upload_file_to_s3
from app.schemas import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])

# ── Upload constraints ────────────────────────────────────────────────────────
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.get("/", response_model=list[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    category_id: int | None = None,
    db: Session = Depends(get_db),
):
    """List products with optional category filter and pagination."""
    query = db.query(Product)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    return query.offset(skip).limit(limit).all()


@router.post(
    "/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED
)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
):
    """Update a product. Only provided fields are changed."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product. Cleans up its S3 image if one exists."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Best-effort S3 cleanup — don't block deletion if S3 fails.
    if product.image_url:
        try:
            delete_file_from_s3(product.image_url)
        except RuntimeError:
            pass  # Intentionally ignored: S3 cleanup is best-effort.

    db.delete(product)
    db.commit()


@router.post("/{product_id}/upload-image", response_model=ProductResponse)
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an image for a product, storing it in S3.

    Validates file type and size before uploading. Replaces any existing
    image (deleting the old one from S3).
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # ── Validate content type ─────────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '{file.content_type}' not allowed. "
                f"Allowed: {sorted(ALLOWED_CONTENT_TYPES)}"
            ),
        )

    # ── Validate file size ────────────────────────────────────────────────
    # Read content to check length, then reset for the actual upload.
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )
    file.file.seek(0)

    # ── Replace existing image ────────────────────────────────────────────
    if product.image_url:
        try:
            delete_file_from_s3(product.image_url)
        except RuntimeError:
            pass  # Intentionally ignored: old image cleanup is best-effort.

    # ── Upload to S3 ──────────────────────────────────────────────────────
    try:
        image_url = upload_file_to_s3(file)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image to S3",
        ) from e

    product.image_url = image_url
    db.commit()
    db.refresh(product)
    return product
