from typing import List, Tuple, Union, Set, Dict
from .models import PlaylistInfo

PlaylistRef = Union[str, int, PlaylistInfo]
Paths = Union[List[str], Tuple[str]]
ItemIndices = Union[List[int], Tuple[int]]
ColumnsMap = Union[Dict[str, str], Set[str], List[str], Tuple[str]]
