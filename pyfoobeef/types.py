from typing import List, Tuple, Union, Set, Dict
from .models import PlaylistInfo, FileSystemEntry

PlaylistRef = Union[str, int, PlaylistInfo]
Paths = Union[
    List[Union[str, FileSystemEntry]], Tuple[List[Union[str, FileSystemEntry]]]
]
ItemIndices = Union[List[int], Tuple[int]]
ColumnsMap = Union[Dict[str, str], Set[str], List[str], Tuple[str]]
