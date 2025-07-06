
install spatial; load spatial;

-- from .shp to geo.parquet
copy 'forets_anciennes_Etat_Major.shp' to 'forets_anciennes_Etat_Major.parquet';
copy 'masque foret2.gpkg' to 'masque foret2.parquet';

-- convert lambert to WGS64
copy(
	select *, ST_FlipCoordinates(ST_Transform(geom, 'EPSG:2154', 'EPSG:4326')) AS geom_wgs84,
	from 'D:\Documents\codes\py_script_store\forets_explo\data/masque foret2.parquet'
) to 'D:\Documents\codes\py_script_store\forets_explo\data/masque foret2.parquet';


select
	f_nf,
	count(1) nb_objets,
	-- ST_Union_Agg(ST_Simplify(geom_wgs84, 100)) AS geom_simplified,
from 'D:\Documents\codes\py_script_store\forets_explo\data/forets_anciennes_Etat_Major.parquet'
group by all

------------------------------------------------------------------------------------
-- masque foret2
------------------------------------------------------------------------------------

from 'D:\Documents\codes\py_script_store\forets_explo\data/masque foret2.parquet'
limit 100

copy(
	select * replace(ST_FlipCoordinates(ST_Transform(geom, 'EPSG:2154', 'EPSG:4326')) AS geom),
	from 'masque foret2.parquet'
) to 'masque foret2.parquet';


------------------------------------------------------------------------------------
-- départements --> https://geoservices.ign.fr/geofla
------------------------------------------------------------------------------------
copy (
	select
		ID_GEOFLA::char as ID_GEOFLA,
		CODE_DEPT::char as CODE_DEPT,
		NOM_DEPT::char as NOM_DEPT,
		CODE_CHF::char as CODE_CHF,
		NOM_CHF::char as NOM_CHF,
		X_CHF_LIEU,
		Y_CHF_LIEU,
		CODE_REG::char as CODE_REG,
		NOM_REG::char as NOM_REG,
		ST_FlipCoordinates(ST_Transform(geom, 'EPSG:2154', 'EPSG:4326')) as geom,
		st_centroid(geom) as geom_centroid,
		-- ST_FlipCoordinates(ST_Transform(st_point(X_CENTROID, Y_CENTROID), 'EPSG:2154', 'EPSG:4326')) as geom_centroid,
	from 'D:\Documents\codes\py_script_store\forets_explo\data\geofla_departement/departement.shp'
) to 'D:\Documents\codes\py_script_store\forets_explo\data/departements_geofla.parquet';


------------------------------------------------------------------------------------
-- communes --> https://geoservices.ign.fr/geofla
------------------------------------------------------------------------------------
copy (
	select
		ID_GEOFLA::char as id_geofla,
		CODE_COM::char as code_com,
		INSEE_COM::char as insee_com,
		NOM_COM::char as nom_com,
		STATUT::char as statut,
		Z_MOYEN as z_moyen,
		SUPERFICIE as superficie,
		POPULATION as population,
		CODE_ARR::char as code_arr,
		CODE_DEPT::char as code_dept,
		NOM_DEPT::char as nom_dept,
		CODE_REG::char as code_reg,
		NOM_REG::char as nom_reg,
		ST_FlipCoordinates(ST_Transform(geom, 'EPSG:2154', 'EPSG:4326')) as geom,
		ST_FlipCoordinates(ST_Transform(st_point(X_CHF_LIEU, Y_CHF_LIEU), 'EPSG:2154', 'EPSG:4326')) as geom_cheflieu,
		-- st_centroid(geom) as geom_centroid,
		-- ST_FlipCoordinates(ST_Transform(st_point(X_CENTROID, Y_CENTROID), 'EPSG:2154', 'EPSG:4326')) as geom_centroid,
	from 'D:\Documents\codes\py_script_store\forets_explo\data\geofla_commune/commune.shp'
) to 'D:\Documents\codes\py_script_store\forets_explo\data/communes_geofla.parquet'

summarize 'D:\Documents\codes\py_script_store\forets_explo\data/communes_geofla.parquet'
