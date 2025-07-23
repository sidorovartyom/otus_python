import hashlib
import json
from datetime import datetime
from typing import Optional

def get_score(
    store, 
    phone: Optional[str] = None, 
    email: Optional[str] = None, 
    birthday: Optional[datetime] = None, 
    gender: Optional[int] = None, 
    first_name: Optional[str] = None, 
    last_name: Optional[str] = None
) -> float:
    key_parts = [
        first_name or "",
        last_name or "",
        phone or "",
        birthday.strftime("%Y%m%d") if birthday else "",
    ]
    key = "uid:" + hashlib.md5("".join(key_parts).encode('utf-8')).hexdigest()
    
    # Try to get from cache
    try:
        score = store.cache_get(key)
        if score is not None:
            return float(score)
    except Exception:
        # Если кеш недоступен, продолжаем без него
        pass
    
    # Calculate score
    score = 0.0
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender is not None:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    
    # Cache the score for 60 minutes
    try:
        store.cache_set(key, score, 60 * 60)
    except Exception:
        # Если кеш недоступен, игнорируем ошибку
        pass
    
    return score

def get_interests(store, cid: str) -> list:
    try:
        r = store.get(f"i:{cid}")
        if r:
            try:
                return json.loads(r)
            except (json.JSONDecodeError, ValueError):
                # Если JSON некорректный, возвращаем пустой список
                return []
        return []
    except Exception:
        # Если хранилище недоступно, возвращаем пустой список
        return []
