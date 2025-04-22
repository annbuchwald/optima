import argparse
import os
import pathlib
import re
from dataclasses import dataclass

import lizard
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

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

#connect to AzureOpenAI for code optimazation
def getResponseFromAzureAI(file_data):

    azure_endpoint = os.getenv("azure_endpoint")  
    azure_deployment = os.getenv("azure_deployment")  
    api_key = os.getenv("azure_openai_api_key")
    api_version = os.getenv("azure_api_version")

    client = AzureOpenAI( 
        api_key = api_key, 
        api_version = api_version,
        azure_endpoint = azure_endpoint 
    )

    language = detect_language(file_data.filepath)
    if not language:
        raise ValueError(f"Unsupported file extension: {file_data.filepath}")
    func_code = extract_function_code(file_data.filepath, file_data.line_begin, file_data.line_end)
    
    prompt = (
    
        f"Here is a function written in {language}. Please analyze and suggest possible improvements in:\n"
        f"- performance\n- readability\n- security\n- maintainability\n - complexity\n"
        f"Also explain the reasoning behind each recommendation.\n\n"
        f"Time Complexity of code: {file_data.complexity}\n\n"
        f"Function code:\n{func_code}"
        
    )

    response = client.chat.completions.create(
        model = azure_deployment,
        messages = [
           
            {"role": "system", "content": "You are a senior software engineer skilled in refactoring and optimizing code."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,  
        temperature=0.7,  
        top_p=0.95,  
        frequency_penalty=0,  
        presence_penalty=0,
    )
    return response.choices[0].message.content




def main():
    parser = argparse.ArgumentParser(
        prog="Optima", description="Function complexity calculator with llm-based optimisation"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", type=str, help="File to analyze")
    group.add_argument("-d", "--directory", type=str, help="Directory to analyze")
    parser.add_argument("-m", "--max-complexity", type=int, default=10, help="Max function complexity")
    parser.add_argument(
        "-r", "--regex", nargs="+", type=str, default=[r".*"], help="List of regex patterns for functions to analyze"
    )
    parser.add_argument("-e", "--extensions", nargs="+", type=str, default=[], help="File extensions to analyze")
    parser.add_argument(
        "-i", "--include-lines", action="store_true", help="Include lines in which function begins/ends"
    )
    args = parser.parse_args()

    if args.file:
        result = analyze_file(args.file, args.max_complexity, args.regex).problematic_functions
    else:
        result = analyze_directory(
            args.directory, args.max_complexity, args.regex, args.extensions
        ).problematic_functions

    if args.include_lines:
        for r in result:
            print(f"{r.filepath} {r.func_name} {r.complexity} {r.line_begin} {r.line_end}")
    else:
        for r in result:
            print(f"{r.filepath} {r.func_name} {r.complexity}")


if __name__ == "__main__":
    main()
