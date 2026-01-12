from dataclasses import dataclass
from typing import Any, Dict, List
import random

@dataclass
class Question:
    """
    Represents a benchmark question definition.
    It serves as a container for a specific question type found across multiple target files,
    holding the template text and the corresponding correct values for each file.
    """
    id: str
    category: str
    text_template: str
    target_files: List[str] 
    correct_answer_values: List[Any]
    extra_data: List[Any] = None

@dataclass
class Answer:
    """
    Represents a single answer option (either correct or a distractor) for a multiple-choice question.
    """    
    text: Any
    is_correct: bool

@dataclass
class BenchmarkItem:
    """
    Represents a complete, distinct benchmark item.
    It aggregates the specific question instance, the ground truth answer, and the generated distractors.
    """
    question: Question
    correct_answer: Answer
    distractors: List[Answer]

    def to_dict(self) -> Dict:
        """
        Converts the benchmark item into a dictionary format suitable for AI evaluation.
        It combines the correct answer with distractors, shuffles them to randomize positions,
        and assigns selection labels (A, B, C, D).

        Returns:
            Dict: The formatted dictionary containing the question prompt, shuffled options, correct label, and target file.
        """
        answers = [self.correct_answer] + self.distractors
        random.shuffle(answers)
        
        return {
            "question_id": self.question.id,
            "category": self.question.category,
            "question": self.question.text_template,
            "answers": [{"text": a.text, "label": chr(65 + i)} for i, a in enumerate(answers)],
            "correct_label": chr(65 + answers.index(self.correct_answer)),
            "target_file": self.question.target_files[0]
        }