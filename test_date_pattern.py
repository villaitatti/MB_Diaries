import re

# Date pattern to detect date headers - matches various date formats
date_pattern = re.compile(
    r'^\s*(?:'
    # Optional day of week: "Monday, " or "Sunday. "
    r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,.\s]+)?'
    # Month: "Aug." or "August" or "Aug"
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
    # Optional period/space after month
    r'[.\s]*'
    # Day: "7" or "8" 
    r'\d{1,2}'
    # Allow text in between (location names)
    r'.*?'
    # Year: "1891" or "91"
    r'(?:18|19|20)?\d{2}',
    re.IGNORECASE
)

# Test cases from the diary
test_cases = [
    "August 7 1891. Antwerp",
    "Aug. 8 Antwerp The Hague 1891",
    "Sunday, Aug. 9. 91. The Hague",
    "want to look at a picture a whole quarter of an hour.",
    "Diary",
    "Read Vol. V of Journal de J. Goncourt at breakfast.",
]

print("Testing date pattern:")
for test in test_cases:
    match = date_pattern.match(test)
    print(f"  '{test[:50]}...' -> {'MATCH' if match else 'NO MATCH'}")