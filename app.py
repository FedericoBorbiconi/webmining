import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from src.data_loader import load_nodes, load_matrix, get_nodes_by_type
from src.optimizer import optimize

TYPE_COLORS = {
    "depot": "black",
    "cultura": "blue",
    "gastronomia": "red",
    "naturaleza": "green",
    "comercio": "orange",
}

st.set_page_config(page_title="Recorrido Turístico - Rosario", page_icon="🗺️", layout="wide")

# --- Cargar datos ---
@st.cache_data(ttl=60)
def load_data():
    nodes = load_nodes("data/g_nodos.txt")
    dist = load_matrix("data/g_distancias.csv")
    time = load_matrix("data/g_tiempos.csv")
    by_type = get_nodes_by_type(nodes)
    return nodes, dist, time, by_type

nodes, dist, time, by_type = load_data()

# --- Header ---
st.title("🗺️ Optimizador de Recorrido Turístico")
st.markdown("Armá el mejor recorrido por Rosario visitando **un lugar de cada tipo**, partiendo y regresando al depot.")

st.divider()

# --- Configuración ---
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
    st.caption("Elegí el orden de los tipos de actividad en tu recorrido.")

    type_order = []
    available = list(by_type.keys())
    for i in range(len(available)):
        label = f"Parada {i+1}"
        remaining = [t for t in available if t not in type_order]
        choice = st.selectbox(label, options=remaining, key=f"type_{i}")
        type_order.append(choice)

st.divider()

# --- Optimizar (guarda resultado en session_state) ---
if st.button("🚀 Optimizar recorrido", type="primary", use_container_width=True):
    cost_matrix = dist if criterion == "distancia" else time if criterion == "tiempo" else dist
    best_route, best_value = optimize(nodes, by_type, cost_matrix, type_order, criterion, dist_matrix=dist)
    st.session_state["best_route"] = best_route
    st.session_state["best_value"] = best_value
    st.session_state["type_order"] = type_order
    st.session_state["criterion"] = criterion

# --- Mostrar resultados si existen ---
if "best_route" in st.session_state:
    best_route = st.session_state["best_route"]
    best_value = st.session_state["best_value"]
    saved_order = st.session_state["type_order"]
    saved_criterion = st.session_state["criterion"]

    # --- Métricas ---
    total_dist = sum(dist.loc[best_route[i], best_route[i+1]] for i in range(len(best_route)-1))
    total_time = sum(time.loc[best_route[i], best_route[i+1]] for i in range(len(best_route)-1))
    total_score = sum(nodes.loc[n, "puntaje"] for n in best_route[1:-1])

    m1, m2, m3 = st.columns(3)
    m1.metric("📏 Distancia total", f"{(total_dist/1000):.1f} km")
    m2.metric("⏱️ Tiempo total", f"{total_time:.0f} min")
    m3.metric("⭐ Puntaje total", f"{total_score} pts")

    st.divider()

    # --- Mapa del recorrido ---
    st.subheader("🗺️ Mapa del recorrido")

    center_lat = nodes["lat"].mean()
    center_lon = nodes["lon"].mean()
    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="CartoDB positron")

    # Marcadores
    for step, node_id in enumerate(best_route):
        lat = nodes.loc[node_id, "lat"]
        lon = nodes.loc[node_id, "lon"]
        tipo = nodes.loc[node_id, "tipo"]
        nombre = nodes.loc[node_id, "nombre"]
        color = TYPE_COLORS.get(tipo, "gray")

        if tipo == "depot":
            icon = folium.Icon(color=color, icon="home", prefix="fa")
        else:
            icon = folium.Icon(color=color, icon="info-sign")

        folium.Marker(
            location=[lat, lon],
            popup=f"<b>{step}. {nombre}</b><br>Tipo: {tipo}<br>Puntaje: {nodes.loc[node_id, 'puntaje']}",
            tooltip=f"{step}. {nombre}",
            icon=icon,
        ).add_to(fmap)

    # Líneas del recorrido
    route_coords = [[nodes.loc[nid, "lat"], nodes.loc[nid, "lon"]] for nid in best_route]
    folium.PolyLine(
        locations=route_coords,
        color="#3388ff",
        weight=4,
        opacity=0.8,
        dash_array="10",
    ).add_to(fmap)

    # Números de tramo en puntos medios
    for i in range(len(best_route) - 1):
        orig = best_route[i]
        dest = best_route[i + 1]
        mid_lat = (nodes.loc[orig, "lat"] + nodes.loc[dest, "lat"]) / 2
        mid_lon = (nodes.loc[orig, "lon"] + nodes.loc[dest, "lon"]) / 2
        folium.Marker(
            location=[mid_lat, mid_lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:12px;color:#3388ff;font-weight:bold;">{i+1}</div>',
                icon_size=(20, 20),
            ),
        ).add_to(fmap)

    st_folium(fmap, use_container_width=True, height=500, returned_objects=[])

    # Leyenda
    legend_html = " | ".join(
        f'<span style="color:{c};font-weight:bold;">●</span> {t.capitalize()}'
        for t, c in TYPE_COLORS.items()
    )
    st.caption(legend_html, unsafe_allow_html=True)

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

    # --- Nodos disponibles por tipo ---
    with st.expander("📌 Ver todos los nodos disponibles por tipo"):
        for tipo in saved_order:
            node_ids = by_type[tipo]
            df = nodes.loc[node_ids][["nombre", "puntaje"]].sort_values("puntaje", ascending=False)
            selected = [n for n in best_route[1:-1] if nodes.loc[n, "tipo"] == tipo][0]
            st.markdown(f"**{tipo.capitalize()}** — seleccionado: **{nodes.loc[selected, 'nombre']}**")
            st.dataframe(df, use_container_width=True)
