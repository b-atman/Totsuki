"""
Name normalization utilities for receipt ingestion.

This module handles converting messy receipt text into canonical names
that can be matched against pantry items.

Example transformations:
    "GREAT VALUE 2% MILK 1GAL" → "milk"
    "BNLS SKNLS CHKN BRST"     → "chicken breast"
    "ORG BABY SPINACH 5OZ"     → "baby spinach"
"""

import re
from difflib import SequenceMatcher
from typing import Optional


# Common brand names to strip from receipt items
BRAND_NAMES = {
    # Full brand names
    "great value", "kirkland", "signature select", "kroger", "safeway",
    "trader joes", "trader joe's", "whole foods", "365", "market pantry",
    "good gather", "simply balanced", "o organics", "open nature",
    "private selection", "simple truth", "essential everyday",
    "store brand", "generic", "house brand",
    # Additional brands
    "kraft", "heinz", "nestle", "kelloggs", "general mills", "campbells",
    "del monte", "dole", "chiquita", "tyson", "perdue", "oscar mayer",
    "land o lakes", "sargento", "tillamook", "cabot", "horizon",
    "stonyfield", "chobani", "fage", "oikos", "yoplait", "dannon",
    # Brand abbreviations commonly seen on receipts
    "gv", "kk", "ss", "mp", "gg", "st", "ee",
}

# Common abbreviations found on receipts
ABBREVIATIONS = {
    "chkn": "chicken",
    "brst": "breast",
    "bnls": "boneless",
    "sknls": "skinless",
    "org": "organic",
    "whl": "whole",
    "grnd": "ground",
    "frsh": "fresh",
    "frzn": "frozen",
    "lg": "large",
    "sm": "small",
    "med": "medium",
    "slcd": "sliced",
    "shrd": "shredded",
    "dcd": "diced",
    "ctg": "cottage",
    "chs": "cheese",
    "chse": "cheese",
    "crm": "cream",
    "bttr": "butter",
    "yog": "yogurt",
    "ygrt": "yogurt",
    "veg": "vegetable",
    "vegs": "vegetables",
    "tom": "tomato",
    "toms": "tomatoes",
    "pot": "potato",
    "pots": "potatoes",
    "oni": "onion",
    "gar": "garlic",
    "pep": "pepper",
    "grn": "green",
    "rd": "red",
    "wht": "white",
    "brn": "brown",
    "blk": "black",
    "sug": "sugar",
    "flr": "flour",
    "brd": "bread",
    "rce": "rice",
    "pst": "pasta",
    "sce": "sauce",
    "jce": "juice",
    "mlk": "milk",
    "eg": "egg",
    "egs": "eggs",
    "bf": "beef",
    "prk": "pork",
    "trky": "turkey",
    "slmn": "salmon",
    "tna": "tuna",
    "shrmp": "shrimp",
    "appl": "apple",
    "appls": "apples",
    "orng": "orange",
    "orngs": "oranges",
    "bana": "banana",
    "banas": "bananas",
    "strw": "strawberry",
    "strws": "strawberries",
    "blueb": "blueberry",
    "bluebs": "blueberries",
    "lett": "lettuce",
    "spin": "spinach",
    "broc": "broccoli",
    "caul": "cauliflower",
    "carr": "carrot",
    "carrs": "carrots",
    "cel": "celery",
    "cucu": "cucumber",
    "cucus": "cucumbers",
    "musr": "mushroom",
    "musrs": "mushrooms",
    "avoc": "avocado",
    "avocs": "avocados",
}

# Size/quantity descriptors to remove (they don't help with matching)
SIZE_PATTERNS = [
    r"\b\d+(\.\d+)?\s*(oz|lb|lbs|kg|g|gal|qt|pt|ct|pk|pc|pcs|ea|ml|l|fl)\b",
    r"\b\d+\s*(pack|count|piece|pieces)\b",
    r"\b(x-?large|xlarge|xl|x-?small|xsmall|xs)\b",
    r"\b(family|value|bulk|economy)\s*(size|pack)?\b",
]

# Words to remove (don't contribute to item identity)
NOISE_WORDS = {
    "organic", "natural", "fresh", "frozen", "canned", "dried",
    "raw", "cooked", "ready", "instant", "quick",
    "low", "reduced", "free", "lite", "light", "fat", "sodium", "sugar",
    "boneless", "skinless", "bone-in", "skin-on",
    "sliced", "diced", "chopped", "minced", "shredded", "grated",
    "whole", "half", "quarter",
    "premium", "select", "choice", "prime",
    "imported", "domestic", "local",
    "usda", "grade", "certified",
}


def normalize_item_name(raw_name: str, keep_descriptors: bool = False) -> str:
    """
    Convert a raw receipt item name to a normalized canonical form.
    
    Args:
        raw_name: The original item name from receipt (e.g., "GV 2% MILK 1GAL")
        keep_descriptors: If True, keeps words like "organic", "boneless"
    
    Returns:
        Normalized name (e.g., "milk")
    
    Examples:
        >>> normalize_item_name("GREAT VALUE 2% MILK 1GAL")
        'milk'
        >>> normalize_item_name("BNLS SKNLS CHKN BRST 2LB")
        'chicken breast'
        >>> normalize_item_name("ORG BABY SPINACH", keep_descriptors=True)
        'organic baby spinach'
    """
    if not raw_name:
        return ""
    
    # Lowercase for consistent processing
    name = raw_name.lower().strip()
    
    # Remove brand names (whole word match only)
    for brand in BRAND_NAMES:
        # Use word boundary to avoid matching substrings (e.g., "ee" in "cheese")
        name = re.sub(r"\b" + re.escape(brand) + r"\b", " ", name)
    
    # Remove size/quantity patterns
    for pattern in SIZE_PATTERNS:
        name = re.sub(pattern, " ", name, flags=re.IGNORECASE)
    
    # Remove percentage patterns (2%, 1%, etc.)
    name = re.sub(r"\b\d+%\b", " ", name)
    
    # Remove standalone numbers
    name = re.sub(r"\b\d+\b", " ", name)
    
    # Split into words for processing
    words = name.split()
    
    # Expand abbreviations
    expanded_words = []
    for word in words:
        clean_word = re.sub(r"[^a-z]", "", word)
        if clean_word in ABBREVIATIONS:
            expanded_words.append(ABBREVIATIONS[clean_word])
        elif clean_word:
            expanded_words.append(clean_word)
    
    # Remove noise words unless keeping descriptors
    if not keep_descriptors:
        expanded_words = [w for w in expanded_words if w not in NOISE_WORDS]
    
    # Join and clean up
    result = " ".join(expanded_words)
    
    # Remove extra whitespace
    result = re.sub(r"\s+", " ", result).strip()
    
    return result


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity score between two item names.
    
    Uses SequenceMatcher for fuzzy matching, which handles
    typos and minor variations well.
    
    Args:
        name1: First item name (should be normalized)
        name2: Second item name (should be normalized)
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not name1 or not name2:
        return 0.0
    
    # Direct match
    if name1 == name2:
        return 1.0
    
    # Check if one contains the other (partial match)
    if name1 in name2 or name2 in name1:
        shorter = min(len(name1), len(name2))
        longer = max(len(name1), len(name2))
        return shorter / longer * 0.9  # Slightly penalize partial matches
    
    # Fuzzy matching using SequenceMatcher
    return SequenceMatcher(None, name1, name2).ratio()


def find_best_match(
    receipt_name: str,
    pantry_items: list[dict],
    threshold: float = 0.6,
) -> Optional[dict]:
    """
    Find the best matching pantry item for a receipt item name.
    
    Args:
        receipt_name: Raw item name from receipt
        pantry_items: List of pantry items with 'name' and 'canonical_name' fields
        threshold: Minimum similarity score to consider a match (0.0 to 1.0)
    
    Returns:
        Best matching pantry item dict, or None if no match above threshold
    
    Example:
        >>> items = [{"id": 1, "name": "Whole Milk", "canonical_name": "milk"}]
        >>> find_best_match("2% MILK 1GAL", items)
        {"id": 1, "name": "Whole Milk", "canonical_name": "milk", "score": 1.0}
    """
    if not receipt_name or not pantry_items:
        return None
    
    normalized_receipt = normalize_item_name(receipt_name)
    
    if not normalized_receipt:
        return None
    
    best_match = None
    best_score = 0.0
    
    for item in pantry_items:
        # Try matching against canonical_name first (preferred)
        canonical = item.get("canonical_name") or ""
        if canonical:
            canonical_normalized = canonical.lower().strip()
            score = calculate_similarity(normalized_receipt, canonical_normalized)
            if score > best_score:
                best_score = score
                best_match = item
        
        # Also try matching against display name
        display_name = item.get("name") or ""
        if display_name:
            display_normalized = normalize_item_name(display_name)
            score = calculate_similarity(normalized_receipt, display_normalized)
            if score > best_score:
                best_score = score
                best_match = item
    
    if best_score >= threshold and best_match:
        return {**best_match, "match_score": best_score}
    
    return None


def suggest_canonical_name(raw_name: str) -> str:
    """
    Suggest a canonical name for a new pantry item.
    
    This is used when creating new items from receipts to
    auto-populate the canonical_name field.
    
    Args:
        raw_name: The display name entered by user or from receipt
    
    Returns:
        Suggested canonical name for matching purposes
    """
    return normalize_item_name(raw_name, keep_descriptors=False)
