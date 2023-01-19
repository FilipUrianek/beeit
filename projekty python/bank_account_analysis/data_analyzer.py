import pandas as pd
from pandas.api.types import is_numeric_dtype
from copy import deepcopy
import os
try:
    import openpyxl
except:
    print("Installing missing dependency openpyxl")
    os.system('pip install openpyxl')
from pathlib import Path
import numpy as np
import argparse
import matplotlib.pyplot as plt


def parse_args():
    parser = argparse.ArgumentParser(
        prog="My data analysis app", description="Accepts xlsx/csv table, draws figures and computes statistics")
    parser.add_argument("--src", required=True, type=Path, default=None)
    parser.add_argument("--dest", required=False,
                        type=Path, default=Path('./output'))

    parser.add_argument("--save_as", required=False, type=str,
                        default="csv", choices=["csv", "xlsx"])
    parser.add_argument("--no_summary", action=argparse.BooleanOptionalAction)
    parser.add_argument("--no_figs", action=argparse.BooleanOptionalAction)
    parser.add_argument("--show_figs", action=argparse.BooleanOptionalAction)
    parser.add_argument("--is_index_dt", action=argparse.BooleanOptionalAction)
    parser.add_argument(
        "--save_modified", action=argparse.BooleanOptionalAction)
    parser.add_argument("--shorten", required=False,
                        type=str, default=[], nargs='+')
    parser.add_argument("--index", required=True,
                        type=str, default=None)
    parser.add_argument("--stats", type=str, nargs="+",
                        default=["mean", "med", "min", "max"])
    parser.add_argument("--rename", type=str, nargs="+",
                        default=[])
    parser.add_argument("--cols_to_plot", type=str, nargs="+",
                        default=["all"])
    parser.add_argument("--plot_cols_by", type=str, nargs="+",
                        default=["index"])
    parser.add_argument("--colors", type=str, nargs="+",
                        default=["red"])
    parser.add_argument("--plot_in_one", action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    if len(args.cols_to_plot) != 1 and len(args.plot_cols_by) != 1 and len(args.cols_to_plot) != len(args.plot_cols_by):
        parser.error(
            "Error: supplied number of target columns doesn't match the number of x-axes to plot by")
    elif len(args.cols_to_plot) != 1 and len(args.colors) != 1 and len(args.cols_to_plot) != len(args.colors):
        parser.error(
            "Error: supplied number of target columns doesn't match the number requested plot colors")
    elif len(args.rename) % 2 != 0:
        parser.error(
            "Error: supplied incorrect number of values for renamed columns")
    elif len(args.shorten) > 2:
        parser.error(
            "Error: requested to shorten but incorrectly supplied new start and end")
    return args


def read_table(src_path):
    if ".csv" in str(src_path):
        src_table = pd.read_csv(src_path)
    elif ".xlsx" in str(src_path) or ".xls" in str(src_path):
        src_table = pd.read_excel(src_path)
    else:
        raise FileNotFoundError("Invaid source file")
    return src_table


def get_numerical_cols(args, df):
    if args.cols_to_plot == ["all"]:
        cols = df.columns
        cols_to_process = []
        for col in cols:
            if is_numeric_dtype(df[col]) or np.issubdtype(df[col].dtype, np.number):
                cols_to_process.append(col)
    else:
        cols_to_process = args.cols_to_plot
    return cols_to_process


def create_numerical_summary(df, cols_to_process):
    df_to_process = df[cols_to_process]
    return df_to_process.describe()


def compute_stats(stats, df, cols_to_process):
    stat_fns = {
        "mean": np.mean,
        "med": np.median,
        "min": np.min,
        "max": np.max
    }
    all_stats = {}
    for stat in stats:
        stat_dict = {}
        for col in cols_to_process:
            stat_dict.setdefault(col, stat_fns[stat](df[col]))
        all_stats.setdefault(stat, deepcopy(stat_dict))
    return all_stats


def plot_stats(cols, stats):
    colors = ["red", "blue", "orange", "purple", "green"]
    colors = colors[:len(stats)]
    fig, axs = plt.subplots(ncols=len(cols), nrows=1,
                            figsize=(len(cols)*3, 4))
    i = 0
    for col in cols:
        col_stats, col_values = [], []
        for stat in stats.keys():
            col_stats.append(stat.upper())
            col_values.append(stats[stat][col])
        axs[i].bar(col_stats, col_values, color=colors, width=0.5)
        axs[i].set_title(col.upper(), pad=15)
        i += 1

    plt.subplots_adjust(wspace=1.0)
    plt.subplots_adjust(hspace=0.6)
    return fig


def plot_cols(df, cols, plot_by, colors, as_one):
    if len(plot_by) == 1:
        plot_by = plot_by*len(cols)
    if len(colors) == 1:
        colors = colors*len(cols)
    col_figs = []
    if as_one:
        main_fig, axs = plt.subplots(
            nrows=1, ncols=len(cols), figsize=(10*len(cols), 7))
    for i in range(len(cols)):
        params = {
            "use_index": (plot_by[i] == "index"),
            "x": plot_by[i] if plot_by[i] != "index" else None
        }
        if as_one:
            axs[i] = df.plot(y=cols[i], **params, kind="line", title=cols[i].upper(
            ), xlabel=df.index.name.upper(), ax=axs[i], color=colors[i], grid=True)
        else:
            fig, ax = plt.subplots(nrows=1, ncols=1)
            ax = df.plot(y=cols[i], **params, kind="line", figsize=(
                8, 5), title=cols[i].upper(), xlabel=df.index.name.upper(), ax=ax, color=colors[i], grid=True)
            col_figs.append((cols[i], fig))
    plt.subplots_adjust(wspace=0.5)
    return [("all", main_fig)] if as_one else col_figs


def main():
    args = parse_args()
    src_path = args.src.resolve()
    out_name = str(src_path).split('/')[-1].split('.')[0]
    output_path = Path('./output', out_name).resolve()

    if not output_path.is_dir():
        os.makedirs(output_path)

    src_table = read_table(src_path=src_path)
    new_index = pd.DatetimeIndex(
        src_table[args.index]) if args.is_index_dt else src_table[args.index]
    src_table.set_index(new_index, inplace=True, drop=True)

    if args.shorten:
        if args.is_index_dt:
            new_end = pd.Timestamp(args.shorten[0])
            if len(args.shorten) < 2:
                new_start = src_table.index[-1]
            else:
                new_start = pd.Timestamp(args.shorten[1])
        else:
            new_start = args.shorten[0]
            if len(args.shorten) < 2:
                new_end = src_table.index[-1]
            else:
                new_end = args.shorten[1]

        src_table = src_table[(src_table.index >= new_start) & (
            src_table.index <= new_end)]

    if args.rename != []:
        src_table.rename(
            {key: value for key, value in [(args.rename[i], args.rename[i+1]) for i in range(0, len(args.rename)-1)]}, axis='columns', inplace=True)

    if args.save_modified:
        if args.save_as == "csv":
            src_table.to_csv(Path(output_path,  out_name + "_modified.csv"))
        elif args.save_as == "xlsx":
            df_mod = src_table.copy()
            if args.is_index_dt:
                df_mod.set_index(df_mod.index.strftime(
                    '%m/%d/%Y'), inplace=True)
            df_mod.to_excel(Path(output_path,  out_name + "_modified.xlsx"))

    cols_to_process = get_numerical_cols(args, src_table)
    if not args.no_summary:
        summary = create_numerical_summary(src_table, cols_to_process)
        if args.save_as == "csv":
            summary.to_csv(Path(output_path, out_name + ".csv"))
        elif args.save_as == "xlsx":
            summary.to_excel(Path(output_path, out_name + ".xlsx"))

    if not args.no_figs:
        stats = compute_stats(args.stats, src_table, cols_to_process)
        stat_plot = plot_stats(cols_to_process, stats)
        stat_plot.savefig(Path(output_path, f"{out_name}_cumulative_stats.png"),
                          bbox_inches='tight', pad_inches=0.3)
        col_plots = plot_cols(
            src_table, cols_to_process, args.plot_cols_by, args.colors, args.plot_in_one)

        for col_label, col_plot in col_plots:
            col_plot.savefig(Path(output_path, f"{col_label}_over_index.png"))
        if args.show_figs:
            plt.show()


if __name__ == "__main__":
    main()
