"""
Manual verification of the full extraction -> retrieval -> generation pipeline
against the live GraphDB instance and the real LLM. Not a test suite - the
questions are open-ended, so this just prints each answer for manual review
rather than asserting exact output. Run it directly:

    python3 scripts/verify_generation.py
"""

import sys

sys.path.insert(0, ".")

from app.rag.pipeline import answer_question

CREATIVE_QUESTIONS = [
    "I want to impress my date but I only have vodka, some sad-looking limes, and ginger beer. Can you save my evening and tell me what to make?",
    "I absolutely despise sweet drinks. Give me the recipe for something incredibly bitter and strong that will make me question my life choices.",
    "My friend doesn't drink alcohol, but I want to make them something that looks and tastes like a complex historical cocktail, not just glorified fruit juice. What are my options?",
    "I have gin, sweet vermouth, and Campari. I know this makes a classic cocktail. What is it, what's the exact ratio, and how should I garnish it?",
    "Who actually invented the Margarita? I've heard at least three different stories. Break down the most credible historical claims for me.",
    "I'm throwing a 1920s Prohibition-era party. What are three authentic cocktails they would have actually served in a speakeasy, and why were those specific drinks popular then?",
    "I bet you don't know any classic cocktails that use raw egg. Prove me wrong, give me the recipe, and tell me who in history thought drinking raw egg was a good idea.",
    "Is it true James Bond's 'shaken, not stirred' Martini is actually a terrible way to make that specific drink? Explain the science and the history behind this.",
    "Tell me a weird historical anecdote about absinthe. Did it really make 19th-century artists hallucinate, or was that just bad marketing?",
    "What is the most expensive or ridiculous cocktail ever sold in history, and why on earth did it cost so much?",
]

FACTUAL_QUESTIONS = [
    "What is the origin country of the Margarita?",
    "What type of glass is used to serve a Negroni?",
    "How many ingredients does a Manhattan have?",
    "Is the Irish Coffee classified as an alcoholic drink?",
    "Which country is the origin of the Mojito?",
    "What category of drink is the Martini?",
    "What kind of glass do I need to serve a Moscow Mule?",
    "How many ingredients are in a Dark and Stormy?",
    "What is the origin country of the Caipirinha?",
    "Which glass is used to serve Sex on the Beach?",
    "What category of drink does the Pina Colada belong to?",
    "Where was the Bloody Mary created according to the database?",
    "How many ingredients are in a Long Island?",
    "In what glass is a Daiquiri traditionally served?",
    "What is the category of a Cosmopolitan?",
]

OFF_TOPIC_QUESTIONS = [
    "How do I bake a chocolate cake?",
    "What is the capital of France?",
    "How do I change a flat tire on a car?",
    "What are the ingredients for a classic spaghetti carbonara?",
    "Can you explain how photosynthesis works?",
]


def run_group(title: str, questions: list[str]) -> None:
    print(f"\n--- {title} ---")
    for question in questions:
        answer = answer_question(question)
        print(f"\nQ: {question}\nA: {answer}")


run_group("creative / open-ended questions", CREATIVE_QUESTIONS)
run_group("factual DB-lookup questions", FACTUAL_QUESTIONS)
run_group("off-topic questions (expect a polite non-answer)", OFF_TOPIC_QUESTIONS)

print("\nDone. Review the answers above for correctness, groundedness, and tone.")
