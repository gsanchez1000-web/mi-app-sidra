import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN Y ESTILO SIDRERO
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

st.markdown("""
    <style>
    /* Estilo para los botones principales */
    div.stButton > button {
        background-color: #2e7d32; color: white; border-radius: 10px;
        height: 3em; width: 100%; font-weight: bold; border: none;
    }
    /* Estilo específico para Seleccionar Bar */
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

# 3. CONTROL DE NAVEGACIÓN
if 'temp_coords' not in st.session_state:
    st.session_state.temp_coords = None
if 'nombre_sugerido' not in st.session_state:
    st.session_state.nombre_sugerido = ""

menu = st.radio("Navegación", ["🗺️ Mapa", "📜 Listado", "➕ Añadir Nuevo"], 
                horizontal=True, label_visibility="collapsed")

# --- LÓGICA DE PANTALLAS ---

if menu == "🗺️ Mapa":
    st.subheader("Bares Registrados")
    m = folium.Map(location=[43.2960, -2.9975], zoom_start=18, tiles=None)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                     attr='Google', name='Satélite').add_to(m)
    
    for _, row in df_mapa.iterrows():
        color = "green" if "Botella" in str(row['Formato']) else "blue"
        folium.Marker(
            [row['LAT'], row['LON']],
            popup=f"<b>{row['Nombre']}</b>",
            icon=folium.Icon(color=color, icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_ver")

elif menu == "📜 Listado":
    st.subheader("Bares en la zona")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], 
                 use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.subheader("Paso 1: Posiciona el punto de mira")
        
        # Mapa de selección con punto de mira central
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        
        # Añadimos un marcador estético que simula el punto de mira
        # En Streamlit-folium, el centro del mapa se captura al moverlo
        salida_sel = st_folium(m_sel, width="100%", height=450, key="mapa_punto_mira")
        
        st.info("Mueve el mapa hasta que el bar quede en el centro. Al moverlo, verás las coordenadas abajo.")
        
        col_sel1, col_sel2 = st.columns([2, 1])
        
        if salida_sel and salida_sel.get("center"):
            centro_lat = salida_sel["center"]["lat"]
            centro_lon = salida_sel["center"]["lng"]
            
            with col_sel1:
                st.write(f"📍 Centro actual: `{centro_lat:.5f}, {centro_lon:.5f}`")
            
            with col_sel2:
                if st.button("🎯 Seleccionar Bar", type="primary"):
                    st.session_state.temp_coords = (centro_lat, centro_lon)
                    # Aquí es donde intentaríamos sacar el nombre de Google si tuviéramos API Key, 
                    # de momento lo dejamos listo para el formulario.
                    st.rerun()

    else:
        # PANTALLA DE FORMULARIO
        st.subheader("Paso 2: Completar datos")
        with st.form("registro_final"):
            nombre = st.text_input("Nombre del Bar", value=st.session_state.nombre_sugerido)
            marca = st.text_input("Marca de Sidra")
            formato = st.radio("¿Qué tienen?", ["Vaso (Pote)", "Botella entera"])
            obs = st.text_area("Notas")
            
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ Registrar Bar"):
                if nombre:
                    nueva_fila = pd.DataFrame([{
                        "Nombre": nombre,
                        "LAT": st.session_state.temp_coords[0],
                        "LON": st.session_state.temp_coords[1],
                        "Marca": marca, "Formato": formato,
                        "Fecha_registro": datetime.now().strftime("%d/%m/%Y"),
                        "Observaciones": obs
                    }])
                    df_final = pd.concat([df_raw, nueva_fila], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.temp_coords = None
                    st.balloons()
                    st.success("¡Guardado! Volviendo al inicio...")
                    st.rerun()
            
            if c2.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
