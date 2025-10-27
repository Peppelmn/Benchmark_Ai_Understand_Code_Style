from typing import List
from DistractorGenerator import DistractorGenerator
from DataClassesDefiner import Question, Answer

class NamingDistractorGenerator(DistractorGenerator):
    """Genera distrattori per domande sul naming"""
    
    def generate(self, correct_answer: Answer, question: Question, num_distractors: int = 3) -> List[Answer]:
        #Ti scorri tutte le domande di naming e crei metodi specifici per ognuna
        pass