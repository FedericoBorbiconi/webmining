import streamlit as st
import pandas as pd
from src.data_loader import load_nodes, load_matrix, get_nodes_by_type
from src.optimizer import optimize, TYPES

st.set_page_config(page_title="Recorrido Turístico - Rosario", page_icon="🗺️", layout="wide")

# --- Cargar datos ---
@st.cache_data
def load_data():
    nodes = load_nodes("data/nodos.txt")
    dist = load_matrix("data/distancias.csv")
    time = load_matrix("data/tiempos.csv")
    by_type = get_nodes_by_type(nodes)
    return nodes, dist, time, by_type

nodes, dist, time, by_type = load_data()

# --- Header ---
st.title("🗺️ Optimizador de Recorrido Turístico")
st.markdown("Armá el mejor recorrido por Rosario visitando **un lugar de cada tipo**, partiendo y regresando al depot.")

st.divider()

# --- Sidebar: configuración ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Criterio de optimización")
    criterion = st.radio(
        "¿Qué querés optimizar?",
        options=["distancia", "tiempo", "puntaje"],
        format_func=lambda x: {
            "distancia": "📏 Minimizar distancia",
            "tiempo": "⏱️ Minimizar tiempo",
            "puntaje": "⭐ Maximizar puntaje",
        }[x],
    )

with col2:
    st.subheader("Orden de actividades")
    st.caption("Arrastrá para reordenar los tipos de actividad en tu recorrido.")

    type_order = []
    available = TYPES.copy()
    for i in range(4):
        label = f"Parada {i+1}"
        choice = st.selectbox(label, options=available, key=f"type_{i}")
        type_order.append(choice)
        available = [t for t in available if t != choice]

st.divider()

# --- Optimizar ---
if st.button("🚀 Optimizar recorrido", type="primary", use_container_width=True):
    cost_matrix = dist if criterion == "distancia" else time if criterion == "tiempo" else dist
    best_route, best_value = optimize(nodes, by_type, cost_matrix, type_order, criterion, dist_matrix=dist)

    # --- Resultado: métricas ---
    total_dist = sum(dist.loc[best_route[i], best_route[i+1]] for i in range(len(best_route)-1))
    total_time = sum(time.loc[best_route[i], best_route[i+1]] for i in range(len(best_route)-1))
    total_score = sum(nodes.loc[n, "puntaje"] for n in best_route[1:-1])

    m1, m2, m3 = st.columns(3)
    m1.metric("📏 Distancia total", f"{total_dist:.1f} km")
    m2.metric("⏱️ Tiempo total", f"{total_time:.0f} min")
    m3.metric("⭐ Puntaje total", f"{total_score} pts")

    st.divider()

    # --- Tabla de ruta ---
    st.subheader("📋 Recorrido óptimo")

    route_data = []
    for step, node_id in enumerate(best_route):
        route_data.append({
            "Paso": step,
            "ID": node_id,
            "Nombre": nodes.loc[node_id, "nombre"],
            "Tipo": nodes.loc[node_id, "tipo"],
            "Puntaje": nodes.loc[node_id, "puntaje"],
        })

    st.dataframe(pd.DataFrame(route_data), use_container_width=True, hide_index=True)

    # --- Tabla de tramos ---
    st.subheader("🛤️ Detalle tramo a tramo")

    legs_data = []
    for i in range(len(best_route) - 1):
        orig = best_route[i]
        dest = best_route[i + 1]
        legs_data.append({
            "Desde": nodes.loc[orig, "nombre"],
            "Hasta": nodes.loc[dest, "nombre"],
            "Distancia (km)": dist.loc[orig, dest],
            "Tiempo (min)": int(time.loc[orig, dest]),
        })

    st.dataframe(pd.DataFrame(legs_data), use_container_width=True, hide_index=True)

    # --- Nodos disponibles por tipo (referencia) ---
    with st.expander("📌 Ver todos los nodos disponibles por tipo"):
        for tipo in type_order:
            node_ids = by_type[tipo]
            df = nodes.loc[node_ids][["nombre", "puntaje"]].sort_values("puntaje", ascending=False)
            selected = [n for n in best_route[1:-1] if nodes.loc[n, "tipo"] == tipo][0]
            st.markdown(f"**{tipo.capitalize()}** — seleccionado: **{nodes.loc[selected, 'nombre']}**")
            st.dataframe(df, use_container_width=True)
