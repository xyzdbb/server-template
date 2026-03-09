from fastapi import APIRouter, HTTPException
from app.api.deps import SessionDep, CurrentUser
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.crud import item_crud
from app.services import create_item, get_user_items

router = APIRouter()

@router.post("/", response_model=ItemResponse, status_code=201)
def create_new_item(session: SessionDep, current_user: CurrentUser, item_in: ItemCreate):
    item = create_item(session, item_in, current_user)
    return item

@router.get("/", response_model=list[ItemResponse])
def read_items(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100):
    items = get_user_items(session, current_user.id, skip, limit)
    return items

@router.get("/{item_id}", response_model=ItemResponse)
def read_item(session: SessionDep, current_user: CurrentUser, item_id: int):
    item = item_crud.get(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return item

@router.put("/{item_id}", response_model=ItemResponse)
def update_item(session: SessionDep, current_user: CurrentUser, item_id: int, item_in: ItemUpdate):
    item = item_crud.get(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    update_data = item_in.model_dump(exclude_unset=True)
    item = item_crud.update(session, item, update_data)
    return item