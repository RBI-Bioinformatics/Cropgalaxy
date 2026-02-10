#!/usr/bin/env python3
# encoding: utf-8

"""
SimpleTracker -- Generate sample ID, barcodes, and plate layout
Updated for Python 3.10+ and pandas 2.x (2026)
"""

import csv
import zipfile
import sys
import os
import pandas as pd
import uuid
import xlrd
import traceback
from xlutils.copy import copy
import argparse
from zipfile import ZIP_DEFLATED

__version__ = "1.0.0"
__updated__ = "2026-02-10"

plate_well_positions_vertical = [
    f"{row}{col:02d}"
    for col in range(1, 13)
    for row in "ABCDEFGH"
]

plate_well_positions_horizontal = [
    f"{row}{col:02d}"
    for row in "ABCDEFGH"
    for col in range(1, 13)
]

infinium_plate_well_format = plate_well_positions_horizontal.copy()

sentrix_wells = [
    f"R{r:02d}C{c:02d}"
    for r in range(1, 13)
    for c in (1, 2)
]

miseq_control_ids = ['NB1','NB1b','NB2','NB2b','NB3','NB3b','NB4','NB4b']
miseq_control_names = [
    'Nipponbare1','Nipponbare1b',
    'Nipponbare2','Nipponbare2b',
    'Nipponbare3','Nipponbare3b',
    'Nipponbare4','Nipponbare4b'
]


# -----------------------------
# Utility Functions
# -----------------------------

def custom_insert(df, header, column):
    if header in df.columns:
        df = df.drop(columns=header)
    df.insert(0, header, column)
    return df


def generate_plate_layout(df, exp_id, well_positions):
    plate_names = []
    plate_barcodes = []
    plate_uuids = []
    plate_readable = []

    samples_per_plate = len(well_positions)

    for i in range(len(df)):
        plate_index = i % samples_per_plate
        if plate_index == 0:
            plate_uuid = uuid.uuid4()

        plate_names.append(f"{exp_id}{(i // samples_per_plate)+1:02d}")
        plate_barcodes.append(str(plate_uuid.int))
        plate_uuids.append(plate_uuid)
        plate_readable.append(well_positions[plate_index])

    df = custom_insert(df, "plate_well_position", plate_readable)
    df = custom_insert(df, "plate_name", plate_names)
    df["plate_barcode"] = plate_barcodes
    df = custom_insert(df, "plate_uuid", plate_uuids)

    return df


def generate_verify_database(df):
    combined = []
    next_steps = []
    last_plate = None

    for i, row in df.iterrows():
        if row["plate_barcode"] != last_plate:
            combined.append(row["plate_barcode"])
            next_steps.append("Scan NEW PLATE")
            last_plate = row["plate_barcode"]

        combined.append(row["sample_barcode"])
        next_steps.append("Scan next plant")

    next_steps = next_steps[1:] + ["END"]

    return pd.DataFrame({
        "barcodes": combined,
        "next_step": next_steps
    })


# -----------------------------
# Generate Samples Mode
# -----------------------------

def generate_samples(
    infile,
    outfile,
    separator,
    exp_id,
    direction,
    check_positions,
    intertek_template_file
):

    df = pd.read_csv(infile, sep=separator)
    new_rows = []

    for _, row in df.iterrows():
        for plant in range(1, row["number_of_plants"] + 1):
            new_row = row.copy()
            new_row["sample_name"] = f"{row['germplasm_name']}-{plant}"
            new_row["uuid"] = uuid.uuid4()
            new_row["sample_barcode"] = str(new_row["uuid"].int)
            new_rows.append(new_row)

    new_df = pd.DataFrame(new_rows).reset_index(drop=True)

    plate_positions = (
        plate_well_positions_horizontal
        if direction == "horizontal"
        else plate_well_positions_vertical
    )

    check_positions = check_positions.split(",")
    well_positions = [x for x in plate_positions if x not in check_positions]

    new_df = generate_plate_layout(new_df, exp_id, well_positions)
    new_df.insert(0, "sequence", range(1, len(new_df) + 1))

    extension = ".csv" if separator == "," else ".txt"

    plate_df = new_df[["plate_uuid","plate_barcode","plate_name"]].drop_duplicates("plate_barcode")

    plate_df.to_csv(outfile + ".plate_barcodes" + extension, sep=separator, index=False)
    new_df.drop(columns=["plate_uuid","plate_barcode"]).to_csv(
        outfile + ".sample_file" + extension,
        sep=separator,
        index=False
    )

    verify_df = generate_verify_database(new_df)
    verify_df.to_csv(outfile + ".verify_db.txt", sep="\t", index=False)


# -----------------------------
# Main
# -----------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Generate sample IDs and plate layouts"
    )

    parser.add_argument("-m", "--mode", default="generate")
    parser.add_argument("-i", "--in", dest="infile", default="files/in.txt")
    parser.add_argument("-o", "--out", dest="outfile", default="files/out")
    parser.add_argument("-e", "--exp-name", dest="exp_name", default="new_exp-")
    parser.add_argument("-d", "--direction", default="horizontal")
    parser.add_argument("-t", "--intertek-template", dest="intertek_template_file")
    parser.add_argument("-c", "--check-position", dest="check_positions", default="H11,H12")

    args = parser.parse_args()

    separator = "," if args.infile.endswith(".csv") else "\t"

    if args.mode == "generate":
        generate_samples(
            infile=args.infile,
            outfile=args.outfile,
            separator=separator,
            exp_id=args.exp_name,
            direction=args.direction,
            check_positions=args.check_positions,
            intertek_template_file=args.intertek_template_file
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
