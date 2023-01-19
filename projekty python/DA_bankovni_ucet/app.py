#nahrání modulů ze standardní knihovny jazyka Python
import os
import argparse
from pathlib import Path
from copy import deepcopy
from typing import List, Dict

#pokud uživatel nenainstaloval potřebné moduly, tak je program doninstaluje
try:
    import numpy
    import pandas
    import matplotlib
    import openpyxl
except:
    print("Installing missing dependency openpyxl")
    os.system('pip install numpy')
    os.system('pip install pandas')
    os.system('pip install matplotlib')
    os.system('pip install openpyxl')

#nahrání modulů, které se musí instalovat
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
import matplotlib.pyplot as plt


def parse_args() -> List[str]:
    '''
    Funkce slouží pro získání argumentů z příkazové řádky pro potřebné parametry.
    
    Návratové hodnoty:
        args: List -> seznam argumentů zadaných z příkazové řádky
    '''
    
    #vytvoří nový objekt pro parsování argumentů příkazové řádky
    parser = argparse.ArgumentParser(
        prog="Aplikace pro analýzu bankovního účtu", 
        description="Aplikace přijímá tabulky ve formátu csv/xlsx, vypočítá statistiky nad bankovním účtem a vykreslí grafy s informacemi o finančním toku na účtu."
    )

    #registrace jednotlivých parametrů pro zápis argumentů do příkazové řádky
    #pro vyvolání nápovědy se do příkazové řádky zapíše příkaz: python app.py -h
    parser.add_argument("--src", required=True, type=Path, default=None,
                        help="cesta k souboru s daty o vývoji bankovního účtu")
    parser.add_argument("--dest", required=False, type=Path, default=Path('./output'),
                        help="cesta k adresáři, do kterého se mají uložit výsledné statistiky a grafy")
    parser.add_argument("--save_as", required=False, type=str, default="csv", choices=["csv", "xlsx"],
                        help="typ souboru, do kterého se mají uložit souhrnné statistiky [csv, xlsx]")
    parser.add_argument("--no_summary", action=argparse.BooleanOptionalAction,
                        help="nevytvářej souhrnné statistiky")
    parser.add_argument("--no_figs", action=argparse.BooleanOptionalAction,
                        help="nevytvářej grafy")
    parser.add_argument("--show_figs", action=argparse.BooleanOptionalAction,
                        help="neukazuj grafy na obrazovce po jejich vytvoření")
    parser.add_argument("--is_index_dt", action=argparse.BooleanOptionalAction,
                        help="zda je zvolená index tabulky datového typu datetime")
    parser.add_argument("--save_modified", action=argparse.BooleanOptionalAction,
                        help="ulož modifikovanou tabulku informací uložit do nového souboru")
    parser.add_argument("--shorten", required=False, type=str, default=[], nargs='+',
                        help="zkrať analýzu pouze do určitého zvoleného indexu (datumo-času)")
    parser.add_argument("--index", required=True, type=str, default=None,
                        help="sloupec, který má být použit jako index tabulky")
    parser.add_argument("--stats", type=str, nargs="+", default=["mean", "med", "min", "max"],
                        help="statistiky, které se mají spočítat nad zvolenými sloupci [mean, med, min, max]")
    parser.add_argument("--rename", type=str, nargs="+", default=[],
                        help="přejmenuj sloupce na specifikované názvy")
    parser.add_argument("--cols_to_plot", type=str, nargs="+", default=["all"],
                        help="výběr sloupců pro analýzu informací")
    parser.add_argument("--plot_cols_by", type=str, nargs="+", default=["index"],
                        help="sloupec, který bude použit pro grafy jako osa x místo indexu")
    parser.add_argument("--colors", type=str, nargs="+", default=["red"],
                        help="barvy datových sad grafů")
    parser.add_argument("--plot_in_one", action=argparse.BooleanOptionalAction,
                        help="zakresli dílčí grafy do jednoho společného grafu")

    #získá parsováním argumenty zadané do příkazové řádky do kolekce args
    args = parser.parse_args()

    #
    if len(args.cols_to_plot) != 1 and len(args.plot_cols_by) != 1 and len(args.cols_to_plot) != len(args.plot_cols_by):
        parser.error("Error: supplied number of target columns doesn't match the number of x-axes to plot by")
    elif len(args.cols_to_plot) != 1 and len(args.colors) != 1 and len(args.cols_to_plot) != len(args.colors):
        parser.error("Error: supplied number of target columns doesn't match the number requested plot colors")
    elif len(args.rename) % 2 != 0:
        parser.error("Error: supplied incorrect number of values for renamed columns")
    elif len(args.shorten) > 2:
        parser.error("Error: requested to shorten but incorrectly supplied new start and end")
    return args


def read_table(src_path: str) -> pd.DataFrame:
    '''
    Funkce přečte tabulková data ze zdrojového souboru a vrátí je v podobě datového rámce pro strojové zpracování.

    Vstupy:
        src_path: str -> cesta ke zdrojovému souboru ve formátu .csv nebo .xls/.xlsx

    Návratové hodnoty:
        src_table: pd.Dataframe -> datový rámec modulu pandas představující strojově zpracovatelnou tabulku
    '''
    if ".csv" in str(src_path):
        src_table = pd.read_csv(src_path)
    elif ".xlsx" in str(src_path) or ".xls" in str(src_path):
        src_table = pd.read_excel(src_path)
    else:
        raise FileNotFoundError("Invaid source file")
    return src_table


def get_numerical_cols(args: argparse.ArgumentParser, df: pd.DataFrame) -> List[str]:
    '''
    Funkce získává seznam sloupců, které se mají zpracovat. Pokud uživatel zadal všechny sloupce, tak si funkce vyparsuje ze zadaného datového rámce jen sloupce s numerickými hodnotami.

    Vstupy:
        args: argparse.ArgumentParser -> seznam argumentů získaných z příkazové řádky
        df: pd.DataFrame -> datový rámec s daty o bankovních transakcích

    Výstupy:
        cols_to_process: List[str] -> seznam názvů sloupců, které se mají analyzovat pro získání a vykreslení informací
    '''

    #pokud je zadáno zpracování všech sloupců, tak získej z rámce ty, které mají numerická data
    if args.cols_to_plot == ["all"]:
        cols = df.columns
        cols_to_process = []
        for col in cols:
            if is_numeric_dtype(df[col]) or np.issubdtype(df[col].dtype, np.number):
                cols_to_process.append(col)
    #v opačném případě získej ty pevně zadané uživatelem
    else:
        cols_to_process = args.cols_to_plot

    #navrať seznam sloupců, které se mají zpracovat programem
    return cols_to_process


def create_numerical_summary(df: pd.DataFrame, cols_to_process: List[str]) -> pd.DataFrame:
    '''
    Provede statistickou analýzu vybraných sloupců, které se mají zpracovat (centrální tendence, rozptyl, tvar distribuce dat).

    Vstupy:
        df: pd.DataFrame -> datový rámec s informace o bankovních transakcích
        cols_to_process: List[str] -> seznam nadpisů sloupců, které se mají statisticky zpracovat

    Návratové hodnoty:
        stat_info: pd.DataFrame -> statistické informace o datech v zadaném datovém rámci
    '''

    #získej z rámce ty sloupce, které si uživatel přeje zpracovat
    df_to_process = df[cols_to_process]

    #proveď statistickou analýzu dat
    stat_info = df_to_process.describe()
    return stat_info


def compute_stats(stats: List[str], df: pd.DataFrame, cols_to_process: List[str]) -> Dict[str, float]:
    '''
    Výpočítá statistické informace jako je střední hodnota, medián, nejmenší hodnota a nejvýšší hodnota ze zadaných sloupců numerických dat určených ke zpracování.

    Vstupy:
        stats: List[str] -> seznam statistik, které si uživatel zvolit k výpočtu nad sloupci
        df: pd.DataFrame -> datový rámec s tabulkovými daty o bankovních transakcích
        cols_to_process: List[str] -> seznam sloupců, pro které se mají spočítat zadané statistické funkce

    Návratové hodnoty:
        all_stats: Dict[str, float] -> slovník vypočítaných statistických informací ze zadaných sloupců
    '''

    #slovník numpy funkcí, které se mají zavolat při zadání klíče s žádanou statistickou informací o datech
    stat_fns = {"mean": np.mean, "med": np.median, "min": np.min, "max": np.max}

    #projeď všechny statistiky zadané uživatelem (slouží jako klíče do slovníku s numpy funkcemi)
    all_stats = {}
    for stat in stats:
        stat_dict = {}
        #spočítej statistiku pro daný sloupec určený ke zpracování
        for col in cols_to_process:
            stat_dict.setdefault(col, stat_fns[stat](df[col]))
        #zapiš výsledek pro danou statistiku do souhrného slovníku statistických informací
        all_stats.setdefault(stat, deepcopy(stat_dict))
    return all_stats


def plot_stats(cols, stats):
    '''
    Funkce vytvoří graf statistických informací (mean, medián, min, max) a navrátí ho pro následné uložení/vykreslení.

    Vstupy:
        cols: -> seznam sloupců, ze kterých byly počítány statistické informace
        stats: -> slovník vypočítaných statistických informací pro zadané sloupce

    Návratové hodnoty:
        fig: matplotlib.figure -> graf vypočítaných statistických informací
    '''

    #seznam předpřipravených barev, vyber jich tolik, kolik je statistik
    colors = ["red", "blue", "orange", "purple", "green"]
    colors = colors[:len(stats)]

    #vytvoř tolik podgrafů, kolik je zvolených sloupců pro zpracování informací
    fig, axs = plt.subplots(ncols=len(cols), nrows=1,figsize=(len(cols)*3, 4))
    
    #projdi každý zvolený sloupec z datového zdroje
    i = 0
    for col in cols:
        col_stats, col_values = [], []
        #projdi každou vypočítanou statistiku pro každý sloupec a připrav seznam hodnot k vykreslení na osy
        for stat in stats.keys():
            col_stats.append(stat.upper())
            col_values.append(stats[stat][col])
        #vykresli z připravených hodnot na osách histogram a nastav mu nadpis podle názvu zdrojového sloupce
        axs[i].bar(col_stats, col_values, color=colors, width=0.5)
        axs[i].set_title(col.upper(), pad=15)
        i += 1

    #přidej mezery mezi podgrafy
    plt.subplots_adjust(wspace=1.0)
    plt.subplots_adjust(hspace=0.6)
    return fig


def plot_cols(df: pd.DataFrame, cols: List[str], plot_by, colors, as_one):
    '''
    Funkce ...
    '''

    #vytvoř tolik os x (kategorií), kolik je analyzovaných sloupců
    if len(plot_by) == 1:
        plot_by = plot_by*len(cols)
    
    #použij tolik barev, kolik je analyzovaných sloupců
    if len(colors) == 1:
        colors = colors*len(cols)
    
    #pokud uživatel zadal v příkazové řádce jeden velký multigraf, tak pro něj připrav plátno
    col_figs = []
    if as_one:
        main_fig, axs = plt.subplots(
            nrows=1, ncols=len(cols), figsize=(10*len(cols), 7))
    
    #vytvoř podgrafy pro všechny sloupce
    for i in range(len(cols)):
        params = {
            "use_index": (plot_by[i] == "index"),
            "x": plot_by[i] if plot_by[i] != "index" else None
        }
        
        #pokud si uživatel přál jeden multigraf, tak ho vytvoř
        if as_one:
            axs[i] = df.plot(y=cols[i], **params, kind="line", title=cols[i].upper(
            ), xlabel=df.index.name.upper(), ax=axs[i], color=colors[i], grid=True)
        #pokud si uživatel přál více dílčích grafů, tak je vytvoř
        else:
            fig, ax = plt.subplots(nrows=1, ncols=1)
            ax = df.plot(y=cols[i], **params, kind="line", figsize=(
                8, 5), title=cols[i].upper(), xlabel=df.index.name.upper(), ax=ax, color=colors[i], grid=True)
            col_figs.append((cols[i], fig))
    
    #přidej místo mezi podgrafy pro přehlednost
    plt.subplots_adjust(wspace=0.5)

    #vrát grafy k vykreslení nebo jeden velký graf, pokud to uživatel specifikoval v příkazové řádce
    return [("all", main_fig)] if as_one else col_figs


def main():

    #získej argumenty zadané uživatelem z příkazové řádky
    args = parse_args()

    #přemění relativní cestu k souboru z argumentu na absolutní
    src_path = args.src.resolve()

    #připojí k cestě output adresář
    out_name = str(src_path).split('/')[-1].split('.')[0]
    output_path = Path('./output', out_name).resolve()

    #pokud output adresář neexistuje na zadané cestě, tak ho vytvoř
    if not output_path.is_dir():
        os.makedirs(output_path)

    #načti tabulku s daty o bankovním účtu ze zadané cesty
    src_table = read_table(src_path=src_path)

    #vytvoř datum-čas nebo zvolený index do tabulky (index je série, která určuje odkazování se na záznamy)
    new_index = pd.DatetimeIndex(src_table[args.index]) if args.is_index_dt else src_table[args.index]

    #nastav index v datovém rámci získaného ze vstupního souboru
    src_table.set_index(new_index, inplace=True, drop=True)

    #pokud uživatel vybral zkrácenou analýzu do určitého datumo-času/záznamu
    if args.shorten:
        #pokud je indexem datumo-čas, tak získej nový začátek a konec v záznamech pro analýzu ve formátu datumo-času
        if args.is_index_dt:
            new_end = pd.Timestamp(args.shorten[0])
            if len(args.shorten) < 2:
                new_start = src_table.index[-1]
            else:
                new_start = pd.Timestamp(args.shorten[1])
        #pokud není indexem datumo-čas, tak získej nový začátek a konec v záznamech ve formátu zvoleného indexu
        else:
            new_start = args.shorten[0]
            if len(args.shorten) < 2:
                new_end = src_table.index[-1]
            else:
                new_end = args.shorten[1]

        #získej původní nebo případně menší tabulku bankovních dat při zvolení zkrácení záznamů
        src_table = src_table[(src_table.index >= new_start) & (
            src_table.index <= new_end)]

    #pokud uživatel zadal v argumentech příkazové řádky nová jména pro vykreslení sloupců, tak je přejmenuj
    if args.rename != []:
        src_table.rename({key: value for key, value in [(args.rename[i], args.rename[i+1]) for i in range(0, len(args.rename)-1)]}, axis='columns', inplace=True)

    #pokud si uživatel přeje modifikované informace z tabulky uložit, tak ulož do zadaného formátu (csv, xslx)
    if args.save_modified:
        if args.save_as == "csv":
            src_table.to_csv(Path(output_path,  out_name + "_modified.csv"))
        elif args.save_as == "xlsx":
            df_mod = src_table.copy()
            if args.is_index_dt:
                df_mod.set_index(df_mod.index.strftime('%m/%d/%Y'), inplace=True)
            df_mod.to_excel(Path(output_path,  out_name + "_modified.xlsx"))

    #získej názvy sloupců s numerickými dat pro statistické zpracování dat o bankovních přesunech
    cols_to_process = get_numerical_cols(args, src_table)

    #pokud si uživatel přeje statistickou analýzu dat, tak ji ulož v tabulkové podobě do zvoleného formátu
    if not args.no_summary:
        summary = create_numerical_summary(src_table, cols_to_process)
        if args.save_as == "csv":
            summary.to_csv(Path(output_path, out_name + ".csv"))
        elif args.save_as == "xlsx":
            summary.to_excel(Path(output_path, out_name + ".xlsx"))

    #pokud si uživatel přeje vytvořit grafy
    if not args.no_figs:

        #získej statistické informace o datech, které si uživatel žádá (mean, med, min, max)
        stats = compute_stats(args.stats, src_table, cols_to_process)

        #vykresli grafy statistických informací ze sloupců určených ke zpracování (např. průměrnou hodnotu vkladu, medián výběru, aj.)
        stat_plot = plot_stats(cols_to_process, stats)

        #ulož vygenerované grafy se statistickými informacemi do zadané výstupní cesty z příkazové řádky
        stat_plot.savefig(Path(output_path, f"{out_name}_cumulative_stats.png"), bbox_inches='tight', pad_inches=0.3)

        #vykreslni grafy ze sloupců určených ke zpracování dat
        col_plots = plot_cols(src_table, cols_to_process, args.plot_cols_by, args.colors, args.plot_in_one)

        #ulož do souboru všechny dílčí grafy (nebo jeden velký multigraf)
        for col_label, col_plot in col_plots:
            col_plot.savefig(Path(output_path, f"{col_label}_over_index.png"))

        #pokud uživatel vybral, že se mají grafy vykreslit na obrazovku, tak je vykresli
        if args.show_figs:
            plt.show()


if __name__ == "__main__":
    main()