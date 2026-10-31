import argparse
import logging
import sys
import radon.complexity as cc
import radon.raw as raw

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="Calculates code complexity metrics for Python code."
    )
    parser.add_argument(
        "filepath", help="Path to the Python file to analyze."
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=10,
        help="Complexity threshold for reporting functions/classes. Defaults to 10.",
    )
    parser.add_argument(
        "--report-raw",
        action="store_true",
        help="Also report raw code metrics (lines of code, comments, etc.)"
    )
    return parser.parse_args()


def calculate_cyclomatic_complexity(filepath):
    """
    Calculates the cyclomatic complexity of functions and classes in a Python file.

    The original file text is always passed to radon as read, so the
    line numbers radon reports are true source line numbers.

    Args:
        filepath (str): Path to the Python file.

    Returns:
        list: A list of tuples containing the function/class name, complexity score,
              line number, and end line number. Returns None when the
              file could not be read or parsed, so the caller can tell
              an error apart from a file that simply defines nothing
              radon reports, which legitimately returns an empty list.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        results = cc.cc_visit(code)
        return [(res.name, res.complexity, res.lineno, res.endline) for res in results]

    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None
    except SyntaxError as e:
        logging.error(f"Syntax error in {filepath}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None


def calculate_raw_metrics(filepath):
    """
    Calculates raw code metrics like lines of code, comments, blank lines, etc.

    Args:
        filepath (str): Path to the Python file.

    Returns:
        dict: A dictionary containing raw metrics. Returns None on
        error, for the same reason as the complexity function above.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        metrics = raw.analyze(code)
        return {
            "sloc": metrics.sloc,
            "lloc": metrics.lloc,
            "comments": metrics.comments,
            "multi": metrics.multi,
            "blank": metrics.blank,
            "single_comments": metrics.single_comments
        }
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

def main():
    """
    Main function to execute the code complexity analysis.
    """
    args = setup_argparse()

    # Input validation for threshold
    if args.threshold <= 0:
        logging.error("Complexity threshold must be a positive integer.")
        sys.exit(1)

    complexity_results = calculate_cyclomatic_complexity(args.filepath)

    if complexity_results is None:
        sys.exit(1)

    # The threshold is a real filter: only blocks above it are listed.
    exceeding = [result for result in complexity_results if result[1] > args.threshold]
    if exceeding:
        print(f"Code Complexity Analysis for {args.filepath}:\n")
        for name, complexity, lineno, endline in exceeding:
            print(f"  - {name} (lines {lineno}-{endline}): Complexity = {complexity}")
            print(f"    Warning: Complexity exceeds threshold ({args.threshold})!")
        print("\n")
    else:
        print(f"No functions or classes exceed the complexity threshold ({args.threshold}).")

    if args.report_raw:
        raw_metrics = calculate_raw_metrics(args.filepath)
        if raw_metrics is None:
            sys.exit(1)
        if raw_metrics:
            print("Raw Code Metrics:\n")
            for metric, value in raw_metrics.items():
                print(f"  - {metric}: {value}")
            print("\n")

if __name__ == "__main__":
    # Example usage (from command line):
    # python main.py my_python_file.py --threshold 15 --report-raw
    # python main.py my_python_file.py
    main()