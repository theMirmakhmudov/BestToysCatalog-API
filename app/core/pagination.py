from typing import Tuple
from fastapi import Query

def page_params(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)) -> Tuple[int, int]:
    return limit, offset
