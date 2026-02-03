import random
from typing import List
from DistractorGenerator import DistractorGenerator
from DataClassesDefiner import Question, Answer

class SpacingDistractorGenerator(DistractorGenerator):
    """
    Specialized distractor generator for spacing-related questions.
    """
    
    def generate(self, correct_answer: Answer, question: Question, num_distractors: int = 3) -> List[Answer]:
        """
        Orchestrates the generation of distractors based on the question ID, distinguishing between numeric spacing values (S01-S12) and wrapping strategies (S13).

        Args:
            correct_answer (Answer): The correct answer object containing the ground truth.
            question (Question): The question object containing the ID.
            num_distractors (int): The number of wrong answers to generate.

        Returns: A list of Answer objects representing the distractors.
        """
        if any(question.id.__eq__(id) for id in ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12"]):
            return self.generate_distractor(float(correct_answer.text), num_distractors)
        elif question.id == "S13":
            strategies = [
                "All arguments are on the same line",
                "Every argument is on a new line",
                "Mixed strategy (some on new lines, others not)"
            ]
            distractors = []
            correct_value = correct_answer.text
            for strategy in strategies:
                if strategy != correct_value and all(d.text != strategy for d in distractors):
                    distractors.append(Answer(strategy, False))
            return distractors
        pass

    def generate_distractor(self, correct_value: float, num_distractors: int) -> List[Answer]:
        """
        Generates numeric distractors by applying random perturbations to the correct value, ensuring non-negative and unique results.

        Args:
            correct_value (float): The correct numeric value (e.g., number of spaces or lines).
            num_distractors (int): The number of distractors to generate.

        Returns: A list of Answer objects with incorrect numeric values.
        """
        distractors = list()
        while len(distractors) < num_distractors:
            perturbation = random.choice([-3 ,-2, -1, 1, 2, 3])
            distractor_value = correct_value + perturbation
            if distractor_value >= 0 and distractor_value != correct_value and all(float(d.text) != float(distractor_value) for d in distractors):
                distractors.append(Answer(float(distractor_value), False))
        return distractors