from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from flask import abort

from db import db, get_next_sequence


class BaseModel:
    collection: str = ""
    fields: List[str] = []

    def __init__(self, **kwargs: Any) -> None:
        for field in self.fields:
            setattr(self, field, kwargs.get(field))

    @classmethod
    def _col(cls):
        return db[cls.collection]

    @classmethod
    def from_doc(cls, doc: Optional[Dict[str, Any]]) -> Optional["BaseModel"]:
        if not doc:
            return None
        data = {field: doc.get(field) for field in cls.fields}
        return cls(**data)

    def to_doc(self) -> Dict[str, Any]:
        return {field: getattr(self, field) for field in self.fields}

    @classmethod
    def find(cls, filter_doc: Optional[Dict[str, Any]] = None, sort: Optional[List] = None, limit: Optional[int] = None):
        cursor = cls._col().find(filter_doc or {})
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(int(limit))
        return [cls.from_doc(doc) for doc in cursor]

    @classmethod
    def find_one(cls, filter_doc: Optional[Dict[str, Any]] = None, sort: Optional[List] = None):
        if sort:
            cursor = cls._col().find(filter_doc or {}).sort(sort).limit(1)
            for doc in cursor:
                return cls.from_doc(doc)
            return None
        return cls.from_doc(cls._col().find_one(filter_doc or {}))

    @classmethod
    def count(cls, filter_doc: Optional[Dict[str, Any]] = None) -> int:
        return int(cls._col().count_documents(filter_doc or {}))

    @classmethod
    def get_or_404(cls, id_value: int):
        try:
            id_int = int(id_value)
        except Exception:
            abort(404)
            return None
        doc = cls._col().find_one({"id": id_int})
        if not doc:
            abort(404)
        return cls.from_doc(doc)

    @classmethod
    def find_by_ids(cls, ids: Iterable[int]) -> List["BaseModel"]:
        id_list = [int(i) for i in ids]
        if not id_list:
            return []
        docs = cls._col().find({"id": {"$in": id_list}})
        return [cls.from_doc(doc) for doc in docs]

    @classmethod
    def aggregate(cls, pipeline: List[Dict[str, Any]]):
        return list(cls._col().aggregate(pipeline))

    def save(self):
        if getattr(self, "id", None) is None:
            setattr(self, "id", get_next_sequence(self.collection))
        if getattr(self, "created_at", None) is None and "created_at" in self.fields:
            setattr(self, "created_at", datetime.utcnow())
        self.__class__._col().update_one({"id": self.id}, {"$set": self.to_doc()}, upsert=True)
        return self

    def delete(self):
        if getattr(self, "id", None) is None:
            return
        self.__class__._col().delete_one({"id": self.id})


class Admin(BaseModel):
    collection = "admins"
    fields = ["id", "username", "password_hash", "created_at"]


class Artwork(BaseModel):
    collection = "artworks"
    fields = ["id", "title", "description", "image_filename", "hashtags", "status", "created_at"]

    @classmethod
    def random(cls, limit: int):
        pipeline = [{"$sample": {"size": int(limit)}}]
        docs = cls._col().aggregate(pipeline)
        return [cls.from_doc(doc) for doc in docs]


class PurchaseRequest(BaseModel):
    collection = "purchase_requests"
    fields = [
        "id",
        "full_name",
        "phone_number",
        "email",
        "artwork_id",
        "artwork_title_snapshot",
        "message",
        "status",
        "created_at",
    ]


class Visit(BaseModel):
    collection = "visits"
    fields = ["id", "path", "ip", "user_agent", "created_at"]


class ArtworkView(BaseModel):
    collection = "artwork_views"
    fields = ["id", "artwork_id", "created_at"]
