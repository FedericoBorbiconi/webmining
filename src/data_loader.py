import os
import pandas as pd


def _parse_time(s: str) -> int:
    """Convierte "HH:MM" a minutos desde medianoche."""
    h, m = s.strip().split(":")
    return int(h) * 60 + int(m)


def load_nodes(path="data/g_nodos.txt"):
    """
    Carga el archivo de nodos turísticos.

    Args:
        path: ruta al archivo de nodos delimitado por '|'.

    Returns:
        DataFrame con columnas nombre, tipo, puntaje, lat, lon, apertura_min,
        cierre_min, indexado por ID.
    """
    df = pd.read_csv(path, sep="\t", skipinitialspace=True)
    df.columns = df.columns.str.strip()
    df["nombre"] = df["nombre"].str.strip()
    df["tipo"] = df["tipo"].str.strip()
    df["ID"] = df["ID"].astype(int)
    df["puntaje"] = df["puntaje"].astype(float)
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    df["apertura_min"] = df["Apertura"].apply(_parse_time)
    df["cierre_min"] = df["Cierre"].apply(_parse_time)
    # Cierres pasada la medianoche (ej: "01:30" con apertura "17:30")
    mask = df["cierre_min"] < df["apertura_min"]
    df.loc[mask, "cierre_min"] += 1440
    df.set_index("ID", inplace=True)
    return df


def load_matrix(path):
    """
    Carga una matriz de costos (distancia o tiempo) desde un CSV.

    Args:
        path: ruta al archivo CSV con IDs como índice y columnas.

    Returns:
        DataFrame cuadrado con índice y columnas enteros (IDs de nodos).
    """
    df = pd.read_csv(path, index_col=0)
    df.index = df.index.astype(int)
    df.columns = df.columns.astype(int)
    return df


def list_depots(data_dir="data"):
    """
    Descubre los depots disponibles buscando subcarpetas de data_dir que
    contengan g_nodos.txt. El nombre del depot se obtiene del nodo con ID=0.

    Args:
        data_dir: directorio raíz de datos.

    Returns:
        Lista de tuplas (subfolder_path, depot_name) ordenada por nombre de carpeta.
    """
    depots = []
    try:
        entries = sorted(os.scandir(data_dir), key=lambda e: e.name)
    except FileNotFoundError:
        return depots

    for entry in entries:
        if not entry.is_dir():
            continue
        nodes_path = os.path.join(entry.path, "g_nodos.txt")
        if not os.path.exists(nodes_path):
            continue
        df = pd.read_csv(nodes_path, sep="\t", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        df["ID"] = df["ID"].astype(int)
        row = df[df["ID"] == 0]
        depot_name = row["nombre"].values[0].strip() if not row.empty else entry.name
        depots.append((entry.path, depot_name))

    return depots


def get_nodes_by_type(nodes_df):
    """
    Agrupa los IDs de nodos por tipo, excluyendo el depot.

    Args:
        nodes_df: DataFrame de nodos (salida de load_nodes).

    Returns:
        Diccionario {tipo: [lista de IDs]} sin incluir el tipo 'depot'.
    """
    groups = {}
    for tipo, group in nodes_df.groupby("tipo"):
        if tipo != "depot":
            groups[tipo] = list(group.index)
    return groups
