from rapidfuzz import fuzz
import itertools

# Liste de catégories (exemple avec une faute)
categories = [
    'Automation',
    'BDD',
    'Classification',
    'Data Science',
    'Docker',
    'Machine Learning',
    'Streaming de données',
    'Systèmes distribués',
    'Sytèmes distribués'  # Faute de frappe
]

# Détection des doublons ou fautes de frappe
print("Catégories similaires détectées (score > 90) :\n")
for cat1, cat2 in itertools.combinations(categories, 2):
    score = fuzz.ratio(cat1, cat2)
    if score > 90 and cat1 != cat2:
        print(f"- '{cat1}' vs '{cat2}' (score: {score:.1f})")