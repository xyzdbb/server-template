from pydantic import BaseModel, Field

class ItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    title: str | None = None

class ItemResponse(ItemBase):
    id: int
    owner_id: int
    
    class Config:
        from_attributes = True