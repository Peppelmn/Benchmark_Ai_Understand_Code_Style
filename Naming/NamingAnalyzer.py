import ast
import random
from CodebaseAnalyzer import CodebaseAnalyzer
from DataClassesDefiner import Question, Answer
from typing import Set, Dict, Tuple

class _NameCollector(ast.NodeVisitor):
    """
    Un NodeVisitor che raccoglie tutti i nomi unici
    da Classi, Funzioni, Argomenti e Variabili in un singolo file.
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
    """Analizza la codebase su aspetti di naming, trova la risposta corretta per le domande"""

    def __init__(self, codebase_path: str):
        super().__init__(codebase_path)
        self._file_naming_cache: Dict[str, Dict[str, int]] = {}
        self.parse_error_count = 0

    def analyze(self, question: Question) -> Answer:
        
        if question.id == "N01":
            return Answer(self.question_N01()[1] , True)
        elif question.id == "N02":
            return Answer(self.question_N02()[1], True)
        elif question.id == "N03":
            return Answer(self.question_N03()[1], True)
        elif question.id == "N04":
            return Answer(self.question_N04()[1], True)
        elif question.id == "N05":
            return Answer(self.question_N05()[1], True)
        else:
            raise ValueError(f"ID domanda Naming sconosciuto: {question.id}")
                
    
    def _is_pascal_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: return False
        return (
            "_" not in name and
            name[0].isupper()
        )

    def _is_camel_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: return False
        return (
            "_" not in name and
            name[0].islower() and
            any(c.isupper() for c in name)
        )

    def _is_snake_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: return False
        return name.islower()

    def _get_naming_counts_for_file(self, file_path: str) -> Dict[str, Dict]:
        """
        Esegue l'analisi AST su un SINGOLO file e classifica ogni nome.
        Utilizza una cache per evitare di ri-analizzare.
        
        RESTITUISCE: 
        Un dizionario strutturato:
        { "snake_case": {"count": 5, "names": ["var1", ...]}, ... }
        """
        if file_path in self._file_naming_cache:
            return self._file_naming_cache[file_path]
        
        counts = {
            "PascalCase": {"count": 0, "names": []},
            "camelCase":  {"count": 0, "names": []},
            "snake_case":  {"count": 0, "names": []},
            "constants":   {"count": 0, "names": []},
            "special":     {"count": 0, "names": []},
            "other":       {"count": 0, "names": []}
        }
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            collector = _NameCollector()
            collector.visit(tree)
            all_names_in_file = collector.names
            
        except Exception as e:
            self._file_naming_cache[file_path] = counts
            return counts

        for name in all_names_in_file:
            if name.isupper():
                counts["constants"]["count"] += 1
                counts["constants"]["names"].append(name)
            elif name.startswith('__') and name.endswith('__'):
                counts["special"]["count"] += 1
                counts["special"]["names"].append(name)
            elif name.startswith('_'):
                counts["special"]["count"] += 1
                counts["special"]["names"].append(name)
            elif self._is_pascal_case(name):
                counts["PascalCase"]["count"] += 1
                counts["PascalCase"]["names"].append(name)
            elif self._is_camel_case(name):
                counts["camelCase"]["count"] += 1
                counts["camelCase"]["names"].append(name)
            elif self._is_snake_case(name):
                counts["snake_case"]["count"] += 1
                counts["snake_case"]["names"].append(name)
            else:
                counts["other"]["count"] += 1
                counts["other"]["names"].append(name)

        self._file_naming_cache[file_path] = counts
        return counts

    def _find_random_file_for_convention(self, convention: str):
        """
        Trova un file *casuale* nella codebase che contenga almeno un
        esempio di una specifica convenzione (es. "snake_case") E
        che non superi le 1000 righe di codice.
        
        Restituisce: (percorso_file_relativo, conteggio, lista_di_nomi)
        """
        candidate_files = []
        max_lines = 1000

        for file_path in self.python_files:
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                if len(lines) > max_lines:
                    continue
            
            except Exception as e:
                print(f"[!] Errore leggendo {file_path} per contare le righe: {e}")
                continue

            counts = self._get_naming_counts_for_file(str(file_path))
            
            default_data = {"count": 0, "names": []} 
            
            convention_data = counts.get(convention, default_data)
            current_count = convention_data["count"]
            current_names = convention_data["names"]
            
            # Se questo file ha almeno un esempio, è un candidato
            if current_count > 0:
                relative_path = file_path.relative_to(self.codebase_path)
                candidate_files.append((str(relative_path), current_count, current_names))

        if not candidate_files:
            print(f"[ATTENZIONE] NamingAnalyzer non ha trovato file per '{convention}' (con < {max_lines} righe)")
            return None 

        return random.choice(candidate_files)

    def question_N01(self):
        """Trova un file casuale con nomi snake_case e il loro numero."""
        return self._find_random_file_for_convention("snake_case")

    def question_N02(self):
        """Trova un file casuale con nomi camelCase e il loro numero."""
        return self._find_random_file_for_convention("camelCase")

    def question_N03(self):
        """Trova un file casuale con nomi PascalCase e il loro numero."""
        return self._find_random_file_for_convention("PascalCase")
    
    def question_N04(self):
        """
        Trova il file (< 1000 righe) con il maggior numero
        totale di nomi classificabili (snake, camel, pascal) e
        restituisce la convenzione dominante di QUEL file.
        
        Restituisce: (percorso_file_relativo, "convenzione_dominante")
        """
        best_file_path = None
        dominant_convention = "other"
        max_total_names = 0 
        max_lines = 1000

        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if len(f.readlines()) > max_lines:
                        continue
            except Exception as e:
                print(f"[!] Errore leggendo {file_path} per contare le righe: {e}")
                continue
            
            # Ottiene i dati del file (dalla cache o analizzandolo)
            counts_data = self._get_naming_counts_for_file(str(file_path))
            
            # Estrae i conteggi
            snake_count = counts_data["snake_case"]["count"]
            camel_count = counts_data["camelCase"]["count"]
            pascal_count = counts_data["PascalCase"]["count"]
            
            total_classifiable_names = snake_count + camel_count + pascal_count

            # Troviamo il file con il maggior numero di nomi in totale
            # (ignoriamo file con meno di 10 nomi per evitare file banali)
            if total_classifiable_names > max_total_names and total_classifiable_names > 10:
                max_total_names = total_classifiable_names
                best_file_path = file_path
                
                # Ora determina la convenzione dominante PER QUESTO file
                convention_counts = {
                    "snake_case": snake_count,
                    "camelCase": camel_count,
                    "PascalCase": pascal_count
                }
                
                # Trova la chiave (il nome della convenzione) con il valore (conteggio) massimo
                dominant_convention = max(convention_counts, key=convention_counts.get)

        if best_file_path is None:
            print(f"[ATTENZIONE] NamingAnalyzer non ha trovato file con > 10 nomi per N04")
            return None # Restituisce None come le altre funzioni

        relative_path = best_file_path.relative_to(self.codebase_path)
        
        # Restituisce il file trovato e la sua convenzione vincente (es. "snake_case")
        return (str(relative_path), dominant_convention)
    
    def question_N05(self):
        random_convention = random.choice(["snake_case", "camelCase", "PascalCase"])
        random_file = self._find_random_file_for_convention(random_convention)
        random_element = random.choice(random_file[2]) if random_file else None
        return random_file[0], random_convention, random_element if random_element else None
    
    