import streamlit as st
import polars as pl
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from shapely.geometry import Point, Polygon
import numpy as np

st.set_page_config(page_title="Sélecteur de Placettes", page_icon="🌳", layout="wide")


# @st.cache_data
# def load_data():
#     lat_center, lon_center = 48.8566, 2.3522
#     n_points = 100
#     data = pl.DataFrame(
#         {
#             "placette_id": [f"P{i + 1}" for i in range(n_points)],
#             "latitude": lat_center + (np.arange(n_points) * 0.001) + np.random.uniform(-0.005, 0.005, n_points),
#             "longitude": lon_center + (np.arange(n_points) * 0.001) + np.random.uniform(-0.005, 0.005, n_points),
#             "hauteur_moyenne_arbres": np.random.uniform(15, 30, n_points).round(1),
#             "densite": np.random.randint(300, 800, n_points),
#         }
#     )
#     return data
# df = load_data()


def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Calcule la distance du grand cercle entre deux points
    sur la terre (spécifiés en degrés décimaux).
    Retourne la distance en mètres.
    """
    # Convertit les degrés décimaux en radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # Formule Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371000  # Rayon de la Terre en mètres
    return c * r


if "grid_data" not in st.session_state:
    st.warning("Veuillez d'abord sélectionner une commune et générer un quadrillage sur la page d'accueil.")
    st.page_link("app.py", label="Retour à l'accueil", icon="🏠")
    st.stop()

# Charge les données depuis l'état de session
df = st.session_state["grid_data"]
selection_name = st.session_state["selection_name"]
selection_geometry = st.session_state["selection_geometry"]

st.title(f"🗺️ Analyse Interactive : {selection_name}")

if "drawings" not in st.session_state:
    st.session_state.drawings = []

# --- Mise en page et création de la carte ---
col1, col2 = st.columns([0.5, 0.5])
with col1:
    st.subheader("Carte des placettes")
    map_center = [df["latitude"].mean(), df["longitude"].mean()]
    m = folium.Map(location=map_center, zoom_start=12)
    Draw(
        export=True,
        draw_options={"polyline": False, "polygon": True, "rectangle": True, "circle": True, "marker": False, "circlemarker": False},
    ).add_to(m)
    for row in df.iter_rows(named=True):
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            color="blue",
            fill=True,
            fill_color="darkblue",
            tooltip=f"ID: {row['placette_id']}\nHauteur: {row['hauteur_moyenne_arbres']}m",
        ).add_to(m)

    output = st_folium(
        m,
        returned_objects=["last_active_drawing", "last_object_clicked", "all_drawings"],
        width="100%",
        height=500,
    )

with col2:
    st.subheader("📊 Indicateurs de la Sélection")

    selected_points_df = pl.DataFrame()
    current_drawings = output.get("all_drawings")

    # CAS 1 : L'utilisateur a cliqué sur la poubelle
    if st.session_state.drawings and not current_drawings:
        st.toast("🗑️ Sélection annulée !")

    # CAS 2 : Un point existant a été cliqué
    elif output.get("last_object_clicked"):
        clicked_lat = output["last_object_clicked"]["lat"]
        clicked_lon = output["last_object_clicked"]["lng"]
        selected_points_df = df.filter((pl.col("latitude") == clicked_lat) & (pl.col("longitude") == clicked_lon))

    # CAS 3 : Un nouveau dessin a été fait
    elif output.get("last_active_drawing"):
        drawing = output["last_active_drawing"]
        shape_type = drawing["geometry"]["type"]

        # Si c'est un polygone (ou rectangle)
        if shape_type in ["Polygon"]:
            drawn_polygon = Polygon([(p[1], p[0]) for p in drawing["geometry"]["coordinates"][0]])
            coords = list(zip(df["latitude"], df["longitude"]))
            mask = [Point(p).within(drawn_polygon) for p in coords]
            selected_points_df = df.filter(pl.Series(mask, dtype=pl.Boolean))

        # ### AJOUT ### : Si c'est un cercle
        elif shape_type == "Point":  # Folium représente un cercle par son point central
            center_lon, center_lat = drawing["geometry"]["coordinates"]
            radius_m = drawing["properties"]["radius"]

            # Calcule la distance de chaque placette au centre du cercle
            distances = haversine_distance(center_lon, center_lat, df["longitude"], df["latitude"])

            # Le masque est True si la distance est inférieure ou égale au rayon
            mask = distances <= radius_m
            selected_points_df = df.filter(mask)

    st.session_state.drawings = current_drawings

    if not selected_points_df.is_empty():
        st.success(f"**{len(selected_points_df)}** placette(s) sélectionnée(s) !")
        avg_height = selected_points_df["hauteur_moyenne_arbres"].mean()
        avg_density = selected_points_df["densite"].mean()
        metric1, metric2 = st.columns(2)
        metric1.metric(label="Hauteur moyenne", value=f"{avg_height:.1f} m")
        metric2.metric(label="Densité moyenne", value=f"{avg_density:.0f} arbres/ha")
        st.write("### Données sélectionnées :")
        st.dataframe(selected_points_df.select(["placette_id", "hauteur_moyenne_arbres", "densite"]))
    else:
        st.info("👈 Cliquez sur un point ou utilisez les outils pour dessiner une zone.")
