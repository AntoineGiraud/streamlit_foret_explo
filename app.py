import streamlit as st
import geopandas as gpd
import polars as pl
from shapely.geometry import Point
import numpy as np
import folium
from streamlit_folium import st_folium

# --- Configuration de la Page ---
st.set_page_config(page_title="Configuration de la Grille", page_icon="🗺", layout="wide")

st.title("Génération de placettes 🌲 par commune")
st.info("Comunnes & départements issus du découpage administratif [Geofla](https://geoservices.ign.fr/geofla)")

# --- Fonctions ---


@st.cache_data  # Met en cache les données du fichier pour une performance optimale
def load_geodata(filepath):
    """Charge le fichier GeoParquet des communes."""
    gdf = gpd.read_parquet(filepath)
    # Assure que le système de coordonnées est bien WGS84 (lat/lon)
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf


def generate_grid_in_polygon(gdf_selection, spacing_meters):
    """Génère une grille de points à l'intérieur d'un polygone GeoDataFrame."""
    # Projeter en Lambert-93 (EPSG:2154), un système de coordonnées en mètres pour la France
    gdf_proj = gdf_selection.to_crs(epsg=2154)

    minx, miny, maxx, maxy = gdf_proj.total_bounds

    x_coords = np.arange(minx, maxx, spacing_meters)
    y_coords = np.arange(miny, maxy, spacing_meters)
    grid_x, grid_y = np.meshgrid(x_coords, y_coords)

    grid_points = [Point(x, y) for x, y in zip(grid_x.ravel(), grid_y.ravel())]
    if not grid_points:
        return pl.DataFrame()  # Retourne un DF vide si la grille est vide

    grid_gdf = gpd.GeoDataFrame(geometry=grid_points, crs="EPSG:2154")

    # Ne garder que les points qui sont à l'intérieur du polygone
    points_in_commune = gpd.sjoin(grid_gdf, gdf_proj, how="inner", predicate="within")

    # Reprojeter les points finaux en WGS84 (lat/lon) pour l'affichage
    points_latlon = points_in_commune.to_crs(epsg=4326)

    # Créer le DataFrame Polars final
    df = pl.DataFrame(
        {
            "placette_id": [f"P{i + 1}" for i in range(len(points_latlon))],
            "latitude": points_latlon.geometry.y,
            "longitude": points_latlon.geometry.x,
            # Ajout de données aléatoires pour les autres colonnes
            "hauteur_moyenne_arbres": np.random.uniform(5, 25, len(points_latlon)).round(1),
            "densite": np.random.randint(100, 500, len(points_latlon)),
        }
    )
    return df


# --- Chargement des données ---
geodata = load_geodata("data/communes_geofla.parquet")

# --- Interface Utilisateur ---


col_param, col_resultat = st.columns([0.5, 0.5])

with col_param:
    st.header("Paramétrage")
    st.markdown("Choisissez un département, une commune, puis la finesse du quadrillage.")

    # 1. Sélection du département
    departments = sorted(geodata["nom_dept"].unique())
    selected_dept = st.selectbox("1. Choix du département", options=departments, index=None, placeholder="Sélectionnez un département...")

    # 2. Sélection de la commune (dépend du département)
    if selected_dept:
        communes_in_dept = sorted(geodata[geodata["nom_dept"] == selected_dept]["nom_com"].unique())
        selected_commune = st.selectbox("2. Choix de la commune", options=communes_in_dept, index=None, placeholder="Sélectionnez une commune...")

        # 3. Sélection du grain et génération
        if selected_commune:
            spacing = st.select_slider("3. Choix de l'espacement entre les placettes (en mètres)", options=[100, 250, 500, 1000, 2000], value=500)

            if st.button(f"Générer le Quadrillage pour {selected_commune}", type="primary"):
                with st.spinner(f"Génération d'une grille de {spacing}x{spacing}m..."):
                    # Récupère la géométrie de la commune sélectionnée
                    commune_gdf = geodata[(geodata["nom_dept"] == selected_dept) & (geodata["nom_com"] == selected_commune)]
                    grid_df = generate_grid_in_polygon(commune_gdf, spacing)

                    if not grid_df.is_empty():
                        st.success(f"**{len(grid_df)}** placettes ont été générées avec succès !")

                        # Stocker les données dans l'état de session
                        st.session_state["grid_data"] = grid_df
                        st.session_state["commune_gdf"] = commune_gdf
                        st.session_state["selection_name"] = f"{selected_commune} ({selected_dept})"
                        st.session_state["selection_geometry"] = commune_gdf.geometry

                    else:
                        st.error("Aucune placette n'a pu être générée. La commune est peut-être trop petite pour le grain sélectionné.")

with col_resultat:
    st.header("Résultats")
    if not st.session_state.get("grid_data", pl.DataFrame()).is_empty():
        grid_df = st.session_state["grid_data"]
        commune_gdf = st.session_state["commune_gdf"]

        st.page_link("pages/1_🌳_explore_placettes.py", label="👉 Les données sont prêtes ! RDV sur la page d'exploration")

        st.write("Données sur la commune")
        st.dataframe(commune_gdf)

        st.write(f"Aperçu des {len(grid_df)} placettes générées")
        st.map(grid_df, latitude="latitude", longitude="longitude", height=300)

        # # Calcule le centre de la commune pour centrer la carte
        # center_point = commune_gdf["geom_cheflieu"].iloc[0]
        # map_center = (center_point.y, center_point.x)
        # # center_point = commune_gdf.geom.centroid.iloc[0]
        # # map_center = [center_point.y, center_point.x]
        # print(f"{center_point=}")
        # print(f"{map_center=} yay")

        # # Crée la carte Folium
        # m = folium.Map(location=map_center, zoom_start=11)

        # # 1. Ajoute la couche du polygone de la commune
        # folium.GeoJson(commune_gdf["geom"], style_function=lambda x: {"color": "#0078A3", "weight": 2, "fillOpacity": 0.1}).add_to(m)

        # # 2. Ajoute la couche des points générés
        # for row in grid_df.iter_rows(named=True):
        #     folium.CircleMarker(location=[row["latitude"], row["longitude"]], radius=1, color="red", fill=True).add_to(m)

        # st_folium(m, width="100%", height=400)
