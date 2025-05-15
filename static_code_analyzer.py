import argparse
import os
import pathlib
import re
from dataclasses import dataclass

import lizard

@dataclass
class FunctionComplexity:
    func_name: str
    filepath: str
    complexity: int
    line_begin: int
    line_end: int


@dataclass
class AnalyseComplexityResult:
    max_complexity: int
    problematic_functions: list[FunctionComplexity]


def function_name_matches_any_regex(func_name: str, regex_list: list[re.Pattern]) -> bool:
    for regex in regex_list:
        if re.match(regex, func_name):
            return True
    return False


def analyze_file(filepath: str, max_complexity: int, regex_patterns: list[str]) -> AnalyseComplexityResult:
    lizard_result = lizard.analyze_file(filepath)
    analyze_result = AnalyseComplexityResult(max_complexity, [])

    function_regexes = []
    for regex in regex_patterns:
        function_regexes.append(re.compile(regex))

    for function in lizard_result.function_list:
        if function.cyclomatic_complexity > max_complexity and function_name_matches_any_regex(
                function.name, function_regexes
        ):
            func_comp = FunctionComplexity(
                function.name, filepath, function.cyclomatic_complexity, function.start_line, function.end_line
            )
            analyze_result.problematic_functions.append(func_comp)

    return analyze_result


def analyze_directory(
        directory: str, max_complexity: int, regex_patterns: list[str], extensions: list[str]
) -> AnalyseComplexityResult:
    analyze_result = AnalyseComplexityResult(max_complexity, [])

    for subdir, dirs, files in os.walk(directory):
        for file in files:
            filepath = subdir + os.sep + file
            if len(extensions) == 0 or pathlib.Path(filepath).suffix in extensions:
                analyze_result.problematic_functions.extend(
                    analyze_file(filepath, max_complexity, regex_patterns).problematic_functions
                )

    return analyze_result
#detect a programming language of a given file
def detect_language(filepath: str) -> str:
    ext_to_language = {
    '.c': 'C/C++', '.cpp': 'C/C++', '.cc': 'C/C++', '.h': 'C/C++', '.hpp': 'C/C++','.java': 'Java', '.cs': 'C#', '.js': 'JavaScript', '.ts': 'TypeScript', '.vue': 'VueJS',
    '.m': 'Objective-C', '.swift': 'Swift', '.py': 'Python', '.rb': 'Ruby','.ttcn3': 'TTCN-3', '.php': 'PHP', '.scala': 'Scala', '.gd': 'GDScript',
    '.go': 'Golang', '.lua': 'Lua', '.rs': 'Rust', '.f90': 'Fortran', '.f95': 'Fortran','.kt': 'Kotlin', '.sol': 'Solidity', '.erl': 'Erlang', '.zig': 'Zig', '.pl': 'Perl'
    }
    ext = pathlib.Path(filepath).suffix
    return ext_to_language.get(ext)

#extract a given function of code from file
def extract_function_code(filepath: str, start_line: int, end_line: int) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return ''.join(lines[start_line - 1:end_line])


# def run_analysis(file_path: str = None, directory_path: str = None, max_complexity: int = 10, regex_patterns=None,extensions=None, include_lines: bool = True)-> str:
#
#     str = ""
#     if file_path:
#         result = analyze_file(file_path, max_complexity, regex_patterns).problematic_functions
#     else:
#         result = analyze_directory(
#             directory_path, max_complexity, regex_patterns, extensions
#         ).problematic_functions
#
#     for r in result:
#         if include_lines:
#             # print(f"{r.filepath} {r.func_name} {r.complexity} {r.line_begin} {r.line_end}")
#             str+=f"File: {r.filepath}, Function name: {r.func_name}, Complexity: {r.complexity}, Begins: {r.line_begin}, Ends: {r.line_end}\n"
#
#         else:
#             # print(f"{r.filepath} {r.func_name} {r.complexity}")
#             str+=f"File: {r.filepath}, Function name: {r.func_name}, Complexity: {r.complexity}\n"
#         str+=f"{extract_function_code(r.filepath,r.line_begin,r.line_end)}\n"
#
#     return str




