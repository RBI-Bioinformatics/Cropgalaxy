#!/usr/bin/env python3
"""
Convert LGC genotype data to Flapjack genotype format

Usage:
    python LGC-Flapjack_converter.py input.csv output.txt
"""

import sys

# Check arguments
if len(sys.argv) != 3:
    print("Usage: python LGC-Flapjack_converter.py <input_file> <output_file>")
    sys.exit(1)

intertek_file = sys.argv[1]
flapjack_file = sys.argv[2]

LGC_id = 'DNA \\ Assay'
fj_header = '# fjFile = GENOTYPE'
missing_string = 'NN'


def replacer(line):
    """Clean and convert a single line into Flapjack format"""
    s = line.replace(LGC_id, '')

    search_list = ['?', 'DUPE', 'Bad', 'NTC', 'Unused', 'empty', 'Uncallable', 'NA']
    for item in search_list:
        s = s.replace(item, missing_string)

    s = s.replace('Missing', '-')
    s = s.replace(',', '\t')
    s = s.replace(':', '')

    return s


def main():
    with open(intertek_file, 'r', encoding='utf-8') as infile, \
         open(flapjack_file, 'w', encoding='utf-8') as outfile:

        outfile.write(fj_header + "\n")

        always_print = False

        for line in infile:
            # Start printing once header line is found
            if always_print or LGC_id in line:
                always_print = True
                outfile.write(replacer(line))


if __name__ == "__main__":
    main()
