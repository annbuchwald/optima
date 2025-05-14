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
#detect a programming language of a given files
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

def getAnalyzedCode(file=None, directory=None, max_complexity=None, regex=None, extensions= None, include_lines= None) -> str:
    language = detect_language(file)
    getSummary = f"Here is a function written in {language}\n.Please analyze and suggest possible improvements in:\n"

    if file:
        result = analyze_file(file, max_complexity, regex).problematic_functions
    else:
        result = analyze_directory(
            directory, max_complexity, regex, extensions
        ).problematic_functions
    if include_lines:
        for r in result:
            #print(f"{r.filepath} {r.func_name} {r.complexity} {r.line_begin} {r.line_end}")
            getSummary += f"{r.filepath} {r.func_name} {r.complexity} {r.line_begin} {r.line_end}"

    else:
        for r in result:
            #print(f"{r.filepath} {r.func_name} {r.complexity}")
            getSummary += f"{r.filepath} {r.func_name} {r.complexity}"
    getSummary += extract_function_code(file, include_lines[0], include_lines[1])
    return getSummary



# def main():
#     parser = argparse.ArgumentParser(
#         prog="Optima", description="Function complexity calculator with llm-based optimisation"
#     )
#     group = parser.add_mutually_exclusive_group(required=True)
#     group.add_argument("-f", "--file", type=str, help="File to analyze")
#     group.add_argument("-d", "--directory", type=str, help="Directory to analyze")
#     parser.add_argument("-m", "--max-complexity", type=int, default=10, help="Max function complexity")
#     parser.add_argument(
#         "-r", "--regex", nargs="+", type=str, default=[r".*"], help="List of regex patterns for functions to analyze"
#     )
#     parser.add_argument("-e", "--extensions", nargs="+", type=str, default=[], help="File extensions to analyze")
#     parser.add_argument(
#         "-i", "--include-lines", action="store_true", help="Include lines in which function begins/ends"
#     )
#     args = parser.parse_args()
#
#     if args.file:
#         result = analyze_file(args.file, args.max_complexity, args.regex).problematic_functions
#     else:
#         result = analyze_directory(
#             args.directory, args.max_complexity, args.regex, args.extensions
#         ).problematic_functions
#
#     if args.include_lines:
#         for r in result:
#             print(f"{r.filepath} {r.func_name} {r.complexity} {r.line_begin} {r.line_end}")
#     else:
#         for r in result:
#             print(f"{r.filepath} {r.func_name} {r.complexity}")
#
#
# if __name__ == "__main__":
#     main()
