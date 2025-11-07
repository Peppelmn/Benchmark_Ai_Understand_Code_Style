import random
from typing import List
from DistractorGenerator import DistractorGenerator
from DataClassesDefiner import Question, Answer

class SpacingDistractorGenerator(DistractorGenerator):
    """Genera distrattori per domande sullo spacing"""
    
    def generate(self, correct_answer: Answer, question: Question, num_distractors: int = 3) -> List[Answer]:
        if any(question.id.__eq__(id) for id in ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12"]):
            return self.generate_distractors_1(float(correct_answer.text), num_distractors)
        pass

    def generate_distractors_1(self, correct_value: float, num_distractors: int) -> List[Answer]:

        distractors = list()
        while len(distractors) < num_distractors:
            # Genera un distrattore casuale vicino al valore corretto
            perturbation = random.choice([-3 ,-2, -1, 1, 2, 3])
            distractor_value = correct_value + perturbation
            if distractor_value >= 0 and distractor_value != correct_value and all(d.text != str(distractor_value) for d in distractors):
                distractors.append(Answer(str(distractor_value), False))
        return distractors