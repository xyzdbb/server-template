from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access-token"],
        description="JWT access token used for authenticated requests.",
    )
    refresh_token: str = Field(
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh-token"],
        description="JWT refresh token used to obtain a new access token.",
    )
    token_type: str = Field(default="bearer", examples=["bearer"])


class TokenPayload(BaseModel):
    sub: int | None = None
    type: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh-token"],
        description="Valid refresh token previously issued by the login endpoint.",
    )
