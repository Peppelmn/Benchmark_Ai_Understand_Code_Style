import ast
import random
from CodebaseAnalyzer import CodebaseAnalyzer
from DataClassesDefiner import Question, Answer
from typing import Set, Dict, Tuple

class _NameCollector(ast.NodeVisitor):
    """
    An AST NodeVisitor that collects all unique identifiers from Classes, Functions, Arguments, and Variables within a single file.
    """
    # Un node visitor cammina l'albero AST e ogni volta che incontra un nodo di interesse, chiama il metodo corrispondente "visit_<NodeType>".
    def __init__(self):
        self.names: Set[str] = set()

    def add_name(self, name: str):
        if name:
            self.names.add(name)

    # Visita un nodo di tipo class definition
    def visit_ClassDef(self, node: ast.ClassDef):
        self.add_name(node.name)
        self.generic_visit(node) # Continua a visitare i nodi figli

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.add_name(node.name)
        self.generic_visit(node) 

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.add_name(node.name)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg):
        self.add_name(node.arg)

    # Visita un nodo di tipo assegnamento (es. x = 10)
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.add_name(target.id)
        self.generic_visit(node)

    # Visita un nodo di tipo assegnamento con annotazione (es. x: int = 10)
    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self.add_name(node.target.id)
        self.generic_visit(node)

    # Visita un nodo di tipo espressione nominata ((x := 10) > 5 è condizione vera, assegna 10 a x e ritorna 10)
    def visit_NamedExpr(self, node: ast.NamedExpr):
        if isinstance(node.target, ast.Name):
            self.add_name(node.target.id)
        self.generic_visit(node)


class NamingAnalyzer(CodebaseAnalyzer):

    def __init__(self, codebase_path: str, max_token_limit, max_results_per_question = 10):
        super().__init__(codebase_path, max_token_limit, max_results_per_question)
        self._file_naming_cache = {}
                
    def _is_pascal_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        
        return (
            "_" not in name and
            name[0].isupper() and
            any(c.islower() for c in name)
        )

    def _is_camel_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        
        return (
            "_" not in name and
            name[0].islower() and
            any(c.isupper() for c in name)
        )

    def _is_snake_case(self, name: str) -> bool:
        if not name or name.startswith("_") or len(name) < 2: 
            return False
        return (
            name.islower() and
            "_" in name
        )

    def _get_naming_counts_for_file(self, file_path: str) -> Dict[str, Dict]:
        """
        Parses a specific file using AST to collect all names and classifies them according to naming conventions (Pascal, camel, snake, constants, etc.).

        Args:
            file_path (str): The absolute path to the file to analyze.

        Returns: A dictionary containing counts and lists of names found for each convention category.
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
            self.parse_error_count += 1 
            self._file_naming_cache[file_path] = counts
            return counts
        
        for original_name in all_names_in_file:
            
            if original_name.isupper():
                counts["constants"]["count"] += 1
                counts["constants"]["names"].append(original_name)
                continue

            if original_name.startswith('__') and original_name.endswith('__'):
                counts["special"]["count"] += 1
                counts["special"]["names"].append(original_name)
                continue

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

    def _find_files_for_convention(self, convention: str):
        """
        Scans the codebase to find files containing names that follow a specific convention.

        Args:
            convention (str): The convention key to search for (e.g., "snake_case", "PascalCase").

        Returns: A list of tuples containing (relative_path, count, list_of_names).
        """
        candidate_files = []

        for file_path in self.python_files:
            
            if len(candidate_files) >= self.max_results_per_question:
                break 

            counts = self._get_naming_counts_for_file(str(file_path))
            
            default_data = {"count": 0, "names": []} 
            
            convention_data = counts.get(convention, default_data) # Ottieni i dati per la convenzione specificata, se non esistono dati usa default
            current_count = convention_data["count"]
            current_names = convention_data["names"]
            
            if current_count > 0:
                relative_path = file_path.relative_to(self.codebase_path)
                candidate_files.append((str(relative_path), float(current_count), current_names))

        if not candidate_files:
            print(f"[ATTENZIONE] NamingAnalyzer non ha trovato file per '{convention}'")
            return None 

        return candidate_files

    def question_N01(self):
        """
        Identifies files containing names following the snake_case convention.

        Returns: A list of files with a count of snake_case names found.
        """
        return self._find_files_for_convention("snake_case")

    def question_N02(self):
        """
        Identifies files containing names following the camelCase convention.

        Returns: A list of files with a count of camelCase names found.
        """
        return self._find_files_for_convention("camelCase")

    def question_N03(self):
        """
        Identifies files containing names following the PascalCase convention.

        Returns: A list of files with a count of PascalCase names found.
        """
        return self._find_files_for_convention("PascalCase")
    
    def question_N04(self):
        """
        Analyzes files with at least 5 classifiable names to determine the dominant naming convention used within that specific file.

        Returns: A list of tuples containing (relative_file_path, dominant_convention).
        """
        dominant_convention = "other"
        candidate_files = []

        for file_path in self.python_files:

            if len(candidate_files) >= self.max_results_per_question:
                break
            
            counts_data = self._get_naming_counts_for_file(str(file_path))
            
            snake_count = counts_data["snake_case"]["count"]
            camel_count = counts_data["camelCase"]["count"]
            pascal_count = counts_data["PascalCase"]["count"]
            
            total_classifiable_names = snake_count + camel_count + pascal_count
            if total_classifiable_names >= 5:
                
                convention_counts = {
                    "snake_case": snake_count,
                    "camelCase": camel_count,
                    "PascalCase": pascal_count
                }
                
                # Trova la convenzione con il conteggio massimo. Il parametro "key" specifica che il confronto deve essere fatto sui valori del dizionario, altrimenti confronta le chiavi (stringhe).
                dominant_convention = max(convention_counts, key=convention_counts.get) 
                relative_path = str(file_path.relative_to(self.codebase_path))

                candidate_files.append((relative_path, dominant_convention))

        if not candidate_files:
            print(f"[ATTENZIONE] NamingAnalyzer non ha trovato file con > 10 nomi per N04")
            return None

        return candidate_files
    
    def question_N05(self):
        """
        Generates random samples of names fitting specific conventions (snake, camel, pascal) from the codebase.

        Returns: A list of tuples containing (target_file, correct_convention, example_name).
        """
        results = []
        
        conventions = ["snake_case", "camelCase", "PascalCase"]

        snake_candidates = self._find_files_for_convention("snake_case")
        camel_candidates = self._find_files_for_convention("camelCase")
        pascal_candidates = self._find_files_for_convention("PascalCase")

        while len(results) < self.max_results_per_question:
            
            random_convention = random.choice(conventions)
            
            if random_convention == "snake_case":
                candidates = snake_candidates
            elif random_convention == "camelCase":
                candidates = camel_candidates
            else:
                candidates = pascal_candidates
            
            if not candidates:
                continue

            if isinstance(candidates, list):
                chosen_file_data = random.choice(candidates)
            else:
                chosen_file_data = candidates

            file_path = chosen_file_data[0]
            names_list = chosen_file_data[2]

            if not names_list:
                continue

            random_element = random.choice(names_list)
            
            item = (file_path, random_convention, random_element)
            
            if item not in results:
                results.append(item)

        if len(results) < self.max_results_per_question:
            print(f"[WARN] question_N05 ha trovato solo {len(results)}/{self.max_results_per_question} campioni.")

        return results
    
    def question_N06(self):
        """
        Selects a random name from a random file and determines if it adheres to any of the three main conventions (snake, camel, pascal).

        Returns: A list of tuples containing (file_path, is_standard_bool_string, selected_name).
        """
        candidate_files = []
        
        while len(candidate_files) < self.max_results_per_question:

            try:
                file_path = random.choice(self.python_files)

                counts_data = self._get_naming_counts_for_file(str(file_path))
                
                all_names_in_file = (
                    counts_data["PascalCase"]["names"] +
                    counts_data["camelCase"]["names"] +
                    counts_data["snake_case"]["names"] +
                    counts_data["constants"]["names"] +
                    counts_data["other"]["names"] +
                    counts_data["special"]["names"]
                )

                if not all_names_in_file:
                    continue 

                random_name = random.choice(all_names_in_file)
                
                name_to_test = random_name.lstrip('_')
                
                is_standard = (
                    self._is_pascal_case(name_to_test) or
                    self._is_camel_case(name_to_test) or
                    self._is_snake_case(name_to_test)
                )
                
                relative_path = file_path.relative_to(self.codebase_path)
                candidate_files.append((str(relative_path), str(is_standard).lower(), random_name))

            except Exception as e:
                print(f"[ERRORE] question_N06 ha incontrato un errore: {e}")
                continue
        
        return candidate_files if candidate_files else None
    
    def question_N07(self):
        """
        Identifies files containing names that do not follow standard conventions (classified as "other").

        Returns: A list of files containing non-standard identifier names.
        """
        return self._find_files_for_convention("other")
    
    def question_N08(self):
        """
        Analyzes constant names (UPPERCASE) to determine if they contain underscores.

        Returns: A list of tuples containing (file_path, "true"/"false", constant_name).
        """
        results = []
        

        for file_path in self.python_files:
            if len(results) >= self.max_results_per_question:
                break

            counts_data = self._get_naming_counts_for_file(str(file_path))
            constants_list = counts_data["constants"]["names"]

            if not constants_list:
                continue

            random_constant = random.choice(constants_list)

            answer = "true" if "_" in random_constant else "false"
            
            relative_path = str(file_path.relative_to(self.codebase_path))

            results.append((relative_path, answer, random_constant))

        return results
    
    def question_N09(self):
        """
        Identifies the longest identifier name present within a randomly selected file.

        Returns: A list of tuples containing (file_path, max_length, longest_name).
        """
        candidate_files = []
        
        while len(candidate_files) < self.max_results_per_question:

            try:
                file_path = random.choice(self.python_files)
                counts_data = self._get_naming_counts_for_file(str(file_path))
                
                all_names_in_file = (
                    counts_data["PascalCase"]["names"] +
                    counts_data["camelCase"]["names"] +
                    counts_data["snake_case"]["names"] +
                    counts_data["constants"]["names"] +
                    counts_data["other"]["names"] +
                    counts_data["special"]["names"]
                )

                if not all_names_in_file:
                    continue

                longest_name = max(all_names_in_file, key=len)
                max_length = len(longest_name)
                
                relative_path = file_path.relative_to(self.codebase_path)
                candidate_files.append((str(relative_path), float(max_length), longest_name))

            except Exception as e:
                continue

        return candidate_files if candidate_files else None