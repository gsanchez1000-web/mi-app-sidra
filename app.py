import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# CSS para centrar la chincheta de forma absoluta respecto al mapa
st.markdown("""
    <style>
    .map-container {
        position: relative;
        width: 100%;
        max-width: 800px; /* Ajustamos para que en móvil no se desparrame */
        margin: 0 auto;  /* Centra el contenedor en la pantalla */
    }
    .chincheta-fija {
        position: absolute;
        top: 50%;
        left: 50%;
        /* El secreto: -50% en ambos ejes para centro perfecto */
        /* Luego -100% en Y para que la punta sea la que marque el sitio */
        transform: translate(-50%, -100%); 
        z-index: 9999;
        pointer-events: none;
        font-size: 55px;
        filter: drop-shadow(2px 4px 3px rgba(0,0,0,0.4));
    }
    div.stButton > button {
        background-color: #2e7d32; color: white; border-radius: 12px;
        height: 3.5em; width: 100%; font-weight: bold; border: none;
    }
    .stButton button[kind="primary"] {
        background-color: #d35400 !important;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARGA DE DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")
df_mapa = df_raw.copy()
df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None

menu = st.radio("Navegación", ["🗺️ Mapa", "📜 Listado", "➕ Añadir Nuevo"], 
                horizontal=True, label_visibility="collapsed")

# --- PANTALLAS ---

if menu == "🗺️ Mapa":
    st.subheader("Bares Registrados")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=18, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                     attr='Google', name='Satélite').add_to(m)
    for _, row in df_mapa.iterrows():
        color = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker([row['LAT'], row['LON']], icon=folium.Icon(color=color, icon="glass-whiskey", prefix="fa")).add_to(m)
    st_folium(m, width="100%", height=500, key="ver_mapa")

elif menu == "📜 Listado":
    st.subheader("Listado de Bares")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.markdown("#### 📍 Paso 1: Sitúa el bar en el centro")
        
        # EL CONTENEDOR QUE LO CENTRA TODO
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        st.markdown('<div class="chincheta-fija">📍</div>', unsafe_allow_html=True)
        
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        
        salida_sel = st_folium(m_sel, width="100%", height=450, key="mapa_alta_final")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if salida_sel and salida_sel.get("center"):
            lat, lng = salida_sel["center"]["lat"], salida_sel["center"]["lng"]
            st.info(f"🎯 Apuntando a: {lat:.5f}, {lng:.5f}")
            if st.button("🎯 Seleccionar este Bar", type="primary"):
                st.session_state.temp_coords = (lat, lng)
                st.rerun()
    else:
        # PANTALLA FORMULARIO
        st.subheader("📝 Paso 2: Datos del Bar")
        with st.form("registro"):
            nombre = st.text_input("Nombre del Bar")
            marca = st.text_input("Marca de Sidra")
            formato = st.radio("Formato", ["Vaso (Pote)", "Botella entera"])
            obs = st.text_area("Observaciones")
            if st.form_submit_button("✅ Guardar Bar"):
                if nombre:
                    nueva_fila = pd.DataFrame([{"Nombre": nombre, "LAT": st.session_state.temp_coords[0], "LON": st.session_state.temp_coords[1], "Marca": marca, "Formato": formato, "Fecha_registro": datetime.now().strftime("%d/%m/%Y"), "Observaciones": obs}])
                    conn.update(data=pd.concat([df_raw, nueva_fila], ignore_index=True))
                    st.session_state.temp_coords = None
                    st.balloons()
                    st.rerun()
