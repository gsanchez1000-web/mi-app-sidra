import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Ruta Sidrera", layout="wide", page_icon="🍎")

# CSS para fijar la chincheta en el centro del mapa y estilo de botones
st.markdown("""
    <style>
    /* Estilo del contenedor del mapa para posicionar la chincheta encima */
    .map-container {
        position: relative;
        width: 100%;
    }
    .chincheta-centro {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -100%);
        z-index: 1000;
        pointer-events: none; /* Para que no interfiera con el toque del mapa */
        font-size: 40px;
    }
    div.stButton > button {
        background-color: #2e7d32; color: white; border-radius: 10px;
        height: 3.5em; width: 100%; font-weight: bold; border: none;
    }
    .stButton button[kind="primary"] {
        background-color: #d35400 !important;
        font-size: 1.2em;
    }
    </style>
""", unsafe_allow_html=True)

# 2. DATOS
conn = st.connection("gsheets", type=GSheetsConnection)
df_raw = conn.read(ttl="0")
df_mapa = df_raw.copy()
df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa['LON'] = pd.to_numeric(df_mapa['LON'].astype(str).str.replace(',', '.'), errors='coerce')
df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])

# 3. NAVEGACIÓN
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
        folium.Marker(
            [row['LAT'], row['LON']],
            popup=f"<b>{row['Nombre']}</b>",
            icon=folium.Icon(color=color, icon="glass-whiskey", prefix="fa")
        ).add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_ver")

elif menu == "📜 Listado":
    st.subheader("Listado de Bares")
    st.dataframe(df_mapa[['Nombre', 'Marca', 'Formato', 'Fecha_registro']], 
                 use_container_width=True, hide_index=True)

elif menu == "➕ Añadir Nuevo":
    if st.session_state.temp_coords is None:
        st.subheader("Mueve el mapa para situar la chincheta")
        
        # Contenedor con la chincheta visual
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        # Este es el icono de la chincheta que se verá en el centro
        st.markdown('<div class="chincheta-centro">📍</div>', unsafe_allow_html=True)
        
        m_sel = folium.Map(location=[43.2960, -2.9975], zoom_start=19, tiles=None)
        folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                         attr='Google', name='Satélite').add_to(m_sel)
        
        # Capturamos el movimiento del mapa
        salida_sel = st_folium(m_sel, width="100%", height=450, key="mapa_chincheta")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if salida_sel and salida_sel.get("center"):
            c_lat = salida_sel["center"]["lat"]
            c_lng = salida_sel["center"]["lng"]
            
            st.write(f"Coordenadas actuales: `{c_lat:.5f}, {c_lng:.5f}`")
            
            if st.button("🎯 Seleccionar Bar", type="primary"):
                st.session_state.temp_coords = (c_lat, c_lng)
                st.rerun()
    else:
        # FORMULARIO EN PANTALLA NUEVA
        st.subheader("📝 Datos del Nuevo Bar")
        with st.form("registro_final"):
            nombre = st.text_input("Nombre del Bar (si Google no lo da, escríbelo)")
            marca = st.text_input("Marca de Sidra")
            formato = st.radio("¿Cómo la sirven?", ["Vaso (Pote)", "Solo Botella entera"])
            obs = st.text_area("Observaciones")
            
            col_b1, col_b2 = st.columns(2)
            if col_b1.form_submit_button("✅ Registrar Bar"):
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
                    st.success("¡Registrado!")
                    st.rerun()
            
            if col_b2.form_submit_button("❌ Cancelar"):
                st.session_state.temp_coords = None
                st.rerun()
