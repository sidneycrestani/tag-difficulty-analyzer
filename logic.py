# logic.py

import statistics
from aqt import mw

def get_parent_tags(max_depth: int = 3) -> list:
    """Gets a list of all parent tags in the collection."""
    parent_tags_set = set()
    for tag in mw.col.tags.all():
        components = tag.split('::')
        for i in range(1, len(components)):
            if i > max_depth: break
            parent_prefix = "::".join(components[:i])
            parent_tags_set.add(parent_prefix)
    return sorted(list(parent_tags_set))

def convert_ease_to_difficulty(ease_factor: float) -> float:
    MIN_EASE = 1.30; BASE_EASE = 2.50
    if ease_factor >= BASE_EASE: return 0.0
    if ease_factor <= MIN_EASE: return 100.0
    return ((BASE_EASE - ease_factor) / (BASE_EASE - MIN_EASE)) * 100.0

def calculate_tag_difficulties(parent_tag: str) -> list:
    parent_components = parent_tag.split('::')
    grouping_depth = len(parent_components) + 1
    tag_search = f'tag:"{parent_tag}" or tag:"{parent_tag}::*"'
    search_query = f"({tag_search}) -is:suspended"
    card_ids = mw.col.find_cards(search_query)
    if not card_ids: return []
    results = {}
    for cid in card_ids:
        card = mw.col.get_card(cid)
        note = card.note()
        if not note: continue
        difficulty, metric = 0.0, ""
        if card.memory_state:
            metric = "FSRS"
            fsrs_d = card.memory_state.difficulty
            if fsrs_d > 0:
                difficulty = (fsrs_d - 1) / 9.0 * 100.0
            else: continue
        elif card.factor > 0:
            metric = "Ease-Based"
            difficulty = convert_ease_to_difficulty(card.factor / 1000.0)
        else: continue
        grouping_keys_for_this_card = set()
        for card_tag in note.tags:
            if not card_tag.lower().startswith(parent_tag.lower()): continue
            card_components = card_tag.split('::')
            if len(card_components) < grouping_depth: continue

            # --- FIX: Convert the grouping key to lowercase for case-insensitive grouping ---
            grouping_key = "::".join(card_components[:grouping_depth]).lower()
            
            grouping_keys_for_this_card.add(grouping_key)
        for key in grouping_keys_for_this_card:
            if key not in results:
                results[key] = {"difficulties": [], "metrics": set()}
            results[key]["difficulties"].append(difficulty)
            results[key]["metrics"].add(metric)
    final_results = []
    for tag, data in results.items():
        if not data["difficulties"]: continue
        median_difficulty = statistics.median(data["difficulties"])
        final_results.append({
            "tag": tag, "difficulty": median_difficulty, "card_count": len(data["difficulties"]),
            "metric_used": "/".join(sorted(list(data["metrics"])))
        })
    final_results.sort(key=lambda x: x["difficulty"], reverse=True)
    return final_results