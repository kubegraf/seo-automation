import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
from typing import List, TypeVar, Type, Optional
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> list:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {filename}: {e}")
        return []
    except IOError as e:
        logger.error(f"Failed to read {filename}: {e}")
        return []


def _save_json(filename: str, data: list) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def load_all(filename: str, model_class: Type[T]) -> List[T]:
    raw = _load_json(filename)
    result = []
    for item in raw:
        try:
            result.append(model_class(**item))
        except Exception as e:
            logger.warning(f"Skipping malformed record in {filename}: {e}")
    return result


def save_all(filename: str, items: List[BaseModel]) -> None:
    _save_json(filename, [item.model_dump() for item in items])


def upsert(filename: str, item: BaseModel, model_class: Type[T]) -> None:
    items = load_all(filename, model_class)
    item_id = getattr(item, 'id', None)
    matched = any(getattr(i, 'id', None) == item_id for i in items)
    if matched:
        items = [item if getattr(i, 'id', None) == item_id else i for i in items]
    else:
        items.append(item)
    save_all(filename, items)


def find_by_id(filename: str, item_id: str, model_class: Type[T]) -> Optional[T]:
    for item in load_all(filename, model_class):
        if getattr(item, 'id', None) == item_id:
            return item
    return None


def find_by_field(filename: str, field: str, value, model_class: Type[T]) -> List[T]:
    items = load_all(filename, model_class)
    return [i for i in items if getattr(i, field, None) == value]


# Convenience functions
def load_articles():
    from shared.models import Article
    return load_all("articles.json", Article)


def save_articles(articles):
    save_all("articles.json", articles)


def load_keywords():
    from shared.models import Keyword
    return load_all("keywords.json", Keyword)


def save_keywords(keywords):
    save_all("keywords.json", keywords)


def load_competitors():
    from shared.models import Competitor
    return load_all("competitors.json", Competitor)


def save_competitors(competitors):
    save_all("competitors.json", competitors)


def load_reports():
    from shared.models import SEOReport
    return load_all("seo_reports.json", SEOReport)


def save_reports(reports):
    save_all("seo_reports.json", reports)
