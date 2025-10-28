import re
from CodebaseAnalyzer import CodebaseAnalyzer
from DataClassesDefiner import Question, Answer
import random

class SpacingAnalyzer(CodebaseAnalyzer):
    """Analizza la codebase su aspetti di spacing, trova la risposta corretta per le domande"""

    def analyze(self, question: Question) -> Answer:
        # Scorri le domande di spacing e crei metodi specifici per ognuna per trovare la risposta corretta
        if question.id.__eq__("S01"):
            return Answer(self.question_S01()[1], True) 
        elif question.id.__eq__("S02"):
            return Answer(self.question_S02()[1], True)
        pass

    def question_S01(self):
        def count_spaces_between_tokens(line):
            line = line.split('#')[0].rstrip()
            line = line.lstrip()
            if not line.strip():
                return None

            # Rimuove stringhe e f-string per evitare "=" interni
            line = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", line)

            # Controlla se c’è un vero assegnamento
            if "=" not in line or any(op in line for op in ["==", "!=", ">=", "<="]):
                return None

            # Collassa chiamate funzione in un token singolo
            def collapse_calls(s):
                pattern = re.compile(r"([A-Za-z_]\w*)\s*\([^()]*\)")
                while True:
                    new_s = pattern.sub(lambda m: m.group(1) + "(__CALL__)", s)
                    if new_s == s:
                        break
                    s = new_s
                return s

            line = collapse_calls(line)

            tokens = re.findall(r"[A-Za-z_]\w*|\d+\.\d+|\d+|[+\-*/%=(),\[\]]", line)
            if len(tokens) < 2:
                return None

            splits = re.split(r"[A-Za-z_]\w*|\d+\.\d+|\d+|[+\-*/%=(),\[\]]", line)
            splits = [s for s in splits if s != '']
            space_counts = [len(s) for s in splits if s.strip() == '']

            return sum(space_counts) / len(space_counts) if space_counts else 0
        
        def analyze_file(file_path):
            """Analizza un singolo file e restituisce una lista di valori di spaziatura."""
            spaces = []
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "=" in line and not any(op in line for op in ["==", "!=", ">=", "<="]):
                        val = count_spaces_between_tokens(line)
                        if val is not None:
                            spaces.append(round(val, 2))
            return spaces
        
        def find_consistent_spacing_files():
            """Restituisce i file dove la spaziatura è costante in tutte le assegnazioni.

            Usa `self.python_files` (Path objects) forniti dalla classe base `CodebaseAnalyzer`.
            """
            consistent_files = []

            for path in self.python_files:
                # `path` è un pathlib.Path; analyze_file accetta anche path-like
                spaces = analyze_file(path)

                if not spaces:
                    continue  # Nessuna assegnazione trovata

                # Verifica coerenza: tutte le spaziature sono uguali
                if max(spaces) == min(spaces):
                    # salva solo il nome del file (basename) e il valore costante
                    relative_path = path.relative_to(self.codebase_path)
                    consistent_files.append((str(relative_path), spaces[0]))

            return random.choice(consistent_files) if consistent_files else None

        return find_consistent_spacing_files()
    
    def question_S02(self):
        def count_spaces_in_control_structure(line):
            """Analizza gli spazi in una struttura di controllo."""
            # Rimuovi commenti e spazi iniziali/finali
            line = line.split('#')[0].rstrip()
            line = line.lstrip()
            if not line.strip():
                return None

            # Verifica se è una struttura di controllo
            control_keywords = ('if', 'while', 'for')
            if not any(line.startswith(keyword + ' ') for keyword in control_keywords):
                return None

            # Estrai la condizione tra la keyword e il ':'
            try:
                # Trova la keyword usata
                keyword = next(k for k in control_keywords if line.startswith(k + ' '))
                condition = line[len(keyword):].split(':')[0].strip()

                # Per i 'for', prendi solo la parte dopo 'in'
                if keyword == 'for' and ' in ' in condition:
                    condition = condition.split(' in ')[1]

                # Rimuovi stringhe per evitare falsi positivi
                condition = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", condition)
                
                # Collassa le chiamate di funzione
                def collapse_calls(s):
                    pattern = re.compile(r"([A-Za-z_]\w*)\s*\([^()]*\)")
                    while True:
                        new_s = pattern.sub(lambda m: m.group(1) + "(__CALL__)", s)
                        if new_s == s:
                            break
                        s = new_s
                    return s

                condition = collapse_calls(condition)

                # Trova i token e gli spazi tra essi
                tokens = re.findall(r"[A-Za-z_]\w*|\d+\.\d+|\d+|[<>=!]=|[+\-*/%<>]=?|and|or|not|in|is|[(),\[\]]", condition)
                if len(tokens) < 2:
                    return None

                splits = re.split(r"[A-Za-z_]\w*|\d+\.\d+|\d+|[<>=!]=|[+\-*/%<>]=?|and|or|not|in|is|[(),\[\]]", condition)
                splits = [s for s in splits if s != '']
                space_counts = [len(s) for s in splits if s.strip() == '']

                return sum(space_counts) / len(space_counts) if space_counts else 0

            except (IndexError, StopIteration):
                return None

        def analyze_file(file_path):
            """Analizza un singolo file e restituisce una lista di valori di spaziatura."""
            spaces = []
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    val = count_spaces_in_control_structure(line)
                    if val is not None:
                        spaces.append(round(val, 2))
            return spaces

        def find_consistent_spacing_files():
            """Restituisce i file dove la spaziatura nelle strutture di controllo è costante."""
            consistent_files = []

            for path in self.python_files:
                spaces = analyze_file(path)

                if not spaces:
                    continue  # Nessuna struttura di controllo trovata

                # Verifica coerenza: tutte le spaziature sono uguali
                if max(spaces) == min(spaces):
                    relative_path = path.relative_to(self.codebase_path)
                    consistent_files.append((str(relative_path), spaces[0]))

            return random.choice(consistent_files) if consistent_files else None
            # return consistent_files
        return find_consistent_spacing_files()