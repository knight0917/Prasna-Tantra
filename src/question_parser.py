import re

HOUSE_KEYWORDS = {
    10: ('career',   r'job|career|profession|work|office|boss|promotion|salary|business|employ|interview|recruit|infosys|company|resign|retire|transfer'),
    7:  ('marriage', r'marriage|marry|married|wife|husband|spouse|partner|relationship|wedding|bride|groom|divorce|separate|love|girlfriend|boyfriend|engagement'),
    5:  ('children', r'child|son|daughter|baby|pregnant|pregnancy|birth|kid|deliver|conceive|exam|study|education|college|admission|iit|school|result'),
    6:  ('illness',  r'sick|illness|disease|health|hospital|doctor|recover|cure|medicine|surgery|pain|fever|cancer|treatment|diagnos|infection|operation'),
    4:  ('property', r'house|property|flat|land|home|plot|apartment|mother|vehicle|car|bike|buy|purchase|construct|rent|lease|bungalow'),
    2:  ('wealth',   r'money|wealth|finance|loan|debt|income|rich|poor|investment|saving|profit|loss|bank|borrow|lend|fund|cash|pay|afford'),
    9:  ('travel',   r'travel|trip|journey|abroad|foreign|visa|passport|flight|tour|immigrat|overseas|outside|country|settle'),
    3:  ('siblings', r'brother|sister|sibling|neighbour|cousin|communication|phone|letter|message|news|document|media|report|short'),
    8:  ('longevity',r'death|die|dead|longevity|surgery|accident|fatal|terminal|chronic|critical|inheritance|last rites|serious illness|life threatening|how long will i live'),
    11: ('wealth',   r'gain|profit|friend|wish|desire|hope|elder|income|achieve|goal|ambition|success|win|lottery|bonus'),
    12: ('loss',     r'loss|expense|foreign settle|hospital admit|prison|jail|enemy|hidden|secret|isolat|abroad settl|spiritual|monk|asylum'),
    1:  ('wealth',   r'myself|my future|who am i|what will happen to me|my overall'),
}

TOPIC_MAP = {
    'career': 'career', 'marriage': 'marriage', 'children': 'children',
    'illness': 'illness', 'property': 'property', 'wealth': 'wealth',
    'travel': 'travel', 'siblings': 'siblings', 'longevity': 'longevity',
    'loss': 'loss', 'father': 'father',
}

def parse_question(user_question: str) -> dict:
    """
    Classifies a natural language query using a high-performance regex-based 
    keyword classifier with auxiliary verb filtering.
    """
    text = user_question.lower().strip()
    
    TEST_PATTERNS = r'test|testing|just asking|checking|random|fake|joke|fun|curious|what if|hypothetical|suppose|imagine'
    if re.search(TEST_PATTERNS, text):
        return {
            'house': 2, 'topic': 'wealth', 'query_topic': 'wealth',
            'query_house': 2, 'confidence': 'low',
            'rephrased': user_question,
            'reasoning': 'Question appears to be a test or hypothetical. Sincerity check will flag this.',
            'is_test_question': True
        }
    
    # Remove common auxiliary verbs that are not meaningful keywords
    # This prevents false positives like 'will' triggering House 8/12
    text = re.sub(r'\b(will|shall|would|could|should|may|might|can|do|does|did|is|are|was|were|be|been|being|have|has|had|get|got)\b', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    scores = {}
    
    # Keyword-based scoring per house
    for house, (topic, pattern) in HOUSE_KEYWORDS.items():
        matches = len(re.findall(pattern, text))
        if matches > 0:
            scores[house] = (matches, topic)

    if scores:
        # Pick the house with highest match frequency
        best_house = max(scores, key=lambda h: scores[h][0])
        best_topic = scores[best_house][1]
        match_count = scores[best_house][0]
        confidence = 'high' if match_count >= 2 else 'medium' if match_count == 1 else 'low'
    else:
        # Default to Wealth (House 2) if no keywords found
        best_house = 2
        best_topic = 'wealth'
        confidence = 'low'

    # Build rephrased (trim to keep layout clean)
    rephrased = user_question.strip()
    if len(rephrased) > 60:
        rephrased = rephrased[:57] + '...'

    house_names = {
        1:'Self', 2:'Wealth & Finance', 3:'Siblings & Communication',
        4:'Property & Home', 5:'Children & Education', 6:'Illness & Health',
        7:'Marriage & Relationships', 8:'Longevity', 9:'Travel & Fortune',
        10:'Career & Profession', 11:'Gains & Friends', 12:'Loss & Foreign'
    }

    reasoning = f'Keywords matched suggest this relates to {house_names.get(best_house, "House " + str(best_house))} (House {best_house}).'
    if confidence == 'low':
        reasoning = 'No strong keywords found. Defaulted to House 2 (Wealth). Please use the topic selector for better accuracy.'

    return {
        'house': best_house,
        'topic': best_topic,
        'query_topic': TOPIC_MAP.get(best_topic, 'wealth'),
        'query_house': best_house,
        'confidence': confidence,
        'rephrased': rephrased,
        'reasoning': reasoning,
    }
