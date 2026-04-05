from src.optimizer import evaluate_route


def print_route(route, nodes_df, value, criterion, dist_matrix, time_matrix, schedule=None):
    """
    Imprime en consola el resultado del recorrido óptimo.

    Muestra una tabla con cada paso (ID, nombre, tipo, puntaje),
    el detalle tramo a tramo (distancia y tiempo), y los totales.
    Si se provee schedule, muestra llegada/salida por parada.

    Args:
        route: lista de IDs del recorrido (incluyendo depot al inicio y al final).
        nodes_df: DataFrame de nodos.
        value: valor óptimo encontrado (costo o puntaje).
        criterion: "distancia", "tiempo" o "puntaje".
        dist_matrix: DataFrame de distancias.
        time_matrix: DataFrame de tiempos.
        schedule: lista de dicts con llegada/salida por parada (opcional).
    """
    criterion_labels = {
        "distancia": "Minimizar distancia",
        "tiempo": "Minimizar tiempo",
        "puntaje": "Maximizar puntaje",
    }

    print(f"\n{'='*60}")
    print(f"  Criterio: {criterion_labels[criterion]}")
    print(f"{'='*60}\n")

    # Tabla de ruta
    if schedule:
        print(f"  {'Paso':<6} {'ID':<5} {'Nombre':<30} {'Tipo':<14} {'Pts':<5} {'Llegada':<8} {'Salida':<8}")
        print(f"  {'-'*76}")
        for step, node_id in enumerate(route):
            nombre = nodes_df.loc[node_id, "nombre"]
            tipo = nodes_df.loc[node_id, "tipo"]
            puntaje = nodes_df.loc[node_id, "puntaje"]
            llegada = schedule[step]["llegada"] or "—"
            salida = schedule[step]["salida"] or "—"
            espera = " ⏳" if schedule[step]["espera"] else ""
            print(f"  {step:<6} {node_id:<5} {nombre:<30} {tipo:<14} {puntaje:<5} {llegada:<8} {salida:<8}{espera}")
    else:
        print(f"  {'Paso':<6} {'ID':<5} {'Nombre':<32} {'Tipo':<15} {'Puntaje':<8}")
        print(f"  {'-'*66}")
        for step, node_id in enumerate(route):
            nombre = nodes_df.loc[node_id, "nombre"]
            tipo = nodes_df.loc[node_id, "tipo"]
            puntaje = nodes_df.loc[node_id, "puntaje"]
            print(f"  {step:<6} {node_id:<5} {nombre:<32} {tipo:<15} {puntaje:<8}")

    # Tramos
    print(f"\n  {'Tramo':<35} {'Dist (km)':<12} {'Tiempo (min)':<12}")
    print(f"  {'-'*59}")

    total_dist = 0.0
    total_time = 0.0
    for i in range(len(route) - 1):
        orig = route[i]
        dest = route[i + 1]
        d = dist_matrix.loc[orig, dest]
        t = time_matrix.loc[orig, dest]
        total_dist += d
        total_time += t
        n_orig = nodes_df.loc[orig, "nombre"]
        n_dest = nodes_df.loc[dest, "nombre"]
        label = f"{n_orig[:15]} -> {n_dest[:15]}"
        print(f"  {label:<35} {d:<12.1f} {t:<12.0f}")

    total_score = sum(nodes_df.loc[n, "puntaje"] for n in route[1:-1])

    print(f"\n  {'='*60}")
    print(f"  Distancia total:  {total_dist:.1f} km")
    print(f"  Tiempo total:     {total_time:.0f} min")
    print(f"  Puntaje total:    {total_score}")
    print(f"  {'='*60}\n")
