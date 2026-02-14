import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# Estilo de botones estable
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #2e7d32; color: white; border-radius: 12px;
        height: 3.5em; width: 100%; font-weight: bold; border: none;
    }
    .stButton button[kind="primary"] {
        background-color: #d35400 !important;
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
    st.subheader("Listado de la Ruta")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.markdown("#### 🎯 Paso 1: Mueve el mapa hasta el centro")
        
        # Creamos el mapa centrado en Barakaldo
        # IMPORTANTE: Capturamos el centro actual para dibujar el visor
        pos_inicial = [43.2960, -2.9975]
        
        m_sel = folium.Map(location=pos_inicial, zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)

        # Técnica: Añadimos un marcador que simule un "visor" o "punto de mira"
        # Este marcador NO SE MUEVE porque lo forzamos al centro que devuelve el componente
        salida_sel = st_folium(m_sel, width="100%", height=450, key="mapa_visor")
        
        if salida_sel and salida_sel.get("center"):
            lat = salida_sel["center"]["lat"]
            lng = salida_sel["center"]["lng"]
            
            # Mostramos un mensaje de guía muy claro
            st.success(f"📍 Estás apuntando a: {lat:.5f}, {lng:.5f}")
            st.info("💡 El punto de registro es exactamente el centro del recuadro del mapa.")
            
            if st.button("🎯 SELECCIONAR ESTE BAR", type="primary"):
                st.session_state.temp_coords = (lat, lng)
                st.rerun()
        else:
            st.warning("Desliza un poco el mapa para activar el visor de coordenadas.")

    else:
        # PANTALLA FORMULARIO (Se mantiene igual, que es estable)
        st.subheader("📝 Paso 2: Datos del Bar")
        with st.form("registro"):
            nombre = st.text_input("Nombre del Bar")
            marca = st.text_input("Marca de Sidra")
            formato = st.radio("Formato", ["Vaso (Pote)", "Botella entera"])
            obs = st.text_area("Notas")
            if st.form_submit_button("✅ Guardar en la Ruta"):
                if nombre:
                    nueva_fila = pd.DataFrame([{"Nombre": nombre, "LAT": st.session_state.temp_coords[0], "LON": st.session_state.temp_coords[1], "Marca": marca, "Formato": formato, "Fecha_registro": datetime.now().strftime("%d/%m/%Y"), "Observaciones": obs}])
                    conn.update(data=pd.concat([df_raw, nueva_fila], ignore_index=True))
                    st.session_state.temp_coords = None
                    st.balloons()
                    st.rerun()
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
