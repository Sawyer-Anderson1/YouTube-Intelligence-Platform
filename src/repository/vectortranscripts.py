from pymongo.collection import Collection
from typing import Optional, List, Dict


class ResultsRepository:
    def __init__(self, collection: Collection):
            self.collection = collection

    def get_results(self, query_type: Optional[str] = None, limit: int = 5) -> List[Dict]:
        query_filter = {}
        if query_type:
            query_filter["query_type"] = query_type

        return list(
            self.collection
            .find(query_filter, {"_id": 0})
            .sort("run_date", -1)
            .limit(limit)
        )

    def get_by_type(self, query_type: str, limit: int = 5) -> List[Dict]:
        return list(
            self.collection
            .find({"query_type": query_type}, {"_id": 0})
            .sort("run_date", -1)
            .limit(limit)
        )