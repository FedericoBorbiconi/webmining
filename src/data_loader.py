import pandas as pd


def load_nodes(path="data/g_nodos.txt"):
    """
    Carga el archivo de nodos turísticos.

    Args:
        path: ruta al archivo de nodos delimitado por '|'.

    Returns:
        DataFrame con columnas nombre, tipo, puntaje, lat, lon, indexado por ID.
    """
    df = pd.read_csv(path, sep="\t", skipinitialspace=True)
    df.columns = df.columns.str.strip()
    df["nombre"] = df["nombre"].str.strip()
    df["tipo"] = df["tipo"].str.strip()
    df["ID"] = df["ID"].astype(int)
    df["puntaje"] = df["puntaje"].astype(int)
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
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
