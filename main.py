# import argparse
# import os
# import pathlib
# import re
# from dataclasses import dataclass
#
# import lizard
# from dotenv import load_dotenv
# from openai import AzureOpenAI
#
# load_dotenv()
#
# @dataclass
# class FunctionComplexity:
#     func_name: str
#     filepath: str
#     complexity: int
#     line_begin: int
#     line_end: int
#
#
# @dataclass
# class AnalyseComplexityResult:
#     max_complexity: int
#     problematic_functions: list[FunctionComplexity]
#
#
# def function_name_matches_any_regex(func_name: str, regex_list: list[re.Pattern]) -> bool:
#     for regex in regex_list:
#         if re.match(regex, func_name):
#             return True
#     return False
#
#
# def analyze_file(filepath: str, max_complexity: int, regex_patterns: list[str]) -> AnalyseComplexityResult:d
#     lizard_result = lizard.analyze_file(filepath)
#     analyze_result = AnalyseComplexityResult(max_complexity, [])
#
#     function_regexes = []
#     for regex in regex_patterns:
#         function_regexes.append(re.compile(regex))
#
#     for function in lizard_result.function_list:
#         if function.cyclomatic_complexity > max_complexity and function_name_matches_any_regex(
#             function.name, function_regexes
#         ):
#             func_comp = FunctionComplexity(
#                 function.name, filepath, function.cyclomatic_complexity, function.start_line, function.end_line
#             )
#             analyze_result.problematic_functions.append(func_comp)
#
#     return analyze_result
#
#
# def analyze_directory(
#     directory: str, max_complexity: int, regex_patterns: list[str], extensions: list[str]
# ) -> AnalyseComplexityResult:
#     analyze_result = AnalyseComplexityResult(max_complexity, [])
#
#     for subdir, dirs, files in os.walk(directory):
#         for file in files:
#             filepath = subdir + os.sep + file
#             if len(extensions) == 0 or pathlib.Path(filepath).suffix in extensions:
#                 analyze_result.problematic_functions.extend(
#                     analyze_file(filepath, max_complexity, regex_patterns).problematic_functions
#                 )
#
#     return analyze_result
#
# def main():
#     return print("Hello World")
#
#
# if __name__ == "__main__":
#     main()
