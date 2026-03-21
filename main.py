from src.data_loader import load_nodes, load_matrix, get_nodes_by_type
from src.optimizer import optimize, TYPES
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
            return TYPES
        parts = [p.strip().lower() for p in raw.split(",")]
        if len(parts) != len(tipos):
            print(f"  Debe haber exactamente {len(tipos)} tipos.")
            continue
        if set(parts) != set(tipos):
            print(f"  Tipos inválidos. Usar: {', '.join(tipos)}")
            continue
        return parts


def main():
    nodes = load_nodes("data/nodos.txt")
    dist = load_matrix("data/distancias.csv")
    time = load_matrix("data/tiempos.csv")
    by_type = get_nodes_by_type(nodes)

    criterion = prompt_criterion()
    type_order = prompt_type_order(by_type)

    if criterion == "distancia":
        cost_matrix = dist
    elif criterion == "tiempo":
        cost_matrix = time
    else:
        cost_matrix = dist  # para desempate en puntaje

    best_route, best_value = optimize(
        nodes, by_type, cost_matrix, type_order, criterion, dist_matrix=dist
    )

    print_route(best_route, nodes, best_value, criterion, dist, time)


if __name__ == "__main__":
    main()
