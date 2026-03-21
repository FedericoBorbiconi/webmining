from diagrams import Diagram
from diagrams.generic.blank import Blank


def build_tsp_flow_diagram() -> None:
    graph_attr = {
        "rankdir": "LR",
        "splines": "spline",
        "fontname": "Helvetica",
        "fontsize": "12",
    }

    node_attr = {
        "shape": "box",
        "style": "rounded,filled",
        "fillcolor": "#F8FAFC",
        "color": "#334155",
        "fontname": "Helvetica",
        "fontsize": "11",
    }

    edge_attr = {
        "color": "#475569",
        "fontname": "Helvetica",
        "fontsize": "10",
    }

    with Diagram(
        name="tsp_flow_diagrams",
        filename="docs/diagrams/tsp_flow_diagrams",
        outformat="png",
        show=False,
        graph_attr=graph_attr,
        node_attr=node_attr,
        edge_attr=edge_attr,
    ):
        input_csv = Blank("CSV de distancias")
        load = Blank("Carga con pandas")
        index_nodes = Blank("Índices de nodos")
        vars_xij = Blank("Variables binarias x_ij")
        constraints = Blank("Restricciones TSP + MTZ")
        objective = Blank("Objetivo: minimizar costo")
        solve = Blank("Resolver con OR-Tools")
        status = Blank("¿Solución factible?")
        extract = Blank("Extraer arcos x_ij = 1")
        review = Blank("Revisar datos/modelo")

        input_csv >> load >> index_nodes >> vars_xij >> constraints >> objective >> solve >> status
        status >> extract
        status >> review


if __name__ == "__main__":
    build_tsp_flow_diagram()
