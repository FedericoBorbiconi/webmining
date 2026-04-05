from src.data_loader import load_nodes, load_matrix, get_nodes_by_type
from src.optimizer import optimize
from src.display import print_route


def prompt_criterion():
    """
    Solicita al usuario el criterio de optimización por consola.

    Returns:
        String "distancia", "tiempo" o "puntaje".
    """
    print("\n  Elegir criterio de optimización:")
    print("  [1] Minimizar distancia")
    print("  [2] Minimizar tiempo")
    print("  [3] Maximizar puntaje")
    while True:
        choice = input("  > ").strip()
        if choice == "1":
            return "distancia"
        elif choice == "2":
            return "tiempo"
        elif choice == "3":
            return "puntaje"
        print("  Opción inválida. Elegir 1, 2 o 3.")


def prompt_type_order(nodes_by_type):
    """
    Solicita al usuario el orden de los tipos de actividad.

    Permite ingresar un orden personalizado separado por comas o
    presionar Enter para usar el orden por defecto.

    Args:
        nodes_by_type: diccionario {tipo: [IDs]} para validar los tipos disponibles.

    Returns:
        Lista de strings con los tipos en el orden elegido.
    """
    tipos = list(nodes_by_type.keys())
    print(f"\n  Tipos disponibles: {', '.join(tipos)}")
    print(f"  Ingresá el orden separado por comas (ej: cultura,gastronomia,naturaleza,comercio)")
    print(f"  O presioná Enter para usar el orden por defecto.")
    while True:
        raw = input("  > ").strip()
        if raw == "":
            return tipos
        parts = [p.strip().lower() for p in raw.split(",")]
        if len(parts) != len(tipos):
            print(f"  Debe haber exactamente {len(tipos)} tipos.")
            continue
        if set(parts) != set(tipos):
            print(f"  Tipos inválidos. Usar: {', '.join(tipos)}")
            continue
        return parts


def prompt_start_time():
    """
    Solicita la hora de salida del depot por consola.

    Returns:
        Entero con los minutos desde medianoche (ej: 10:00 → 600).
    """
    print("\n  Hora de salida del depot (HH:MM, ej: 10:00):")
    while True:
        raw = input("  > ").strip()
        try:
            h, m = raw.split(":")
            return int(h) * 60 + int(m)
        except ValueError:
            print("  Formato inválido. Usar HH:MM (ej: 10:00).")


def prompt_stay_time(tipo):
    """
    Solicita el tiempo de estadía para un tipo de actividad.

    Returns:
        Entero con los minutos de estadía (default 30).
    """
    print(f"  Tiempo de estadía en {tipo} (min, Enter para 30):")
    raw = input("  > ").strip()
    if raw == "":
        return 30
    try:
        return int(raw)
    except ValueError:
        return 30


def main():
    nodes = load_nodes("data/g_nodos.txt")
    dist = load_matrix("data/g_distancias.csv")
    time = load_matrix("data/g_tiempos.csv")
    by_type = get_nodes_by_type(nodes)

    criterion = prompt_criterion()
    type_order = prompt_type_order(by_type)
    start_minutes = prompt_start_time()
    stay_times = [prompt_stay_time(t) for t in type_order]

    if criterion == "distancia":
        cost_matrix = dist
    elif criterion == "tiempo":
        cost_matrix = time
    else:
        cost_matrix = dist  # para desempate en puntaje

    best_route, best_value, schedule = optimize(
        nodes, by_type, cost_matrix, type_order, criterion, dist_matrix=dist,
        stay_times=stay_times, time_matrix=time, start_minutes=start_minutes,
    )

    if best_route is None:
        print("\n  No existe ruta factible con los horarios y tiempos de estadía indicados.")
        return

    print_route(best_route, nodes, best_value, criterion, dist, time, schedule=schedule)


if __name__ == "__main__":
    main()
