from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from DataClassesDefiner import Question, Answer

class DistractorGenerator:
    """Base class for distractor generators"""
    
    @abstractmethod
    def generate(self, correct_answer: Answer, question: Question, num_distractors: int = 3) -> List[Answer]:
        """Generates plausible incorrect answers (distractors) for a given question."""
        pass