import streamlit as st
import pandas as pd
import folium
from datetime import time
from streamlit_folium import st_folium
from src.data_loader import load_nodes, load_matrix, get_nodes_by_type, list_depots
from src.optimizer import optimize

TYPE_COLORS = {
    "depot": "black",
    "Cervecería": "red",
    "Heladería": "blue",
    "Museo": "green",
    "Restaurante": "orange",
}

st.set_page_config(page_title="Recorrido Turístico - Rosario", page_icon="🗺️", layout="wide")

# --- Cargar datos ---
@st.cache_data(ttl=60)
def load_data(depot_folder):
    nodes = load_nodes(f"{depot_folder}/g_nodos.txt")
    dist = load_matrix(f"{depot_folder}/g_distancias.csv")
    time_mat = load_matrix(f"{depot_folder}/g_tiempos.csv")
    by_type = get_nodes_by_type(nodes)
    return nodes, dist, time_mat, by_type

# --- Header ---
st.title("🗺️ Optimizador de Recorrido Turístico")

# --- Selección de depot ---
_PLACEHOLDER = "— Seleccioná un punto de partida —"

depots = list_depots("data")
if not depots:
    st.error("No se encontraron depots en la carpeta data/. Creá subcarpetas con g_nodos.txt, g_distancias.csv y g_tiempos.csv.")
    st.stop()

depot_paths = {name: path for path, name in depots}
depot_names = [_PLACEHOLDER] + list(depot_paths.keys())

selected_depot_name = st.selectbox("Punto de partida", options=depot_names)

if selected_depot_name == _PLACEHOLDER:
    st.stop()

# Limpiar resultados previos si cambió el depot
if st.session_state.get("_active_depot") != selected_depot_name:
    for key in ("best_route", "best_value", "schedule", "type_order", "criterion", "stay_times"):
        st.session_state.pop(key, None)
    st.session_state["_active_depot"] = selected_depot_name

depot_folder = depot_paths[selected_depot_name]
nodes, dist, time_mat, by_type = load_data(depot_folder)

st.markdown(f"Armá el mejor recorrido por Rosario eligiendo los **tipos de actividad** a visitar, partiendo y regresando desde **{selected_depot_name}**.")

st.divider()

available_types = list(by_type.keys())

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
    st.subheader("Cantidad de paradas")
    num_stops = st.number_input(
        "¿Cuántos lugares querés visitar?",
        min_value=1,
        max_value=20,
        value=len(available_types),
        step=1,
    )

col3, _ = st.columns(2)
with col3:
    st.subheader("Hora de salida del depot")
    start_time_input = st.time_input("Hora de salida", value=time(10, 0))
    start_minutes = start_time_input.hour * 60 + start_time_input.minute

st.divider()

# --- Selección de tipos y tiempos de estadía ---
st.subheader("Orden de actividades y tiempo de estadía")
st.caption("Elegí el tipo de actividad para cada parada y cuánto tiempo querés quedarte.")

type_order = []
stay_times = []

for i in range(num_stops):
    col_type, col_time = st.columns([3, 1])
    with col_type:
        choice = st.selectbox(
            f"Parada {i+1}",
            options=available_types,
            key=f"type_{i}",
        )
        type_order.append(choice)
    with col_time:
        stay = st.number_input(
            f"Tiempo en parada {i+1} (min)",
            min_value=0,
            value=30,
            step=5,
            key=f"stay_{i}",
        )
        stay_times.append(stay)

st.divider()

# --- Optimizar ---
if st.button("🚀 Optimizar recorrido", type="primary", use_container_width=True):
    cost_matrix = dist if criterion == "distancia" else time_mat if criterion == "tiempo" else dist
    best_route, best_value, schedule = optimize(
        nodes, by_type, cost_matrix, type_order, criterion,
        dist_matrix=dist, stay_times=stay_times, time_matrix=time_mat,
        start_minutes=start_minutes,
    )
    st.session_state["best_route"] = best_route
    st.session_state["best_value"] = best_value
    st.session_state["schedule"] = schedule
    st.session_state["type_order"] = type_order
    st.session_state["criterion"] = criterion
    st.session_state["stay_times"] = stay_times

# --- Mostrar resultados si existen ---
if "best_route" in st.session_state:
    best_route = st.session_state["best_route"]
    best_value = st.session_state["best_value"]
    schedule = st.session_state["schedule"]
    saved_order = st.session_state["type_order"]
    saved_criterion = st.session_state["criterion"]
    stay_times_saved = st.session_state["stay_times"]

    if best_route is None:
        st.warning("No existe ruta factible con los horarios y tiempos de estadía indicados.")
        st.stop()

    # --- Métricas ---
    total_dist = sum(dist.loc[best_route[i], best_route[i+1]] for i in range(len(best_route)-1))
    total_travel_time = sum(time_mat.loc[best_route[i], best_route[i+1]] for i in range(len(best_route)-1))/60
    total_stay_time = sum(stay_times_saved)
    total_time = total_travel_time + total_stay_time
    total_score = sum(nodes.loc[n, "puntaje"] for n in best_route[1:-1])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📏 Distancia total", f"{(total_dist/1000):.1f} km")
    m2.metric("🚶 Tiempo traslado", f"{total_travel_time:.0f} min")
    m3.metric("🕐 Tiempo en lugares", f"{total_stay_time:.0f} min")
    m4.metric("⏱️ Tiempo total", f"{total_time:.0f} min")

    st.metric("⭐ Puntaje total", f"{total_score:.1f} pts")

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
        is_depot = nodes.loc[node_id, "tipo"] == "depot"
        stay_idx = step - 1
        stay_val = 0 if is_depot else stay_times_saved[stay_idx] if 0 <= stay_idx < len(stay_times_saved) else 0
        row = {
            "Paso": step,
            "ID": node_id,
            "Nombre": nodes.loc[node_id, "nombre"],
            "Tipo": nodes.loc[node_id, "tipo"],
            "Puntaje": nodes.loc[node_id, "puntaje"],
            "Tiempo estadía (min)": stay_val,
        }
        if schedule is not None:
            row["Llegada"] = schedule[step]["llegada"] or "—"
            row["Salida"] = schedule[step]["salida"] or "—"
            row["Espera"] = "⏳ sí" if schedule[step]["espera"] else ""
        route_data.append(row)

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
            "Distancia (km)": round(dist.loc[orig, dest] / 1000, 2),
            "Tiempo traslado (min)": round(int(time_mat.loc[orig, dest])/60,2),
        })

    st.dataframe(pd.DataFrame(legs_data), use_container_width=True, hide_index=True)

    # --- Nodos disponibles por tipo ---
    with st.expander("📌 Ver todos los nodos disponibles por tipo"):
        for tipo in saved_order:
            node_ids = by_type[tipo]
            df = nodes.loc[node_ids][["nombre", "puntaje"]].sort_values("puntaje", ascending=False)
            selected_in_type = [n for n in best_route[1:-1] if nodes.loc[n, "tipo"] == tipo]
            selected_names = ", ".join(nodes.loc[n, "nombre"] for n in selected_in_type)
            st.markdown(f"**{tipo}** — seleccionados: **{selected_names}**")
            st.dataframe(df, use_container_width=True)
