from dataclasses import dataclass


@dataclass
class Book:

    path: str
    name: str
    ext: str
    size: int