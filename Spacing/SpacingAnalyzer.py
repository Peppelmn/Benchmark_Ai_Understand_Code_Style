import re
import string
from CodebaseAnalyzer import CodebaseAnalyzer
from DataClassesDefiner import Question, Answer
import random
import ast

class SpacingAnalyzer(CodebaseAnalyzer):

    def __init__(self, codebase_path: str, max_token_limit, max_results_per_question = 10):
        super().__init__(codebase_path, max_token_limit, max_results_per_question)

    def _find_consistent_files(self, analyze_function, per_line=True):
        """
        Scans codebase files by applying a specific analysis function and selects only those files where the analysis result is consistent.

        Args:
            analyze_function (callable): The function to apply to each line or file.
            per_line (bool): If True, analyzes the file line by line; otherwise, analyzes the whole file path.

        Returns: A list of tuples (relative_path, consistent_value, None).
        """
        consistent_files = []

        for path in self.python_files:

            if len(consistent_files) >= self.max_results_per_question:
                break

            try:
                if per_line:
                    values = []
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for _, line in enumerate(f):
                            val = analyze_function(line)
                            if val is not None:
                                if isinstance(val, list):
                                    if len(val) == 0:
                                        continue
                                    val = sum(val) / len(val)
                                values.append(round(val, 2))
                else:
                    val = analyze_function(path)
                    if val is None:
                        continue
                    if isinstance(val, list):
                        values = val
                    else:
                        values = [val]

                if not values:
                    continue

                # Verifica se tutti i valori nella lista sono identici (consistenza)
                if len(set(values)) == 1:
                    relative_path = path.relative_to(self.codebase_path)
                    consistent_files.append((str(relative_path), float(values[0]), None))

            except Exception as e:
                print(f"[!] Errore analizzando {path}: {e}")

        return consistent_files

    def question_S01(self):
        """
        Analyzes spacing around operators (assignment, comparison, mathematical) within code lines, ignoring strings and function calls.

        Returns: A list of files where operator spacing is consistent, including the average number of spaces detected.
        """
        def count_spaces_between_tokens(line):

            # Rimuove commenti e spazi iniziali/finali
            line = line.split('#')[0].rstrip()
            line = line.lstrip()
            if not line.strip():
                return None

            line = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", line)

            if "=" not in line or any(op in line for op in ["==", "!=", ">=", "<="]):
                return None

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
        """
        Analyzes token spacing within control structure conditions (if, while, for), ignoring strings and nested calls.

        Returns: A list of files where spacing in conditions is consistent, including the average number of spaces detected.
        """
        def count_spaces_in_control_structure(line):
            line = line.split('#')[0].rstrip()
            line = line.lstrip()
            if not line.strip():
                return None

            control_keywords = ('if', 'while', 'for')
            if not any(line.startswith(keyword + ' ') for keyword in control_keywords):
                return None

            try:
                keyword = next(k for k in control_keywords if line.startswith(k + ' '))
                condition = line[len(keyword):].split(':')[0].strip()

                if keyword == 'for' and ' in ' in condition:
                    condition = condition.split(' in ')[1]

                condition = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", condition)
                
                def collapse_calls(s):
                    pattern = re.compile(r"([A-Za-z_]\w*)\s*\([^()]*\)")
                    while True:
                        new_s = pattern.sub(lambda m: m.group(1) + "(__CALL__)", s)
                        if new_s == s:
                            break
                        s = new_s
                    return s

                condition = collapse_calls(condition)

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
        """
        Helper method that analyzes the number of spaces present around commas in function argument lists.

        Args:
            count_before_after (str): "before" to count spaces preceding the comma, "after" for those following it.

        Returns: A list of files with consistent spacing around commas.
        """
        def count_spaces_around_commas(line):
            line = line.split('#')[0].rstrip()
            line = line.lstrip()
            if not line.strip():
                return None

            func_pattern = r'(?:def\s+\w+|[\w.]+)\s*\(([^)]+)\)'
            matches = re.findall(func_pattern, line)
            
            if not matches:
                return None

            space_counts = []
            
            for args_str in matches:
                args_cleaned = re.sub(r"f?(['\"])(?:\\.|(?!\1).)*\1", "__STR__", args_str)
                
                parts = args_cleaned.split(',')
                
                if len(parts) <= 1:
                    continue
                
                if count_before_after == "before":
                    for i in range(len(parts) - 1):
                        part = parts[i]
                        trailing_spaces = len(part) - len(part.rstrip(' '))
                        space_counts.append(trailing_spaces)
                else:
                    for i in range(1, len(parts)):
                        part = parts[i]
                        leading_spaces = len(part) - len(part.lstrip(' '))
                        space_counts.append(leading_spaces)
            
            return sum(space_counts) / len(space_counts) if space_counts else None
        
        return self._find_consistent_files(count_spaces_around_commas)
    
    def question_S03(self):
        """
        Specifically analyzes the number of spaces present *before* a comma in function arguments.

        Returns: A list of files where pre-comma spacing is consistent (e.g., 0 or 1).
        """
        return self.get_spaces_around_commas("before")
    
    def question_S04(self):
        """
        Specifically analyzes the number of spaces present *after* a comma in function arguments.

        Returns: A list of files where post-comma spacing is consistent (e.g., 1).
        """
        return self.get_spaces_around_commas("after")

    def question_S05(self):
        """
        Uses AST to locate function definition ends and counts how many blank lines immediately follow the function body.

        Returns: A list of files that use a consistent number of blank lines after functions.
        """
        def count_blank_lines_after_function(file_path):
            blank_counts = []
            
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

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_end_line_index = node.end_lineno - 1
                    
                    blank_count = 0
                    i = func_end_line_index + 1
                    
                    while i < len(lines):
                        if not lines[i].strip():
                            blank_count += 1
                            i += 1
                        else:
                            break
                    
                    blank_counts.append(blank_count)

            return blank_counts
        
        return self._find_consistent_files(count_blank_lines_after_function, per_line=False)
    
    def question_S06(self):
        """
        Calculates the maximum line length in a file, excluding multi-line docstrings and comments from the count.

        Returns: A list of files with their detected maximum line length.
        """
        def max_line_length(file_path):
            max_length = 0
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    content = re.sub(r"(?s)(?:'''(?:.*?)'''|\"\"\"(?:.*?)\"\"\")", "", content)

                    for _, line in enumerate(content.splitlines()):
                        stripped = line.rstrip("\n\r")
                        if not stripped.strip():
                            continue
                        if stripped.lstrip().startswith("#"):
                            continue
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
                consistent_files.append((str(relative_path), float(max_len), None))
                if len(consistent_files) >= self.max_results_per_question:
                    break
        return consistent_files

    def question_S07(self):
        """
        Analyzes indentation levels to determine the dominant indentation step used in the file.

        Returns: A list of files that maintain consistent indentation.
        """
        def count_indent_spaces(line):
            if not line.strip():
                return None
            if line.lstrip().startswith("#"):
                return None
            if line.startswith("\t"):
                return None
            leading_spaces = len(line) - len(line.lstrip(' '))
            if leading_spaces == 0:
                return None
            return leading_spaces

        def analyze_file(file_path):
            indent_values = []
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for _, line in enumerate(f):
                        val = count_indent_spaces(line)
                        if val is not None:
                            indent_values.append(val)
            except Exception as e:
                print(f"[!] Errore nel file {file_path}: {e}")
                return []

            if not indent_values:
                return []

            diffs = [v for v in set(indent_values) if v > 0]
            if not diffs:
                return []

            smallest = min(diffs)
            if all(v % smallest == 0 for v in diffs):
                return [smallest]
            return []

        return self._find_consistent_files(analyze_file, per_line=False)

    def get_blank_lines_around_comments(self, count_above_below: str):
        """
        Helper method that counts blank lines immediately above or below comments.

        Args:
            count_above_below (str): "above" to count blank lines before a comment, "below" for those after it.

        Returns: A list of files where the number of blank lines around comments is consistent.
        """
        def count_blank_lines_around_comments(file_path):
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

                if stripped.startswith("#") and not stripped.startswith("#!"):
                    j = i - 1
                    count_above = 0
                    while j >= 0 and not lines[j].strip():
                        count_above += 1
                        j -= 1

                    k = i + 1
                    count_below = 0
                    while k < len(lines) and not lines[k].strip():
                        count_below += 1
                        k += 1

                    blanks_above.append(count_above)
                    blanks_below.append(count_below)

            if not blanks_above and not blanks_below:
                return None

            if count_above_below == "above":
                return blanks_above if blanks_above else 0
            elif count_above_below == "below":
                return blanks_below if blanks_below else 0
            
        return self._find_consistent_files(count_blank_lines_around_comments, per_line=False)

    def question_S08(self):
        """
        Analyzes the number of blank lines present immediately above a comment.

        Returns: A list of files that maintain consistent vertical spacing before comments.
        """
        return self.get_blank_lines_around_comments("above")
    
    def question_S09(self):
        """
        Analyzes the number of blank lines present immediately below a comment.

        Returns: A list of files that maintain consistent vertical spacing after comments.
        """
        return self.get_blank_lines_around_comments("below")

    def question_S10(self):
        """
        Uses AST to group import blocks and counts blank lines following them.

        Returns: A list of files that use a consistent number of blank lines after import blocks.
        """
        def count_blank_lines_after_every_import_block(file_path):
            
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
                blank_count = 0
                i = start_line_index + 1
                while i < len(all_lines):
                    if not all_lines[i].strip():
                        blank_count += 1
                        i += 1
                    else:
                        break
                return blank_count

            class ImportVisitor(ast.NodeVisitor):
                def __init__(self, lines):
                    self.lines = lines
                    self.blank_counts = []
                    self.last_import_end_line = -1 

                def visit_Import(self, node):
                    self.process_import_node(node)
                    self.generic_visit(node)

                def visit_ImportFrom(self, node):
                    self.process_import_node(node)
                    self.generic_visit(node)

                def process_import_node(self, node):
                    if not hasattr(node, 'end_lineno'):
                        return
                    
                    current_start_line = node.lineno - 1
                    current_end_line = node.end_lineno - 1
                    
                    if self.last_import_end_line != -1 and current_start_line > (self.last_import_end_line + 1):
                        count = count_blanks_from(self.last_import_end_line, self.lines)
                        self.blank_counts.append(count)

                    self.last_import_end_line = current_end_line
                
                def finalize(self):
                    if self.last_import_end_line != -1:
                        count = count_blanks_from(self.last_import_end_line, self.lines)
                        self.blank_counts.append(count)

            visitor = ImportVisitor(lines)
            visitor.visit(tree)
            visitor.finalize()
            
            return visitor.blank_counts

        return self._find_consistent_files(count_blank_lines_after_every_import_block, per_line=False)
    
    def question_S11(self):
        """
        Uses AST to locate class ends and counts blank lines immediately following them.

        Returns: A list of files that use a consistent number of blank lines after classes.
        """
        def count_blank_lines_after_class_ast(file_path):
            blank_counts = []
            
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

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef): 
                    
                    if not hasattr(node, 'end_lineno'):
                        print(f"[!] Attenzione: 'end_lineno' non disponibile per {file_path} "
                              "(serve Python 3.8+). Salto S11 per questo file.")
                        return []

                    class_end_line_index = node.end_lineno - 1
                    
                    blank_count = 0
                    i = class_end_line_index + 1
                    
                    while i < len(lines):
                        if not lines[i].strip():
                            blank_count += 1
                            i += 1
                        else:
                            break
                    
                    blank_counts.append(blank_count)

            return blank_counts
        
        return self._find_consistent_files(count_blank_lines_after_class_ast, per_line=False)
    
    def question_S12(self):
        """
        Identifies constant assignment blocks via AST and analyzes the blank lines following such blocks.

        Returns: A list of files with consistent vertical separation after constant blocks.
        """
        def _is_constant_name(name_str: str) -> bool:
            if not name_str or not isinstance(name_str, str):
                return False
            if not any(c.isalpha() for c in name_str):
                return False
            
            for char in name_str:
                if char.isalpha() and not char.isupper():
                    return False
            return True

        def count_blank_lines_after_constants_ast(file_path):
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
                blank_count = 0
                i = start_line_index + 1
                while i < len(all_lines):
                    if not all_lines[i].strip():
                        blank_count += 1
                        i += 1
                    else:
                        break
                return blank_count

            class ConstantVisitor(ast.NodeVisitor):
                def __init__(self, lines):
                    self.lines = lines
                    self.blank_counts = []
                    self.last_constant_end_line = -1 

                def visit_Assign(self, node):
                    self.process_constant_node(node)
                    self.generic_visit(node)

                def visit_AnnAssign(self, node):
                    self.process_constant_node(node)
                    self.generic_visit(node)

                def process_constant_node(self, node):
                    
                    is_const = False
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and _is_constant_name(target.id):
                                is_const = True
                                break
                    elif isinstance(node, ast.AnnAssign):
                        if isinstance(node.target, ast.Name) and _is_constant_name(node.target.id):
                            is_const = True

                    if not is_const:
                        return 

                    if not hasattr(node, 'end_lineno'):
                        return 
                    
                    current_start_line = node.lineno - 1
                    current_end_line = node.end_lineno - 1
                    
                    if self.last_constant_end_line != -1 and current_start_line > (self.last_constant_end_line + 1):
                        count = count_blanks_from(self.last_constant_end_line, self.lines)
                        self.blank_counts.append(count)

                    self.last_constant_end_line = current_end_line
                
                def finalize(self):
                    if self.last_constant_end_line != -1:
                        count = count_blanks_from(self.last_constant_end_line, self.lines)
                        self.blank_counts.append(count)

            visitor = ConstantVisitor(lines)
            visitor.visit(tree)
            visitor.finalize()
            
            return visitor.blank_counts

        return self._find_consistent_files(count_blank_lines_after_constants_ast, per_line=False)
    
    def question_S13(self):
        """
        Analyzes function calls to determine the argument wrapping strategy.

        Returns: A list of tuples containing (file_path, strategy_description, example_code_snippet).
        """
        def analyze_function_calls_in_file(file_path):
            found_calls = []
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines_content = content.splitlines()
                
                if not content.strip(): return []

                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        args = node.args + node.keywords
                        
                        if len(args) < 2: continue
                            
                        if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
                            continue

                        start_line = node.lineno - 1
                        end_line = node.end_lineno - 1
                        
                        if start_line == end_line:
                            snippet = lines_content[start_line].strip()
                        else:
                            snippet_lines = lines_content[start_line : end_line + 1]
                            snippet = "\n".join(snippet_lines).strip()

                        arg_lines = []
                        for arg in node.args:
                            arg_lines.append(arg.lineno)
                        for kw in node.keywords:
                            if hasattr(kw, 'lineno'): arg_lines.append(kw.lineno)
                            elif hasattr(kw, 'value'): arg_lines.append(kw.value.lineno)
                        
                        if not arg_lines: continue

                        unique_lines = set(arg_lines)
                        
                        strategy = "mixed"
                        if len(unique_lines) == 1:
                            strategy = "same_line"
                        elif len(unique_lines) == len(args):
                            strategy = "newline_every_arg"
                        
                        found_calls.append((strategy, snippet))
                            
            except Exception:
                return []
                
            return found_calls

        results = []
        max_lines = 1000
        
        for file_path in self.python_files:
            if len(results) >= self.max_results_per_question:
                break

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if len(f.readlines()) > max_lines: continue
            except: continue

            calls_data = analyze_function_calls_in_file(str(file_path))
            
            if calls_data:
                chosen_strategy, snippet = random.choice(calls_data)
                
                relative_path = str(file_path.relative_to(self.codebase_path))
                
                if chosen_strategy == "mixed": chosen_strategy = "Strategia mista (alcuni a capo, altri no)"
                elif chosen_strategy == "same_line": chosen_strategy = "Tutti gli argomenti sono sulla stessa riga"
                elif chosen_strategy == "newline_every_arg": chosen_strategy = "Ogni argomento è su una nuova riga"
                
                results.append((relative_path, chosen_strategy, snippet))

        return results