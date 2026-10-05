from dataclasses import dataclass, field


@dataclass
class Chunk:
    point_id: str
    user_id: int
    data_type: str
    article_id: int
    title: str
    chunk_index: int
    text: str
    category: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    source_id: int = 0        # 行为表主键，用于生成唯一 point_id
    extra: dict = field(default_factory=dict)