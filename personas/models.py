from pydantic import BaseModel, ConfigDict, Field

# Define the World model
class World(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str
    description: str

class Person(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str
    age: int = Field(..., gt=0)  # Ensures age is an integer greater than 0
    background: str
