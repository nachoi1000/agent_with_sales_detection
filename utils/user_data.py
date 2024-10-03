from pydantic import BaseModel, Field
from typing import Optional


class UserInformation(BaseModel):
    """Represents the structure of user nformation to be requested."""
    name: Optional[str] = Field(description="Name and or Last name of the user.")
    email: Optional[str] = Field(description="Email of the user.")
