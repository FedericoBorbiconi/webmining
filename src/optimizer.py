from itertools import product

TYPES = ["cultura", "gastronomia", "naturaleza", "comercio"]


def evaluate_route(route, cost_matrix):
    """
    Calcula el costo total de un recorrido sumando los costos entre nodos consecutivos.

    Args:
        route: lista de IDs de nodos en orden de visita (ej: [0, 2, 6, 19, 15, 0]).
        cost_matrix: DataFrame con los costos entre pares de nodos.

    Returns:
        Costo total (float) del recorrido.
    """
    total = 0.0
    for i in range(len(route) - 1):
        total += cost_matrix.loc[route[i], route[i + 1]]
    return total


def optimize(nodes_df, nodes_by_type, cost_matrix, type_order, criterion, dist_matrix=None):
    """
    Encuentra el recorrido óptimo seleccionando un nodo de cada tipo mediante fuerza bruta.

    Evalúa todas las combinaciones posibles (una por tipo) y retorna la mejor
    según el criterio elegido. El recorrido parte y regresa al depot (nodo 0).

    Args:
        nodes_df: DataFrame de nodos con columnas nombre, tipo, puntaje.
        nodes_by_type: diccionario {tipo: [IDs]} con los nodos agrupados por tipo.
        cost_matrix: DataFrame de costos (distancia o tiempo) a minimizar.
        type_order: lista con el orden de tipos a visitar (ej: ["cultura", "gastronomia", ...]).
        criterion: "distancia", "tiempo" o "puntaje".
        dist_matrix: DataFrame de distancias, usado para desempatar cuando criterion="puntaje".

    Returns:
        Tupla (mejor_ruta, mejor_valor) donde mejor_ruta es una lista de IDs
        y mejor_valor es el costo mínimo o puntaje máximo según el criterio.
    """
    if criterion == "puntaje":
        return _optimize_score(nodes_df, nodes_by_type, type_order, dist_matrix if dist_matrix is not None else cost_matrix)

    node_lists = [nodes_by_type[t] for t in type_order]
    best_route = None
    best_cost = float("inf")

    for combo in product(*node_lists):
        route = [0] + list(combo) + [0]
        cost = evaluate_route(route, cost_matrix)
        if cost < best_cost:
            best_cost = cost
            best_route = route

    return best_route, best_cost


def _optimize_score(nodes_df, nodes_by_type, type_order, dist_matrix):
    """
    Optimiza el recorrido maximizando el puntaje total.

    Selecciona de cada tipo el nodo con mayor puntaje. En caso de empate,
    desempata eligiendo la combinación con menor distancia total.

    Args:
        nodes_df: DataFrame de nodos con columnas nombre, tipo, puntaje.
        nodes_by_type: diccionario {tipo: [IDs]}.
        type_order: lista con el orden de tipos a visitar.
        dist_matrix: DataFrame de distancias para desempate.

    Returns:
        Tupla (mejor_ruta, puntaje_total).
    """
    # Para cada tipo, encontrar el puntaje máximo
    best_by_type = {}
    for t in type_order:
        candidates = nodes_by_type[t]
        max_score = max(nodes_df.loc[c, "puntaje"] for c in candidates)
        best_by_type[t] = [c for c in candidates if nodes_df.loc[c, "puntaje"] == max_score]

    # Si hay empates, desempatar por menor distancia total
    node_lists = [best_by_type[t] for t in type_order]
    best_route = None
    best_dist = float("inf")

    for combo in product(*node_lists):
        route = [0] + list(combo) + [0]
        dist = evaluate_route(route, dist_matrix)
        if dist < best_dist:
            best_dist = dist
            best_route = route

    total_score = sum(nodes_df.loc[n, "puntaje"] for n in best_route[1:-1])
    return best_route, total_score
