import re
import ast
from typing import Any, Dict, List, Optional
from CodebaseAnalyzer import CodebaseAnalyzer

class SpacingAnalyzer(CodebaseAnalyzer):
    """
    Analyzes Python source code to evaluate adherence to various spacing conventions.
    It employs a hybrid approach:
    - **Regex-based analysis** for line-level details (e.g., spaces around operators, indentation).
    - **AST-based analysis** for structural elements (e.g., blank lines after functions, classes, or import blocks).
    """
    def __init__(self, codebase_path: str, max_token_limit: float = float('inf')):
        """
        Initializes the SpacingAnalyzer.

        Args:
            codebase_path (str): The root path of the codebase.
            max_token_limit (float, optional): Token limit for analysis. Defaults to infinity.
        """
        super().__init__(codebase_path, max_token_limit)

    # ==============================================================================
    # LOGICA PURA (Estratta dai vecchi metodi)
    # Queste funzioni non aprono file, analizzano solo stringhe o nodi AST.
    # ==============================================================================

    def _logic_S01(self, line: str) -> Optional[int]:
        """
        (S01) Calculates the average number of spaces used around operators (e.g., =, ==, +, -) in a line.
        It handles string masking and nested function call collapsing to avoid false positives.

        Args:
            line (str): A single line of code.
        Returns:
            Optional[int]: The average space count (e.g., 1 for 'a = b'), or None if no operators are found.
        """
        line = line.split('#')[0].rstrip().lstrip()
        if not line.strip(): return None
        line = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", line)
        if "=" not in line or any(op in line for op in ["==", "!=", ">=", "<="]): return None
        
        # Collapse calls
        pattern = re.compile(r"([A-Za-z_]\w*)\s*\([^()]*\)")
        while True:
            new_s = pattern.sub(lambda m: m.group(1) + "(__CALL__)", line)
            if new_s == line: break
            line = new_s
            
        tokens = re.findall(r"[A-Za-z_]\w*|\d+\.\d+|\d+|[+\-*/%=(),\[\]]", line)
        if len(tokens) < 2: return None
        splits = re.split(r"[A-Za-z_]\w*|\d+\.\d+|\d+|[+\-*/%=(),\[\]]", line)
        splits = [s for s in splits if s != '']
        space_counts = [len(s) for s in splits if s.strip() == '']
        return sum(space_counts) / len(space_counts) if space_counts else 0

    def _logic_S02(self, line: str) -> Optional[int]:
        """
        (S02) Analyzes spacing within control structure conditions (if, while, for).
        Calculates how many spaces separate tokens inside the condition statement.

        Args:
            line (str): A single line of code.
        Returns:
            Optional[int]: Average space count within the condition, or None if not applicable.
        """
        line = line.split('#')[0].rstrip().lstrip()
        if not line.strip(): return None
        control_keywords = ('if', 'while', 'for')
        if not any(line.startswith(keyword + ' ') for keyword in control_keywords): return None
        try:
            keyword = next(k for k in control_keywords if line.startswith(k + ' '))
            condition = line[len(keyword):].split(':')[0].strip()
            if keyword == 'for' and ' in ' in condition:
                condition = condition.split(' in ')[1]
            condition = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", condition)
            
            # Collapse calls (semplificato per brevità, usa la stessa logica di S01)
            pattern = re.compile(r"([A-Za-z_]\w*)\s*\([^()]*\)")
            while True:
                new_s = pattern.sub(lambda m: m.group(1) + "(__CALL__)", condition)
                if new_s == condition: break
                condition = new_s
                
            tokens = re.findall(r"[A-Za-z_]\w*|\d+\.\d+|\d+|[<>=!]=|[+\-*/%<>]=?|and|or|not|in|is|[(),\[\]]", condition)
            if len(tokens) < 2: return None
            splits = re.split(r"[A-Za-z_]\w*|\d+\.\d+|\d+|[<>=!]=|[+\-*/%<>]=?|and|or|not|in|is|[(),\[\]]", condition)
            splits = [s for s in splits if s != '']
            space_counts = [len(s) for s in splits if s.strip() == '']
            return sum(space_counts) / len(space_counts) if space_counts else 0
        except: return None

    def _logic_commas(self, line: str, mode: str) -> Optional[float]:
        """
        (S03/S04) Helper logic to analyze spacing around commas in function definitions or calls.

        Args:
            line (str): A single line of code.
            mode (str): 'before' to count spaces before commas (S03), 'after' for spaces after (S04).
        Returns:
            Optional[float]: The average number of spaces found, or None.
        """
        line = line.split('#')[0].rstrip().lstrip()
        if not line.strip(): return None
        func_pattern = r'(?:def\s+\w+|[\w.]+)\s*\(([^)]+)\)'
        matches = re.findall(func_pattern, line)
        if not matches: return None
        
        counts = []
        for args_str in matches:
            args_cleaned = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", args_str)
            parts = args_cleaned.split(',')
            if len(parts) <= 1: continue
            
            if mode == "before":
                for i in range(len(parts) - 1):
                    counts.append(len(parts[i]) - len(parts[i].rstrip(' ')))
            else: # after
                for i in range(1, len(parts)):
                    counts.append(len(parts[i]) - len(parts[i].lstrip(' ')))
        
        return sum(counts) / len(counts) if counts else None

    def _logic_S07(self, line: str) -> Optional[int]:
        """
        (S07) Calculates the number of leading spaces (indentation) for a non-empty, non-comment line.

        Args:
            line (str): A single line of code.
        Returns:
            Optional[int]: The count of leading spaces, or None if the line is empty/comment.
        """
        if not line.strip() or line.lstrip().startswith("#") or line.startswith("\t"): return None
        leading = len(line) - len(line.lstrip(' '))
        return leading if leading > 0 else None

    def _logic_S06(self, content: str) -> int:
        """
        (S06) Determines the maximum line length in the file, excluding comments and docstrings.

        Args:
            content (str): The full file content.
        Returns:
            int: The length of the longest valid line of code.
        """
        """Logica S06: Max Line Length (senza docstring)"""
        content = re.sub(r"(?s)(?:'''(?:.*?)'''|\"\"\"(?:.*?)\"\"\")", "", content)
        max_len = 0
        for line in content.splitlines():
            s = line.rstrip("\n\r")
            if not s.strip() or s.lstrip().startswith("#"): continue
            max_len = max(max_len, len(s))
        return max_len

    def _logic_blank_lines_ast(self, tree, lines, node_type):
        """
        (S05/S11) Generic AST logic to count blank lines following specific node types.
        Used for functions (S05) and classes (S11).

        Args:
            tree (ast.AST): The parsed abstract syntax tree.
            lines (List[str]): The raw lines of the file.
            node_type (type): The AST node class to search for (e.g., ast.FunctionDef).
        Returns:
            List[int]: A list of blank line counts found after each instance of the node.
        """
        counts = []
        for node in ast.walk(tree):
            if isinstance(node, node_type):
                if not hasattr(node, 'end_lineno'): continue
                end_idx = node.end_lineno - 1
                blanks = 0
                idx = end_idx + 1
                while idx < len(lines):
                    if not lines[idx].strip():
                        blanks += 1
                        idx += 1
                    else:
                        break
                counts.append(blanks)
        return counts

    def _count_blanks_from_index(self, lines: List[str], start_idx: int) -> int:
        """
        Helper method to count consecutive blank lines starting from a given index.

        Args:
            lines (List[str]): The list of lines in the file.
            start_idx (int): The starting index to count blank lines from.

        Returns:
            int: The number of consecutive blank lines starting at start_idx.
        """
        count = 0
        i = start_idx
        while i < len(lines):
            if not lines[i].strip():
                count += 1
                i += 1
            else:
                break
        return count

    def _logic_S10(self, tree: ast.AST, lines: List[str]) -> List[int]:
        """
        (S10) Analyzes blank lines following import blocks.
        It uses a custom AST Visitor to detect consecutive import statements as "blocks" 
        and counts the blank lines appearing after each block.

        Args:
            tree (ast.AST): The parsed abstract syntax tree.
            lines (List[str]): The raw lines of the file.
        Returns:
            List[int]: A list of blank line counts after each import block.
        """
        # Usiamo una lista mutabile per raccogliere i risultati dalla closure/inner class
        blank_counts = []
        
        # Variabili di stato per il Visitor
        state = {'last_import_end_line': -1}

        class ImportVisitor(ast.NodeVisitor):
            def __init__(self, analyzer_instance):
                self.analyzer = analyzer_instance

            def visit_Import(self, node):
                self.process_node(node)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                self.process_node(node)
                self.generic_visit(node)

            def process_node(self, node):
                if not hasattr(node, 'end_lineno'): return
                
                # Indici 0-based
                current_start = node.lineno - 1
                current_end = node.end_lineno - 1
                
                last_end = state['last_import_end_line']

                # Se c'è un gap tra questo import e l'ultimo visto, il blocco precedente è finito
                # (current_start > last_end + 1 significa che c'è almeno una riga in mezzo)
                if last_end != -1 and current_start > (last_end + 1):
                    # Conta spazi dopo il BLOCCO PRECEDENTE
                    count = self.analyzer._count_blanks_from_index(lines, last_end + 1)
                    blank_counts.append(count)

                # Aggiorna l'ultimo import visto
                state['last_import_end_line'] = current_end

        visitor = ImportVisitor(self)
        visitor.visit(tree)

        # Gestione dell'ultimo blocco alla fine del file/visita
        if state['last_import_end_line'] != -1:
            count = self._count_blanks_from_index(lines, state['last_import_end_line'] + 1)
            blank_counts.append(count)
            
        return blank_counts

    def _logic_S12(self, tree: ast.AST, lines: List[str]) -> List[int]:
        """
        (S12) Analyzes blank lines following blocks of constant definitions.
        Constants are identified as assignments to names composed entirely of uppercase letters (e.g., MAX_RETRIES).

        Args:
            tree (ast.AST): The parsed abstract syntax tree.
            lines (List[str]): The raw lines of the file.
        Returns:
            List[int]: A list of blank line counts after each constant block.
        """
        blank_counts = []
        state = {'last_const_end_line': -1}

        def is_constant_name(name: str) -> bool:
            if not name or not isinstance(name, str): return False
            if not any(c.isalpha() for c in name): return False # Esclude "_" o "123"
            return all((c.isupper() or not c.isalpha()) for c in name)

        class ConstantVisitor(ast.NodeVisitor):
            def __init__(self, analyzer_instance):
                self.analyzer = analyzer_instance

            def visit_Assign(self, node):
                self.check_const(node)
                self.generic_visit(node)

            def visit_AnnAssign(self, node):
                self.check_const(node)
                self.generic_visit(node)

            def check_const(self, node):
                is_const = False
                # Verifica se è una costante
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name) and is_constant_name(t.id):
                            is_const = True
                            break
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Name) and is_constant_name(node.target.id):
                        is_const = True
                
                if not is_const: return
                if not hasattr(node, 'end_lineno'): return

                current_start = node.lineno - 1
                current_end = node.end_lineno - 1
                last_end = state['last_const_end_line']

                # Logica a blocchi (identica a S10)
                if last_end != -1 and current_start > (last_end + 1):
                    count = self.analyzer._count_blanks_from_index(lines, last_end + 1)
                    blank_counts.append(count)

                state['last_const_end_line'] = current_end

        visitor = ConstantVisitor(self)
        visitor.visit(tree)

        if state['last_const_end_line'] != -1:
            count = self._count_blanks_from_index(lines, state['last_const_end_line'] + 1)
            blank_counts.append(count)

        return blank_counts

    def _logic_S13(self, tree: ast.AST, lines: List[str]) -> List[Dict[str, Any]]:
        """
        (S13) Analyzes argument wrapping strategies in function calls.
        It extracts code snippets and classifies them into:
        - "same_line": All arguments on the same line.
        - "newline_every_arg": Every argument on a new line.
        - "mixed": A combination of the above.

        Args:
            tree (ast.AST): The parsed abstract syntax tree.
            lines (List[str]): The raw lines of the file.
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the 'strategy' and the raw code 'snippet'.
        """
        results = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                args = node.args + node.keywords
                if len(args) < 2: continue
                if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'): continue

                # 1. Estrazione Linee Argomenti
                arg_lines = []
                for arg in node.args:
                    arg_lines.append(arg.lineno)
                for kw in node.keywords:
                    if hasattr(kw, 'lineno'): arg_lines.append(kw.lineno) # Python 3.9+
                    elif hasattr(kw, 'value'): arg_lines.append(kw.value.lineno)
                
                if not arg_lines: continue
                
                # 2. Determinazione Strategia
                unique_lines = set(arg_lines)
                strategy = "mixed" # Default
                
                if len(unique_lines) == 1:
                    # Se tutti gli argomenti sono sulla stessa riga
                    # (Nota: potremmo controllare se sono sulla stessa riga della chiamata, 
                    # ma per ora manteniamo la logica semplice)
                    strategy = "same_line"
                elif len(unique_lines) == len(args):
                    # Se ogni argomento ha una riga unica
                    strategy = "newline_every_arg"
                
                # 3. Estrazione Snippet
                start_line = node.lineno - 1
                end_line = node.end_lineno - 1 # inclusive slice needs +1
                
                # Prendi le righe grezze dal file
                snippet_lines = lines[start_line : end_line + 1]
                snippet = "\n".join(snippet_lines).strip()
                
                results.append({
                    "strategy": strategy,
                    "snippet": snippet
                })
        
        return results

    # ==============================================================================
    # NUOVO METODO PRINCIPALE
    # ==============================================================================

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Orchestrates the full spacing analysis for a single file.

        It performs the following steps:
        1. Reads the file content.
        2. Iterates line-by-line to collect regex-based metrics (S01-S04, S07-S09).
        3. Parses the AST to collect structural metrics (S05, S10-S13).
        4. **Enforces Consistency:** For most metrics, if the file exhibits inconsistent styles 
           (e.g., sometimes 2 spaces after a comma, sometimes 1), the result is set to None 
           to ensure high-quality ground truth.
        5. Casts numeric results to float/int for dataset compatibility.

        Args:
            file_path (str): The absolute path to the file.

        Returns:
            Dict[str, Any]: A dictionary containing calculated values for S01-S13. 
                            Inconsistent metrics return None.
        """
        results = {}
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            lines = content.splitlines()
            
            # 1. Analisi Riga per Riga (Accumulatori)
            # Raccogliamo tutti i valori trovati nel file per verificare la coerenza dopo
            collectors = {
                "S01": [], "S02": [], "S03": [], "S04": [], "S07": [],
                "S08": [], "S09": []
            }

            for i, line in enumerate(lines):
                # S01, S02, S03, S04, S07
                v1 = self._logic_S01(line)
                if v1 is not None: collectors["S01"].append(v1)
                
                v2 = self._logic_S02(line)
                if v2 is not None: collectors["S02"].append(v2)
                
                v3 = self._logic_commas(line, "before")
                if v3 is not None: collectors["S03"].append(v3)
                
                v4 = self._logic_commas(line, "after")
                if v4 is not None: collectors["S04"].append(v4)
                
                v7 = self._logic_S07(line)
                if v7 is not None: collectors["S07"].append(v7)

                # S08/S09 (Commenti)
                stripped = line.strip()
                if stripped.startswith("#") and not stripped.startswith("#!"):
                    # S08 (Above)
                    j = i - 1
                    above = 0
                    while j >= 0 and not lines[j].strip():
                        above += 1
                        j -= 1
                    collectors["S08"].append(above)
                    
                    # S09 (Below)
                    k = i + 1
                    below = 0
                    while k < len(lines) and not lines[k].strip():
                        below += 1
                        k += 1
                    collectors["S09"].append(below)

            # 2. Controllo Consistenza (Regex/Line based)
            # Se tutti i valori raccolti sono uguali, salva il valore. Altrimenti None.
            for key, vals in collectors.items():
                if vals and len(set(vals)) == 1:
                    # Caso speciale S07: deve essere il minimo comune divisore (step)
                    if key == "S07":
                        unique_vals = set(vals)
                        smallest = min(unique_vals)
                        if all(v % smallest == 0 for v in unique_vals):
                            results[key] = float(smallest)
                        else:
                            results[key] = None
                    else:
                        results[key] = float(vals[0])
                else:
                    results[key] = None

            # 3. Analisi S06 (Max Length) - Non richiede consistenza
            results["S06"] = float(self._logic_S06(content))

            # 4. Analisi AST (S05, S10, S11, S12, S13)
            if content.strip():
                try:
                    tree = ast.parse(content)
                    
                    # S05 (Funzioni)
                    res_s05 = self._logic_blank_lines_ast(tree, lines, (ast.FunctionDef, ast.AsyncFunctionDef))
                    if res_s05 and len(set(res_s05)) == 1:
                        results["S05"] = float(res_s05[0])
                    else:
                        results["S05"] = None
                    
                    # S11 (Classi)
                    res_s11 = self._logic_blank_lines_ast(tree, lines, ast.ClassDef)
                    if res_s11 and len(set(res_s11)) == 1:
                        results["S11"] = float(res_s11[0])
                    else:
                        results["S11"] = None

                    # S10 (Imports)
                    res_s10 = self._logic_S10(tree, lines)
                    # Consistenza: se ci sono blocchi e tutti hanno lo stesso spazio dopo
                    if res_s10 and len(set(res_s10)) == 1:
                        results["S10"] = float(res_s10[0])
                    else:
                        results["S10"] = None

                    # S12 (Costanti)
                    res_s12 = self._logic_S12(tree, lines)
                    if res_s12 and len(set(res_s12)) == 1:
                        results["S12"] = float(res_s12[0])
                    else:
                        results["S12"] = None

                    # S13 (Chiamate Funzione)
                    # Qui non cerchiamo consistenza, salviamo TUTTI i campioni trovati.
                    # Il benchmark sceglierà poi uno a caso da questa lista.
                    results["_raw_S13"] = self._logic_S13(tree, lines)

                except SyntaxError:
                    pass

        except Exception as e:
            # print(f"Errore file {file_path}: {e}")
            return {}

        return results