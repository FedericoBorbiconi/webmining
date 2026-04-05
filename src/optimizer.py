from itertools import product


def _mins_to_hhmm(minutes: float) -> str:
    """Convierte minutos desde medianoche a string "HH:MM"."""
    minutes = int(minutes)
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def compute_schedule(route, stay_times, nodes_df, time_matrix, start_minutes):
    """
    Calcula el horario de llegada/salida para cada nodo de la ruta.

    Si se llega antes de la apertura, se espera hasta que abra.
    La ruta es infactible si la salida de algún lugar supera su cierre.
    El depot (nodo 0) al inicio y al final no tiene restricciones de horario.

    Args:
        route: lista de IDs [0, n1, n2, ..., 0].
        stay_times: lista de minutos de estadía por parada (excluye depot).
        nodes_df: DataFrame con columnas apertura_min y cierre_min.
        time_matrix: DataFrame de tiempos de traslado entre nodos (minutos).
        start_minutes: minutos desde medianoche de la salida del depot.

    Returns:
        Tupla (feasible: bool, schedule: list[dict]).
        Cada dict tiene: node_id, llegada, salida (strings HH:MM), espera (bool).
        El primer elemento corresponde al depot de salida (solo salida),
        el último al depot de regreso (solo llegada).
    """
    schedule = []
    current_time = start_minutes
    schedule.append({
        "node_id": route[0],
        "llegada": None,
        "salida": _mins_to_hhmm(current_time),
        "espera": False,
    })

    # Recorrer paradas intermedias (excluir el último depot de retorno)
    for idx, node_id in enumerate(route[1:-1]):
        travel = time_matrix.loc[route[idx], node_id] / 60  # segundos → minutos
        arrival = current_time + travel
        apertura = nodes_df.loc[node_id, "apertura_min"]
        cierre = nodes_df.loc[node_id, "cierre_min"]

        effective_arrival = max(arrival, apertura)
        stay = stay_times[idx] if idx < len(stay_times) else 0
        departure = effective_arrival + stay

        if departure > cierre:
            return False, []

        schedule.append({
            "node_id": node_id,
            "llegada": _mins_to_hhmm(effective_arrival),
            "salida": _mins_to_hhmm(departure),
            "espera": effective_arrival > arrival,
        })
        current_time = departure

    # Depot de regreso: solo llegada, sin restricción
    last_node = route[-2]
    travel_back = time_matrix.loc[last_node, route[-1]] / 60  # segundos → minutos
    arrival_depot = current_time + travel_back
    schedule.append({
        "node_id": route[-1],
        "llegada": _mins_to_hhmm(arrival_depot),
        "salida": None,
        "espera": False,
    })

    return True, schedule


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


def optimize(nodes_df, nodes_by_type, cost_matrix, type_order, criterion,
             dist_matrix=None, stay_times=None, time_matrix=None, start_minutes=None):
    """
    Encuentra el recorrido óptimo seleccionando un nodo de cada tipo mediante fuerza bruta.

    Evalúa todas las combinaciones posibles (una por tipo) y retorna la mejor
    según el criterio elegido. El recorrido parte y regresa al depot (nodo 0).
    Si se proveen stay_times, time_matrix y start_minutes, filtra rutas infactibles
    según las ventanas de tiempo de cada nodo.

    Args:
        nodes_df: DataFrame de nodos con columnas nombre, tipo, puntaje,
                  apertura_min, cierre_min.
        nodes_by_type: diccionario {tipo: [IDs]} con los nodos agrupados por tipo.
        cost_matrix: DataFrame de costos (distancia o tiempo) a minimizar.
        type_order: lista con el orden de tipos a visitar.
        criterion: "distancia", "tiempo" o "puntaje".
        dist_matrix: DataFrame de distancias, usado para desempatar cuando criterion="puntaje".
        stay_times: lista de minutos de estadía por parada (una por tipo en type_order).
        time_matrix: DataFrame de tiempos de traslado, requerido para time windows.
        start_minutes: minutos desde medianoche de la salida del depot.

    Returns:
        Tupla (mejor_ruta, mejor_valor, schedule) donde mejor_ruta es una lista de IDs,
        mejor_valor es el costo mínimo o puntaje máximo, y schedule es la lista de
        horarios por parada (o None si no se usaron ventanas de tiempo).
    """
    use_tw = stay_times is not None and time_matrix is not None and start_minutes is not None

    if criterion == "puntaje":
        return _optimize_score(
            nodes_df, nodes_by_type, type_order,
            dist_matrix if dist_matrix is not None else cost_matrix,
            stay_times=stay_times, time_matrix=time_matrix, start_minutes=start_minutes,
        )

    node_lists = [nodes_by_type[t] for t in type_order]
    best_route = None
    best_cost = float("inf")
    best_schedule = None

    for combo in product(*node_lists):
        if len(set(combo)) != len(combo):
            continue
        route = [0] + list(combo) + [0]

        if use_tw:
            feasible, schedule = compute_schedule(route, stay_times, nodes_df, time_matrix, start_minutes)
            if not feasible:
                continue
        else:
            schedule = None

        cost = evaluate_route(route, cost_matrix)
        if cost < best_cost:
            best_cost = cost
            best_route = route
            best_schedule = schedule

    return best_route, best_cost, best_schedule


def _optimize_score(nodes_df, nodes_by_type, type_order, dist_matrix,
                    stay_times=None, time_matrix=None, start_minutes=None):
    """
    Optimiza el recorrido maximizando el puntaje total.

    Con ventanas de tiempo activas, considera todos los nodos de cada tipo
    (no solo los de mayor puntaje) para garantizar factibilidad, priorizando
    por puntaje y desempatando por distancia.

    Args:
        nodes_df: DataFrame de nodos con columnas nombre, tipo, puntaje,
                  apertura_min, cierre_min.
        nodes_by_type: diccionario {tipo: [IDs]}.
        type_order: lista con el orden de tipos a visitar.
        dist_matrix: DataFrame de distancias para desempate.
        stay_times: lista de minutos de estadía (opcional).
        time_matrix: DataFrame de tiempos de traslado (opcional).
        start_minutes: minutos de salida del depot (opcional).

    Returns:
        Tupla (mejor_ruta, puntaje_total, schedule).
    """
    use_tw = stay_times is not None and time_matrix is not None and start_minutes is not None

    if use_tw:
        # Con TW: explorar todos los nodos, seleccionar el factible de mayor puntaje
        node_lists = [nodes_by_type[t] for t in type_order]
    else:
        # Sin TW: solo candidatos de mayor puntaje por tipo
        best_by_type = {}
        for t in type_order:
            candidates = nodes_by_type[t]
            max_score = max(nodes_df.loc[c, "puntaje"] for c in candidates)
            best_by_type[t] = [c for c in candidates if nodes_df.loc[c, "puntaje"] == max_score]
        node_lists = [best_by_type[t] for t in type_order]

    best_route = None
    best_score = -1
    best_dist = float("inf")
    best_schedule = None

    for combo in product(*node_lists):
        if len(set(combo)) != len(combo):
            continue
        route = [0] + list(combo) + [0]

        if use_tw:
            feasible, schedule = compute_schedule(route, stay_times, nodes_df, time_matrix, start_minutes)
            if not feasible:
                continue
        else:
            schedule = None

        score = sum(nodes_df.loc[n, "puntaje"] for n in combo)
        dist = evaluate_route(route, dist_matrix)

        if score > best_score or (score == best_score and dist < best_dist):
            best_score = score
            best_dist = dist
            best_route = route
            best_schedule = schedule

    return best_route, best_score, best_schedule
