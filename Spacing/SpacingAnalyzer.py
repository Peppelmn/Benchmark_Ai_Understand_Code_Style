import re
import string
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
        elif question.id.__eq__("S03"):
            return Answer(self.question_S03_S04("before")[1], True)
        elif question.id.__eq__("S04"):
            return Answer(self.question_S03_S04("after")[1], True)
        elif question.id.__eq__("S05"):
            return Answer(self.question_S05()[1], True)
        elif question.id.__eq__("S06"):
            return Answer(self.question_S06()[1], True)
        elif question.id.__eq__("S07"):
            return Answer(self.question_S07()[1], True)

    def _find_consistent_spacing_files(self, count_function):
        """Metodo generico per trovare file con spaziatura consistente."""

        def analyze_file(file_path):
            """Analizza un singolo file e restituisce una lista di valori di spaziatura."""
            spaces = []
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f):
                        if i > 2000:  # evita file enormi
                            break
                        val = count_function(line)
                        if val is not None:
                            spaces.append(round(val, 2))
            except Exception as e:
                print(f"[!] Errore nel file {file_path}: {e}")
            return spaces

        consistent_files = []

        for i, path in enumerate(self.python_files):
            spaces = analyze_file(path)
            if not spaces:
                continue
            if max(spaces) == min(spaces):
                relative_path = path.relative_to(self.codebase_path)
                consistent_files.append((str(relative_path), spaces[0]))

        return random.choice(consistent_files) if consistent_files else None

    def question_S01(self):
        
        def count_spaces_between_tokens(line):
            line = line.split('#')[0].rstrip()
            line = line.lstrip()
            if not line.strip():
                return None

            # Rimuove stringhe e f-string per evitare "=" interni
            line = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", line)

            # Controlla se c'è un vero assegnamento
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

        return self._find_consistent_spacing_files(count_spaces_between_tokens)
    
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

        return self._find_consistent_spacing_files(count_spaces_in_control_structure)
    
    def question_S03_S04(self, count_before_after: str):

        def count_spaces_around_commas(line):
            """Analizza gli spazi prima o dopo le virgole negli argomenti di funzione."""
            # Rimuovi commenti e spazi iniziali/finali
            line = line.split('#')[0].rstrip()
            line = line.lstrip()
            if not line.strip():
                return None

            # Cerca definizioni di funzioni o chiamate con argomenti
            # Pattern per catturare il contenuto tra parentesi
            func_pattern = r'(?:def\s+\w+|[\w.]+)\s*\(([^)]+)\)'
            matches = re.findall(func_pattern, line)
            
            if not matches:
                return None

            # Analizza tutti i gruppi di argomenti trovati nella riga
            space_counts = []
            
            for args_str in matches:
                # Rimuovi stringhe per evitare virgole all'interno di esse
                args_cleaned = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", args_str)
                
                # Trova tutte le virgole e conta gli spazi prima o dopo di esse
                parts = args_cleaned.split(',')
                
                # Se c'è solo una parte, non ci sono virgole
                if len(parts) <= 1:
                    continue
                
                if count_before_after == "before":
                    # Conta gli spazi prima della virgola (spazi finali di ogni parte)
                    for i in range(len(parts) - 1):
                        part = parts[i]
                        trailing_spaces = len(part) - len(part.rstrip(' '))
                        space_counts.append(trailing_spaces)
                else:
                    # Conta gli spazi dopo la virgola (spazi iniziali di ogni parte)
                    for i in range(1, len(parts)):
                        part = parts[i]
                        leading_spaces = len(part) - len(part.lstrip(' '))
                        space_counts.append(leading_spaces)
            
            return sum(space_counts) / len(space_counts) if space_counts else None
        
        return self._find_consistent_spacing_files(count_spaces_around_commas)
        
    def question_S05(self):
        def count_blank_lines_after_function(file_path):
            """Conta le righe vuote dopo ogni definizione di funzione (incluso il corpo).
            """
            blank_counts = []
            
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            if not lines:
                return blank_counts
            
            i = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.lstrip()
                
                # Cerca una definizione di funzione
                if stripped.startswith('def ') and '(' in stripped:
                    # Trova l'indentazione della funzione
                    func_indent = len(line) - len(stripped)
                    i += 1
                    
                    # Variabili per tracciare stringhe multi-riga
                    in_multiline_string = False
                    string_delimiter = None
                    
                    # Salta il corpo della funzione
                    # Il corpo finisce quando troviamo una riga non vuota con indentazione <= func_indent
                    while i < len(lines):
                        current_line = lines[i]
                        current_stripped = current_line.lstrip()
                        current_full_stripped = current_line.strip()
                        
                        # Se siamo in una stringa multi-riga, cerca solo la chiusura
                        if in_multiline_string:
                            if string_delimiter in current_line:
                                in_multiline_string = False
                                string_delimiter = None
                            i += 1
                            continue
                        
                        # Se la riga è vuota o è un commento, continua
                        if not current_stripped or current_stripped.startswith('#'):
                            i += 1
                            continue
                        
                        # Controlla se c'è una stringa multi-riga (""" o ''')
                        found_multiline = False
                        for delimiter in ['"""', "'''"]:
                            if delimiter in current_full_stripped:
                                # Conta quante volte appare il delimitatore nella riga
                                count = current_full_stripped.count(delimiter)
                                
                                if count == 1:
                                    # Inizia una stringa multi-riga
                                    in_multiline_string = True
                                    string_delimiter = delimiter
                                    found_multiline = True
                                    i += 1
                                    break
                                elif count >= 2:
                                    # Stringa completa su una sola riga (es: """docstring""")
                                    found_multiline = True
                                    i += 1
                                    break
                        
                        # Se abbiamo trovato una stringa, continua al prossimo ciclo
                        if found_multiline:
                            continue
                        
                        # Calcola l'indentazione
                        current_indent = len(current_line) - len(current_stripped)
                        
                        # Se l'indentazione è maggiore della funzione, siamo nel corpo
                        if current_indent > func_indent:
                            i += 1
                            continue
                        else:
                            # Abbiamo trovato codice allo stesso livello o inferiore
                            # Torniamo indietro per contare le righe vuote
                            break
                    
                    # Ora torniamo indietro per contare le righe vuote
                    # tra la fine del corpo e il codice successivo
                    j = i - 1
                    blank_count = 0
                    
                    # Conta le righe vuote andando indietro
                    while j >= 0 and not lines[j].strip():
                        blank_count += 1
                        j -= 1
                    
                    blank_counts.append(blank_count)
                    continue
                
                i += 1
            
            return blank_counts
        
        consistent_files = []
        
        for path in self.python_files:
            counts = count_blank_lines_after_function(path)
            
            if not counts:
                continue  # Nessuna funzione trovata
            
            # Verifica coerenza: tutti i conteggi sono uguali
            if len(set(counts)) == 1:  # Tutti i valori sono uguali
                relative_path = path.relative_to(self.codebase_path)
                consistent_files.append((str(relative_path), counts[0]))
        
        return random.choice(consistent_files) if consistent_files else None
    
    def question_S06(self):
        """Trova la lunghezza massima delle righe di codice in un file,
        ignorando docstring e stringhe multi-linea ('''...''' e \"\"\"...\"\"\")."""

        def max_line_length(file_path):
            """Restituisce la lunghezza massima delle righe in un file ignorando
            docstring / stringhe multi-linea e commenti/righe vuote."""
            max_length = 0
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    # Rimuove stringhe multi-linea ('''...''' e """...""") su più righe
                    # (?s) abilita DOTALL così il . cattura anche newline
                    content = re.sub(r"(?s)(?:'''(?:.*?)'''|\"\"\"(?:.*?)\"\"\")", "", content)

                    for i, line in enumerate(content.splitlines()):
                        if i > 5000:
                            break
                        stripped = line.rstrip("\n\r")
                        if not stripped.strip():
                            continue
                        if stripped.lstrip().startswith("#"):
                            continue
                        # Considera la lunghezza effettiva della riga
                        length = len(stripped)
                        if length > max_length:
                            max_length = length
            except Exception as e:
                print(f"[!] Errore nel file {file_path}: {e}")
            return max_length if max_length > 0 else None

        consistent_files = []

        for path in self.python_files:
            max_len = max_line_length(path)
            if max_len is not None:
                relative_path = path.relative_to(self.codebase_path)
                consistent_files.append((str(relative_path), max_len))

        return random.choice(consistent_files) if consistent_files else None

    def question_S07(self):
        """Trova i file che usano un numero coerente di spazi per indentazione.
        """

        def count_indent_spaces(line):
            """Conta gli spazi iniziali in una riga di codice Python."""
            if not line.strip():
                return None  # riga vuota
            if line.lstrip().startswith("#"):
                return None  # commento
            if line.startswith("\t"):
                return None  # ignora tabulazioni, non coerente con spazi
            leading_spaces = len(line) - len(line.lstrip(' '))
            if leading_spaces == 0:
                return None
            return leading_spaces

        def analyze_file(file_path):
            """Analizza le indentazioni nel file e restituisce i livelli trovati."""
            indent_values = []
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f):
                        if i > 3000:
                            break
                        val = count_indent_spaces(line)
                        if val is not None:
                            indent_values.append(val)
            except Exception as e:
                print(f"[!] Errore nel file {file_path}: {e}")
                return []

            if not indent_values:
                return []

            # Trova le differenze di indentazione (livelli)
            diffs = [v for v in set(indent_values) if v > 0]
            if not diffs:
                return []

            # Controlla che tutti gli spazi usati per l'indentazione siano multipli di un valore consistente
            smallest = min(diffs)
            if all(v % smallest == 0 for v in diffs):
                return [smallest]
            return []

        consistent_files = []
        for path in self.python_files:
            result = analyze_file(path)
            if result:
                relative_path = path.relative_to(self.codebase_path)
                consistent_files.append((str(relative_path), result[0]))

        return random.choice(consistent_files) if consistent_files else None

    # Da rivedere
    # def question_S08(self, count_above_below: str):
    #     """Trova i file che hanno un numero coerente di righe vuote sopra e sotto i commenti.
    #     Restituisce un file e la media di righe vuote trovata, se coerente.
    #     """

    #     def count_blank_lines_around_comments(file_path):
    #         """Conta le righe vuote immediatamente sopra e sotto i commenti in un file."""
    #         try:
    #             with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    #                 lines = f.readlines()
    #         except Exception as e:
    #             print(f"[!] Errore nel file {file_path}: {e}")
    #             return None

    #         if not lines:
    #             return None

    #         blanks_above = []
    #         blanks_below = []

    #         for i, line in enumerate(lines):
    #             stripped = line.strip()

    #             # Cerca commenti che iniziano con '#'
    #             if stripped.startswith("#") and not stripped.startswith("#!"):
    #                 # Conta le righe vuote sopra
    #                 j = i - 1
    #                 count_above = 0
    #                 while j >= 0 and not lines[j].strip():
    #                     count_above += 1
    #                     j -= 1

    #                 # Conta le righe vuote sotto
    #                 k = i + 1
    #                 count_below = 0
    #                 while k < len(lines) and not lines[k].strip():
    #                     count_below += 1
    #                     k += 1

    #                 blanks_above.append(count_above)
    #                 blanks_below.append(count_below)

    #         # Se non ci sono commenti, ignora il file
    #         if not blanks_above and not blanks_below:
    #             return None

    #         # Calcola le medie
    #         avg_above = sum(blanks_above) / len(blanks_above) if blanks_above else 0
    #         avg_below = sum(blanks_below) / len(blanks_below) if blanks_below else 0

    #         if count_above_below == "above":
    #             return avg_above
    #         elif count_above_below == "below":
    #             return avg_below

    #     consistent_files = []

    #     for path in self.python_files:
    #         result = count_blank_lines_around_comments(path)
    #         if not result:
    #             continue

    #         blank_count = result

    #         # Consideriamo coerente un file se tutti i commenti hanno lo stesso numero di righe vuote
    #         # (cioè medie intere e vicine)
    #         if blank_count.is_integer():
    #             relative_path = path.relative_to(self.codebase_path)
    #             consistent_files.append((str(relative_path), int(blank_count)))

    #     return random.choice(consistent_files) if consistent_files else None