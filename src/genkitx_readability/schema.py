from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class ReadabilityResult:
    url: str
    title: Optional[str]
    author: Optional[str]
    publish_date: Optional[str]
    language: Optional[str]
    text: str
    html: Optional[str]
    excerpt: Optional[str]
    top_image: Optional[str]
    images: List[str]

    def to_dict(self):
        return asdict(self)
