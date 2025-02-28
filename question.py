import random

def get_random_question(filename="question.txt"):
    with open(filename, "r", encoding="utf-8") as file:
        questions = file.readlines()
    questions = [q.strip() for q in questions if q.strip()]  # Remove empty lines
    return random.choice(questions) if questions else "No questions available."

# Example usage
print(get_random_question())