from app.schemas.common import ErrorResponse

UNAUTHORIZED_RESPONSE = {
    "model": ErrorResponse,
    "description": "Authentication required or access token is invalid.",
    "content": {
        "application/json": {
            "example": {"detail": "Could not validate credentials"},
        }
    },
}

FORBIDDEN_RESPONSE = {
    "model": ErrorResponse,
    "description": "Authenticated user does not have permission to access this resource.",
    "content": {
        "application/json": {
            "example": {"detail": "Not enough privileges"},
        }
    },
}

NOT_FOUND_RESPONSE = {
    "model": ErrorResponse,
    "description": "Requested resource was not found.",
    "content": {
        "application/json": {
            "example": {"detail": "Item not found"},
        }
    },
}

BAD_REQUEST_RESPONSE = {
    "model": ErrorResponse,
    "description": "Request is syntactically valid but violates business rules.",
    "content": {
        "application/json": {
            "examples": {
                "invalid_credentials": {
                    "summary": "Invalid login credentials",
                    "value": {"detail": "Incorrect email or password"},
                },
                "inactive_user": {
                    "summary": "Inactive user",
                    "value": {"detail": "Inactive user"},
                },
            }
        }
    },
}

UNPROCESSABLE_ENTITY_RESPONSE = {
    "description": "Request validation failed.",
    "content": {
        "application/json": {
            "example": {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["body", "password"],
                        "msg": "String should have at least 8 characters",
                        "input": "123",
                    }
                ]
            }
        }
    },
}

CONFLICT_RESPONSE = {
    "model": ErrorResponse,
    "description": "Requested operation conflicts with current resource state.",
    "content": {
        "application/json": {
            "example": {"detail": "Email already registered"},
        }
    },
}
