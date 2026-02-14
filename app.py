import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Configuración de la interfaz
st.set_page_config(page_title="Ruta Sidrera Barakaldo", layout="wide", page_icon="🍎")
st.title("🍎 Nuestra Ruta de la Sidra")
st.markdown("Toca el mapa para situar un bar y completa los datos para guardarlo.")

# 1. CONEXIÓN Y LIMPIEZA DE DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")

df = df_raw.copy()
# Aseguramos que las coordenadas sean números (cambia comas por puntos si las hay)
df['LAT'] = pd.to_numeric(df['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df['LON'] = pd.to_numeric(df['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df.dropna(subset=['LAT', 'LON'])

# 2. CONFIGURACIÓN DEL MAPA SATÉLITE
centro = [43.2960, -2.9975] # Centro en San Vicente
m = folium.Map(location=centro, zoom_start=17, tiles=None)

# Capa de Google Satélite
folium.TileLayer(
    tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr = 'Google Maps',
    name = 'Google Satellite',
    max_zoom = 20,
    control = False
).add_to(m)

# 3. FUNCIÓN DE ICONOS (VASO DE SIDRA VS BOTELLA)
def obtener_icono(formato_texto):
    formato_texto = str(formato_texto)
    # Icono BOTELLA (Fondo verde)
    if "Botella" in formato_texto and "Vasos" not in formato_texto:
        return folium.Icon(color="green", icon="wine-bottle", prefix="fa", icon_color="white")
    # Icono VASO DE SIDRA / POTE (Fondo azul)
    # Usamos glass-whiskey que es un vaso ancho y limpio, sin 'X' ni dibujos raros.
    else:
        return folium.Icon(color="blue", icon="glass-whiskey", prefix="fa", icon_color="white")

# 4. COLOCAR MARCADORES DE LOS BARES YA REGISTRADOS
for i, row in df_mapa.iterrows():
    popup_info = f"""
    <div style='font-family: sans-serif; min-width: 150px;'>
        <h4 style='margin:0; color: #d35400;'>{row['Nombre']}</h4>
        <p style='margin:5px 0;'><b>Sidra:</b> {row['Marca']}<br>
        <b>Formato:</b> {row['Formato']}</p>
        <i style='color: #666; font-size: 0.9em;'>{row['Observaciones']}</i>
    </div>
    """
    folium.Marker(
        [row['LAT'], row['LON']],
        popup=folium.Popup(popup_info, max_width=300),
        tooltip=row['Nombre'],
        icon=obtener_icono(row.get('Formato', 'Vaso'))
    ).add_to(m)

# 5. VISUALIZACIÓN DEL MAPA Y CAPTURA DE CLIC
salida = st_folium(m, width="100%", height=500)

lat_sel, lon_sel = None, None
if salida and salida["last_clicked"]:
    lat_sel = salida["last_clicked"]["lat"]
    lon_sel = salida["last_clicked"]["lng"]
    st.info(f"📍 Ubicación seleccionada. Completa el nombre para añadir el bar.")

# 6. FORMULARIO PARA GUARDAR EN GOOGLE SHEETS
st.divider()
with st.form("nuevo_bar", clear_on_submit=True):
    st.subheader("➕ Registrar nueva parada")
    
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del establecimiento")
        marca = st.text_input("Marca de Sidra")
    
    with col2:
        formato = st.radio(
            "¿Cómo la sirven?",
            ["Se puede pedir por Vasos (Pote)", "Solo venden la Botella entera"]
        )
    
    observaciones = st.text_area("Notas (Pinchos, trato, etc.)")
    
    if st.form_submit_button("Guardar en la Ruta"):
        if nombre and lat_sel:
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre,
                "LAT": float(lat_sel),
                "LON": float(lon_sel),
                "Marca": marca,
                "Formato": formato,
                "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                "Observaciones": observaciones
            }])
            
            # Unimos con los datos del Excel y subimos
            df_act = pd.concat([df_raw, nueva_fila], ignore_index=True)
            conn.update(data=df_act)
            
            st.balloons()
            st.success(f"✅ {nombre} guardado correctamente.")
            st.rerun()
        else:
            st.warning("⚠️ Toca primero el punto exacto en el mapa y pon el nombre del bar.")

# 7. TABLA PARA VERLO TODO
with st.expander("Ver lista completa de bares"):
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Observaciones']], use_container_width=True)
