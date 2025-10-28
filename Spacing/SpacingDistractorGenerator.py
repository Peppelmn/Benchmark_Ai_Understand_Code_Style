import random
from typing import List
from DistractorGenerator import DistractorGenerator
from DataClassesDefiner import Question, Answer

class SpacingDistractorGenerator(DistractorGenerator):
    """Genera distrattori per domande sullo spacing"""
    
    def generate(self, correct_answer: Answer, question: Question, num_distractors: int = 3) -> List[Answer]:
        #Ti scorri tutte le domande di spacing e crei metodi specifici per ognuna
        if question.id.__eq__("S01") or question.id.__eq__("S02"):
            return self.generate_distractors_S01(float(correct_answer.text), num_distractors)
        pass

    def generate_distractors_S01(self, correct_value: float, num_distractors: int) -> List[Answer]:

        distractors = list()
        while len(distractors) < num_distractors:
            # Genera un distrattore casuale vicino al valore corretto
            perturbation = random.choice([-2, -1, 1, 2])
            distractor_value = correct_value + perturbation
            if distractor_value >= 0 and distractor_value != correct_value and all(d.text != str(distractor_value) for d in distractors):
                distractors.append(Answer(str(distractor_value), False))
        return distractors