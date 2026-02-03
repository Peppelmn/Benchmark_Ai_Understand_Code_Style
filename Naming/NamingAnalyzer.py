import ast
from typing import Any, Dict, List, Set, Optional
from CodebaseAnalyzer import CodebaseAnalyzer

class _NameCollector(ast.NodeVisitor):
    """
    An AST NodeVisitor subclass designed to traverse the Abstract Syntax Tree of a Python file.
    It collects all unique identifiers found in class definitions, function definitions, 
    arguments, assignments, and annotated assignments.
    """
    def __init__(self):
        self.names: Set[str] = set()

    def add_name(self, name: str):
        if name:
            self.names.add(name)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.add_name(node.name)
        self.generic_visit(node) 

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.add_name(node.name)
        self.generic_visit(node) 

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.add_name(node.name)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg):
        self.add_name(node.arg)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.add_name(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self.add_name(node.target.id)
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr):
        if isinstance(node.target, ast.Name):
            self.add_name(node.target.id)
        self.generic_visit(node)


class NamingAnalyzer(CodebaseAnalyzer):
    """
    Analyzes Python source code to evaluate adherence to various naming conventions 
    (snake_case, camelCase, PascalCase). It utilizes AST parsing to accurately identify 
    variable, function, and class names, distinguishing them from string literals or comments.
    """
    def __init__(self, codebase_path: str, max_token_limit: float = float('inf')):
        """
        Initializes the NamingAnalyzer.

        Args:
            codebase_path (str): The root path of the codebase to be analyzed.
            max_token_limit (float, optional): A limit on the number of tokens to process. 
                                               Defaults to infinity for static dataset generation.
        """
        super().__init__(codebase_path, max_token_limit)
        self._file_naming_cache: Dict[str, Dict[str, Any]] = {}
                
    # ==============================================================================
    # LOGICA HELPER (Validazione stringhe)
    # ==============================================================================

    def _is_pascal_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        return "_" not in name and name[0].isupper() and any(c.islower() for c in name)

    def _is_camel_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        return "_" not in name and name[0].islower() and any(c.isupper() for c in name)

    def _is_snake_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        return name.islower() and "_" in name

    def _get_naming_counts_for_file(self, file_path: str) -> Dict[str, Dict]:
        """
        Parses a specific file using Python's AST module to collect all identifiers and classifies 
        them according to naming conventions (Pascal, camel, snake, constants, etc.).
        Results are cached to improve performance on repeated calls.

        Args:
            file_path (str): The absolute path to the file to analyze.

        Returns:
            Dict[str, Dict]: A dictionary containing counts and lists of names found for each category.
                             Example: {"snake_case": {"count": 10, "names": ["my_var", ...]}, ...}

        Raises:
            Exception: Captures and suppresses parsing errors (e.g., SyntaxError in the source file), 
                       returning an empty count dictionary in such cases.
        """
        if file_path in self._file_naming_cache:
            return self._file_naming_cache[file_path]
        
        counts = {
            "PascalCase": {"count": 0, "names": []},
            "camelCase":  {"count": 0, "names": []},
            "snake_case": {"count": 0, "names": []},
            "constants":  {"count": 0, "names": []},
            "special":    {"count": 0, "names": []},
            "other":      {"count": 0, "names": []}
        }
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            tree = ast.parse(content)
            collector = _NameCollector()
            collector.visit(tree)
            all_names_in_file = collector.names
            
        except Exception:
            # In caso di errore AST o I/O, restituiamo il dict vuoto
            # self.parse_error_count += 1 (opzionale gestirlo qui)
            self._file_naming_cache[file_path] = counts
            return counts
        
        for original_name in all_names_in_file:
            
            # Costanti (TUTTO MAIUSCOLO)
            if original_name.isupper():
                counts["constants"]["count"] += 1
                counts["constants"]["names"].append(original_name)
                continue

            # Dunder methods (__init__)
            if original_name.startswith('__') and original_name.endswith('__'):
                counts["special"]["count"] += 1
                counts["special"]["names"].append(original_name)
                continue

            # Pulizia per classificazione standard
            name_to_classify = original_name.lstrip('_')

            if self._is_pascal_case(name_to_classify):
                counts["PascalCase"]["count"] += 1
                counts["PascalCase"]["names"].append(original_name)

            elif self._is_camel_case(name_to_classify):
                counts["camelCase"]["count"] += 1
                counts["camelCase"]["names"].append(original_name)

            elif self._is_snake_case(name_to_classify):
                counts["snake_case"]["count"] += 1
                counts["snake_case"]["names"].append(original_name)

            else:
                counts["other"]["count"] += 1
                counts["other"]["names"].append(original_name)
        
        self._file_naming_cache[file_path] = counts
        return counts

    # ==============================================================================
    # NUOVO METODO PRINCIPALE (Analisi file singolo)
    # ==============================================================================

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyzes a single file to calculate all Naming benchmark metrics (N01-N09).
        It transforms raw classification counts into the specific format required by the benchmark dataset,
        providing both calculated float values for static questions and raw lists for dynamic sampling.

        Args:
            file_path (str): The absolute path to the file to analyze.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - Static Answers (float): N01 (snake count), N02 (camel count), N03 (Pascal count), 
                  N07 (non-standard count), N09 (max length).
                - Dominant Convention (str/None): N04.
                - Raw Data (list): Keys starting with '_raw_' containing lists of names for 
                  dynamic question generation (N05, N06, N08).
        """
        results = {}
        
        # 1. Ottieni l'analisi grezza dal metodo helper
        counts_data = self._get_naming_counts_for_file(str(file_path))
        
        # --- Risposte Numeriche Dirette (Ground Truth) ---
        results["N01"] = float(counts_data["snake_case"]["count"])  # Count snake
        results["N02"] = float(counts_data["camelCase"]["count"])   # Count camel
        results["N03"] = float(counts_data["PascalCase"]["count"])  # Count Pascal
        results["N07"] = float(counts_data["other"]["count"])       # Count Non-Standard

        # --- N04: Convenzione Dominante ---
        # Somma totale nomi classificabili
        total_classifiable = results["N01"] + results["N02"] + results["N03"]
        
        # Applichiamo la soglia minima (es. 5 nomi) per dare una risposta sensata
        if total_classifiable >= 5:
            mapping = {
                "snake_case": results["N01"],
                "camelCase": results["N02"],
                "PascalCase": results["N03"]
            }
            # Trova la chiave con il valore massimo
            results["N04"] = max(mapping, key=mapping.get)
        else:
            results["N04"] = None

        # --- N09: Nome più lungo ---
        # Aggreghiamo tutti i nomi trovati in un'unica lista
        all_names = []
        for cat in counts_data.values():
            all_names.extend(cat["names"])
            
        if all_names:
            longest = max(all_names, key=len)
            results["N09"] = float(len(longest))
        else:
            results["N09"] = 0.0

        # --- Dati Grezzi per Benchmark Dinamico ---
        # Queste liste servono per generare le domande N05, N06, N08
        # che richiedono di scegliere un nome specifico (es. "Il nome 'myVar' è standard?")
        
        results["_raw_names_snake"] = counts_data["snake_case"]["names"]
        results["_raw_names_camel"] = counts_data["camelCase"]["names"]
        results["_raw_names_pascal"] = counts_data["PascalCase"]["names"]
        results["_raw_names_other"] = counts_data["other"]["names"]
        results["_raw_constants"] = counts_data["constants"]["names"] # Per N08
        results["_raw_all_names"] = all_names # Per N06 (pesca un nome a caso da tutto il file)

        return results