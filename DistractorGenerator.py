from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from DataClassesDefiner import Question, Answer

class DistractorGenerator(ABC):
    """Classe base per generatori di risposte errate"""
    
    @abstractmethod
    def generate(self, correct_answer: Answer, question: Question, num_distractors: int = 3) -> List[Answer]:
        """Genera risposte errate plausibili"""
        pass