import re
import string
from CodebaseAnalyzer import CodebaseAnalyzer
from DataClassesDefiner import Question, Answer
import random
import ast

class SpacingAnalyzer(CodebaseAnalyzer):
    """Analizza la codebase su aspetti di spacing, trova la risposta corretta per le domande"""

    def __init__(self, codebase_path: str, max_token_limit):
        super().__init__(codebase_path, max_token_limit)

    def _find_consistent_files(self, analyze_function, per_line=True):
        """
        Metodo generico per trovare file con una caratteristica 'consistente'.

        - analyze_function: funzione che analizza una riga (se per_line=True) o un intero file (se per_line=False)
        - per_line: True se la funzione lavora su singole righe, False se lavora su un intero file.
        """
        consistent_files = []

        for path in self.python_files:

            if len(consistent_files) >= self.num_target_files_per_question:
                break

            try:

                if per_line:
                    values = []
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f):
                            if i > 1000:  # evita file enormi
                                break
                            val = analyze_function(line)
                            if val is not None:
                                # Se è una lista, estrai media o primo valore
                                if isinstance(val, list):
                                    if len(val) == 0:
                                        continue
                                    val = sum(val) / len(val)
                                values.append(round(val, 2))
                else:
                    # Funzione che analizza tutto il file
                    val = analyze_function(path)
                    if val is None:
                        continue
                    # Può restituire una lista (es. più valori)
                    if isinstance(val, list):
                        values = val
                    else:
                        values = [val]

                # Se non abbiamo valori, salta il file
                if not values:
                    continue

                # Verifica se i valori sono consistenti (tutti uguali)
                if len(set(values)) == 1:
                    relative_path = path.relative_to(self.codebase_path)
                    consistent_files.append((str(relative_path), float(values[0])))

            except Exception as e:
                print(f"[!] Errore analizzando {path}: {e}")

        # Se non trovi nulla, restituisci None
        return consistent_files

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

        return self._find_consistent_files(count_spaces_between_tokens)
    
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

        return self._find_consistent_files(count_spaces_in_control_structure)
    
    def get_spaces_around_commas(self, count_before_after: str):

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
        
        return self._find_consistent_files(count_spaces_around_commas)
    
    def question_S03(self):
        return self.get_spaces_around_commas("before")
    
    def question_S04(self):
        return self.get_spaces_around_commas("after")

    def question_S05(self):
        """
        Trova i file che usano un numero coerente di righe vuote
        dopo una definizione di funzione (incluso il corpo).
        """
        
        def count_blank_lines_after_function(file_path):
            """
            Conta le righe vuote dopo ogni definizione di funzione (incluse quelle annidate)
            usando l'Abstract Syntax Tree (AST).
            """
            blank_counts = []
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines() # Ci serve l'elenco delle righe
                
                if not lines:
                    return []
                    
                tree = ast.parse(content)
                
            except Exception as e:
                # Gestisce sia SyntaxError di ast.parse sia Errori I/O
                self.parse_error_count += 1
                return []

            # ast.walk() scorre l'albero e trova TUTTI i nodi,
            # incluse le funzioni annidate, nell'ordine corretto.
            for node in ast.walk(tree):
                # Cerchiamo sia funzioni normali (def) sia asincrone (async def)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # end_lineno ci dice la riga in cui finisce il corpo della funzione.
                    # L'indice della riga finale (convertito da 1-based a 0-based)
                    func_end_line_index = node.end_lineno - 1
                    
                    # Ora contiamo le righe vuote DOPO questa riga
                    blank_count = 0
                    i = func_end_line_index + 1
                    
                    while i < len(lines):
                        if not lines[i].strip():
                            # È una riga vuota
                            blank_count += 1
                            i += 1
                        else:
                            # È una riga con contenuto, fermiamo il conteggio
                            break
                    
                    # Abbiamo trovato la fine del file o una riga di codice.
                    # Salviamo il conteggio.
                    blank_counts.append(blank_count)

            return blank_counts
        
        return self._find_consistent_files(count_blank_lines_after_function, per_line=False)
    
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
                consistent_files.append((str(relative_path), float(max_len)))
                if len(consistent_files) >= self.num_target_files_per_question:
                    break
        return consistent_files

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

        return self._find_consistent_files(analyze_file, per_line=False)

    def get_blank_lines_around_comments(self, count_above_below: str):
        """Trova i file che hanno un numero coerente di righe vuote sopra e sotto i commenti.
        Restituisce un file e la media di righe vuote trovata, se coerente.
        """

        def count_blank_lines_around_comments(file_path):
            """Conta le righe vuote immediatamente sopra e sotto i commenti in un file."""
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"[!] Errore nel file {file_path}: {e}")
                return None

            if not lines:
                return None

            blanks_above = []
            blanks_below = []

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Cerca commenti che iniziano con '#'
                if stripped.startswith("#") and not stripped.startswith("#!"):
                    # Conta le righe vuote sopra
                    j = i - 1
                    count_above = 0
                    while j >= 0 and not lines[j].strip():
                        count_above += 1
                        j -= 1

                    # Conta le righe vuote sotto
                    k = i + 1
                    count_below = 0
                    while k < len(lines) and not lines[k].strip():
                        count_below += 1
                        k += 1

                    blanks_above.append(count_above)
                    blanks_below.append(count_below)

            # Se non ci sono commenti, ignora il file
            if not blanks_above and not blanks_below:
                return None

            if count_above_below == "above":
                return blanks_above if blanks_above else 0
            elif count_above_below == "below":
                return blanks_below if blanks_below else 0
            
        return self._find_consistent_files(count_blank_lines_around_comments, per_line=False)

    def question_S08(self):
        return self.get_blank_lines_around_comments("above")
    
    def question_S09(self):
        return self.get_blank_lines_around_comments("below")

    def question_S10(self):
        """
        Trova i file che usano un numero coerente di righe vuote
        dopo OGNI blocco di import (singolo o multiplo).
        """

        def count_blank_lines_after_every_import_block(file_path):
            """
            Conta le righe vuote dopo OGNI blocco di import contiguo
            usando l'Abstract Syntax Tree (AST).
            """
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines() # Ci serve l'elenco delle righe
                
                if not lines:
                    return []
                    
                tree = ast.parse(content)
                
            except Exception as e:
                self.parse_error_count += 1
                return []

            def count_blanks_from(start_line_index, all_lines):
                """Helper per contare le righe vuote da un indice di riga."""
                blank_count = 0
                i = start_line_index + 1
                while i < len(all_lines):
                    if not all_lines[i].strip():
                        blank_count += 1
                        i += 1
                    else:
                        break # Trovata riga con contenuto
                return blank_count

            # Usiamo un NodeVisitor per trovare tutti gli import
            # e raggrupparli in blocchi contigui.
            class ImportVisitor(ast.NodeVisitor):
                def __init__(self, lines):
                    self.lines = lines
                    self.blank_counts = []
                    # Indice 0-based dell'ultima riga di import trovata
                    self.last_import_end_line = -1 

                def visit_Import(self, node):
                    self.process_import_node(node)
                    self.generic_visit(node)

                def visit_ImportFrom(self, node):
                    self.process_import_node(node)
                    self.generic_visit(node)

                def process_import_node(self, node):
                    if not hasattr(node, 'end_lineno'):
                        return # Salta se non abbiamo info (Python < 3.8)
                    
                    # Converti in indici 0-based
                    current_start_line = node.lineno - 1
                    current_end_line = node.end_lineno - 1
                    
                    # Se questo import NON è contiguo al precedente...
                    # E abbiamo già visto un import (last_import_end_line != -1)
                    # ...allora il blocco precedente è finito. Contiamo gli spazi.
                    if self.last_import_end_line != -1 and current_start_line > (self.last_import_end_line + 1):
                        # C'è un salto (codice o righe vuote) tra i blocchi di import.
                        # Conta gli spazi dopo il blocco PRECEDENTE.
                        count = count_blanks_from(self.last_import_end_line, self.lines)
                        self.blank_counts.append(count)

                    # Questo import è ora l'ultimo che abbiamo visto.
                    # Aggiorniamo l'indice dell'ultima riga.
                    self.last_import_end_line = current_end_line
                
                def finalize(self):
                    # Dopo aver visitato tutto l'albero,
                    # dobbiamo contare gli spazi dopo l'ULTIMO blocco di import trovato.
                    if self.last_import_end_line != -1:
                        count = count_blanks_from(self.last_import_end_line, self.lines)
                        self.blank_counts.append(count)

            # Esegui il Visitor
            visitor = ImportVisitor(lines)
            visitor.visit(tree)
            visitor.finalize() # Conta gli spazi dopo l'ultimo blocco
            
            return visitor.blank_counts

        return self._find_consistent_files(count_blank_lines_after_every_import_block, per_line=False)
    
    def question_S11(self):
        """
        Trova i file che usano un numero coerente di righe vuote
        dopo una definizione di classe (incluse quelle annidate).
        """
        
        def count_blank_lines_after_class_ast(file_path):
            """
            Conta le righe vuote dopo ogni definizione di classe (incluse quelle annidate)
            usando l'Abstract Syntax Tree (AST).
            """
            blank_counts = []
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines() # Ci serve l'elenco delle righe
                
                if not lines:
                    return []
                    
                tree = ast.parse(content)
                
            except Exception as e:
                # Gestisce sia SyntaxError di ast.parse sia Errori I/O
                self.parse_error_count += 1
                return []

            # ast.walk() scorre l'albero e trova TUTTI i nodi ClassDef,
            # incluse le classi annidate.
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef): 
                    
                    # 'end_lineno' ci dice la riga in cui finisce il corpo della classe.
                    if not hasattr(node, 'end_lineno'):
                        # Sicurezza per versioni < Python 3.8
                        print(f"[!] Attenzione: 'end_lineno' non disponibile per {file_path} "
                              "(serve Python 3.8+). Salto S11 per questo file.")
                        return []

                    # L'indice della riga finale (convertito da 1-based a 0-based)
                    class_end_line_index = node.end_lineno - 1
                    
                    # Ora contiamo le righe vuote DOPO questa riga
                    blank_count = 0
                    i = class_end_line_index + 1
                    
                    while i < len(lines):
                        if not lines[i].strip():
                            # È una riga vuota
                            blank_count += 1
                            i += 1
                        else:
                            # È una riga con contenuto, fermiamo il conteggio
                            break
                    
                    # Abbiamo trovato la fine del file o una riga di codice.
                    # Salviamo il conteggio.
                    blank_counts.append(blank_count)

            return blank_counts
        
        return self._find_consistent_files(count_blank_lines_after_class_ast, per_line=False)
    
    def question_S12(self):
        """
        Trova i file che usano un numero coerente di righe vuote
        dopo OGNI blocco di assegnazione di costanti (es. NOME_MAIUSCOLO = ...).
        """

        def _is_constant_name(name_str: str) -> bool:
            """
            Helper per determinare se un nome di variabile segue la
            convenzione delle costanti (es. MAIUSCOLO, MAIUSCOLO_1).
            """
            if not name_str or not isinstance(name_str, str):
                return False
            # Deve contenere almeno una lettera
            if not any(c.isalpha() for c in name_str):
                return False # Esclude "_" o "123"
            
            # Controlla se tutti i caratteri alfabetici sono maiuscoli
            for char in name_str:
                if char.isalpha() and not char.isupper():
                    return False # Trovata una lettera minuscola
            return True

        def count_blank_lines_after_constants_ast(file_path):
            """
            Conta le righe vuote dopo OGNI blocco di costanti
            usando l'Abstract Syntax Tree (AST).
            """
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines()
                
                if not lines:
                    return []
                    
                tree = ast.parse(content)
                
            except Exception as e:
                self.parse_error_count += 1
                return []

            def count_blanks_from(start_line_index, all_lines):
                """Helper per contare le righe vuote da un indice di riga."""
                blank_count = 0
                i = start_line_index + 1
                while i < len(all_lines):
                    if not all_lines[i].strip():
                        blank_count += 1
                        i += 1
                    else:
                        break # Trovata riga con contenuto
                return blank_count

            class ConstantVisitor(ast.NodeVisitor):
                def __init__(self, lines):
                    self.lines = lines
                    self.blank_counts = []
                    # Indice 0-based dell'ultima riga di costante trovata
                    self.last_constant_end_line = -1 

                def visit_Assign(self, node):
                    """Visita 'VAR = ...'"""
                    self.process_constant_node(node)
                    # Continua a visitare i figli, potrebbero esserci costanti annidate
                    self.generic_visit(node)

                def visit_AnnAssign(self, node):
                    """Visita 'VAR: int = ...'"""
                    self.process_constant_node(node)
                    self.generic_visit(node)

                def process_constant_node(self, node):
                    """Controlla se il nodo è un'assegnazione di costante e processalo."""
                    
                    is_const = False
                    # Controlla se ALMENO una delle destinazioni è una costante
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and _is_constant_name(target.id):
                                is_const = True
                                break
                    elif isinstance(node, ast.AnnAssign):
                        if isinstance(node.target, ast.Name) and _is_constant_name(node.target.id):
                            is_const = True

                    # Se questo nodo non è un'assegnazione di costante, ignora.
                    if not is_const:
                        return 

                    # Controllo di sicurezza per Python < 3.8
                    if not hasattr(node, 'end_lineno'):
                        return 
                    
                    current_start_line = node.lineno - 1
                    current_end_line = node.end_lineno - 1
                    
                    # Controlla se questo è un nuovo blocco di costanti
                    # Se la riga di inizio è > 1 riga dopo la fine dell'ultimo blocco...
                    if self.last_constant_end_line != -1 and current_start_line > (self.last_constant_end_line + 1):
                        # ...allora il blocco precedente è finito. Contiamo gli spazi dopo di esso.
                        count = count_blanks_from(self.last_constant_end_line, self.lines)
                        self.blank_counts.append(count)

                    # Questa riga di costante è ora l'ultima che abbiamo visto
                    self.last_constant_end_line = current_end_line
                
                def finalize(self):
                    """Chiamato dopo la visita, per contare gli spazi dopo l'ultimo blocco."""
                    if self.last_constant_end_line != -1:
                        count = count_blanks_from(self.last_constant_end_line, self.lines)
                        self.blank_counts.append(count)

            # Esegui il Visitor
            visitor = ConstantVisitor(lines)
            visitor.visit(tree)
            visitor.finalize() # Conta gli spazi dopo l'ultimo blocco
            
            return visitor.blank_counts

        # Il tuo metodo helper _find_consistent_files non cambia
        return self._find_consistent_files(count_blank_lines_after_constants_ast, per_line=False)