from typing import Annotated

from fastapi import Query

LimitDep = Annotated[int, Query(ge=1, le=100, description="Max number of records to return")]
OffsetDep = Annotated[int, Query(ge=0, description="Number of records to skip")]
