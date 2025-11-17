from dataclasses import dataclass
from typing import Any, Dict, List
import random

@dataclass
class Question:
    """Rappresenta una domanda del benchmark"""
    id: str
    category: str
    text: str
    target_file: str
    correct_answer_value: Any

@dataclass
class Answer:
    """Rappresenta una risposta (corretta o errata)"""
    text: Any
    is_correct: bool

@dataclass
class BenchmarkItem:
    """Item completo del benchmark"""
    question: Question
    correct_answer: Answer
    distractors: List[Answer]

    def to_dict(self) -> Dict:
        """Converte in formato per l'IA"""
        answers = [self.correct_answer] + self.distractors
        random.shuffle(answers)
        
        return {
            "question_id": self.question.id,
            "category": self.question.category,
            "question": self.question.text,
            "answers": [{"text": a.text, "label": chr(65 + i)} for i, a in enumerate(answers)],
            "correct_label": chr(65 + answers.index(self.correct_answer)),
            "target_file": self.question.target_file
        }