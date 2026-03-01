import time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

from api_amadeus import get_flight_market_demand
from api_events_weather import get_real_events, get_real_weather
import export_utils

st.set_page_config(
    page_title="ORMpro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    * { transition: all 0.3s ease-in-out; }
    
    .stApp { 
        background-color: #0b0f19;
        background: radial-gradient(circle at 50% 30%, #1e1b4b 0%, #0b0f19 60%, #000000 100%);
        background-attachment: fixed;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }

    h1, h2, h3, p, span { color: #e2e8f0; font-family: 'Inter', sans-serif; }

    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937;
    }

    .css-1r6slb0, .css-12oz5g7, div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(10px);
    }

    [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; color: #D4AF37; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }

    hr { border-color: #1f2937; }
    
    /* Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-1 { animation: fadeInUp 0.5s ease-out 0.1s both; }
    .animate-2 { animation: fadeInUp 0.5s ease-out 0.2s both; }
    .animate-3 { animation: fadeInUp 0.5s ease-out 0.3s both; }
    .animate-4 { animation: fadeInUp 0.5s ease-out 0.4s both; }

    /* Button Styling overriding Streamlit defaults */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #4338ca 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(67, 56, 202, 0.4) !important;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: rgba(255, 255, 255, 0.5) !important;
        transform: translateY(-2px);
        background: rgba(255,255,255,0.02) !important;
        box-shadow: 0 10px 20px rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Input Styling */
    div[data-testid="stTextInput"] input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }
</style>
""", unsafe_allow_html=True)

try:
    import data_generator
except ImportError:
    st.error("⚠️ Fichier data_generator.py introuvable.")
    st.stop()

# ==========================================
# GESTION DES DONNÉES & ÉTAT
# ==========================================
if "current_data" not in st.session_state:
    st.session_state.current_data = None
    st.session_state.is_custom = False
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


@st.cache_data
def load_default_data():
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'hotel_market_data.csv')
    try:
        df = pd.read_csv(file_path, parse_dates=['Date'])
        if 'OTA_Price' not in df.columns or 'Search_Volume' not in df.columns:
            st.warning("Mise à jour des données (nouvelles métriques détectées)...")
            data_generator.generate_market_data()
            df = pd.read_csv(file_path, parse_dates=['Date'])
        return df
    except FileNotFoundError:
        st.warning("Données par défaut introuvables. Génération...")
        data_generator.generate_market_data()
        return pd.read_csv(file_path, parse_dates=['Date'])


if st.session_state.current_data is None:
    st.session_state.current_data = load_default_data()

# ==========================================
# PAGE ROUTING (Landing vs Dashboard)
# ==========================================


def render_landing_page():
    # Centered layout for the login/onboarding screen
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Section 1: Badge & Titles (Animate 1)
        st.markdown("""
        <div class="animate-1" style="text-align: center;">
            <span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; letter-spacing: 0.5px;">
                🔴 Version de Démonstration (SaaS Beta)
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h1 class='animate-1' style='text-align: center; color: #ffffff; font-size: 4rem; font-weight: 900; margin-top: 1.5rem; letter-spacing: -1px;'>ORMpro</h1>", unsafe_allow_html=True)
        st.markdown("<p class='animate-1' style='text-align: center; color: #94a3b8; font-size: 1.25rem; margin-bottom: 3rem;'>Le Système d'Intelligence Tarifaire & Prédictive Haute Performance.</p>", unsafe_allow_html=True)

        # Section 2: Main Connection Card (Animate 2)
        st.markdown("""
        <div class="animate-2" style='background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.08); padding: 40px; border-radius: 16px; backdrop-filter: blur(16px); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);'>
            <h3 style='margin-top: 0; color: white; text-align: center; font-size: 1.5rem;'>Connectez votre Établissement</h3>
            <p style='color: #cbd5e1; font-size: 0.95rem; text-align: center; margin-bottom: 30px;'>Générez votre jumeau numérique et analysez l'élasticité prix de votre marché en temps réel.</p>
        </div>
        """, unsafe_allow_html=True)

        # To keep Streamlit inputs perfectly aligned, we inject a negative margin spacer to bridge the HTML div above and Streamlit widgets below
        st.markdown("<div style='margin-top: -85px;' class='animate-2'></div>", unsafe_allow_html=True)
        
        url_input = st.text_input("Lien de l'établissement", placeholder="URL Booking.com, Expedia, ou ID Mews / Opera...", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            st.markdown("<div class='animate-3'>", unsafe_allow_html=True)
            connect_btn = st.button("Connecter et Analyser", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col_btn2:
            st.markdown("<div class='animate-3'>", unsafe_allow_html=True)
            demo_btn = st.button("Mode Démo (Simulé)", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Section 3: Logos / Trust Signals (Animate 4)
        st.markdown("""
        <div class="animate-4" style="text-align: center; margin-top: 3.5rem;">
            <p style="color: #64748b; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1.5rem;">Compatible avec vos systèmes 100% cloud</p>
            <div style="display: flex; justify-content: center; align-items: center; gap: 3rem; opacity: 0.5; filter: grayscale(100%);">
                <span style="font-size: 1.2rem; font-weight: 800; color: white;">Booking.com</span>
                <span style="font-size: 1.2rem; font-weight: 800; color: white; font-family: serif;">Expedia</span>
                <span style="font-size: 1.2rem; font-weight: 800; color: white;">MEWS</span>
                <span style="font-size: 1.2rem; font-weight: 800; color: white;">OPERA</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if connect_btn or demo_btn:
            if connect_btn and not url_input:
                st.error("Veuillez entrer une URL ou un ID valide.")
            else:
                if demo_btn:
                    st.session_state.landing_url = "Demo - Contact Hotel Le Provençal"
                else:
                    st.session_state.landing_url = url_input

                # FAKE LOADING SEQUENCE
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Step 1
                status_text.markdown("🔄 *Établissement d'une connexion sécurisée à l'API...*")
                time.sleep(1)
                progress_bar.progress(25)

                # Step 2
                status_text.markdown("📡 *Aspiration des tarifs historiques et futurs (Rate Shopping)...*")
                time.sleep(1.5)
                progress_bar.progress(50)

                # Step 3
                status_text.markdown("🔎 *Identification du pool concurrentiel (CompSet)...*")
                time.sleep(1)
                progress_bar.progress(75)

                # Step 4
                status_text.markdown("🧠 *Calcul vectoriel de l'élasticité prix par l'IA...*")
                time.sleep(1.5)
                progress_bar.progress(100)

                status_text.success("✅ **Connexion réussie.** Génération du Dashboard...")
                time.sleep(1)

                st.session_state.logged_in = True
                st.rerun()


def render_dashboard():
        # Main content area
        if "current_data" not in st.session_state:
            st.info("👋 Bienvenue sur ORMpro. Veuillez aller dans **Configuration** pour générer les données de votre marché.")
        else:
            df_raw = st.session_state.current_data  # Use df_raw here as it's the full dataset
            # Determine Macro City for APIs and Micro Market for UI labels
            current_city = st.session_state.get('custom_city', 'Paris')
            current_market = st.session_state.get('custom_market_name', current_city)

            # Global Date Filter (moved from sidebar)
            min_date = df_raw['Date'].min().date()
            max_date = df_raw['Date'].max().date()

        OUR_HOTEL_NAME = st.session_state.get('custom_hotel_name', "Mon Hôtel (Simulé)") if st.session_state.is_custom else "Contact Hotel Le Provençal Bordeaux Lac"

        if st.session_state.get("landing_url"):
            st.sidebar.success("🔗 Établissement Connecté (Sync Live)")

        # ==========================================
        # SIDEBAR NAVIGATION & GLOBAL FILTERS
        # ==========================================
        with st.sidebar:
            st.markdown(f"<h3 style='color:#D4AF37; margin-bottom:5px; text-align: center;'>⚡ RM OS PRO</h3><p style='font-size:0.8rem; color:#94a3b8; text-align: center;'>{OUR_HOTEL_NAME}</p>", unsafe_allow_html=True)
            st.markdown("---")

            st.markdown("""
            <style>
                div[data-testid="stRadio"] > div {
                    gap: 0.5rem;
                }
                div[data-testid="stRadio"] label {
                    background-color: transparent;
                    padding: 10px 15px;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                div[data-testid="stRadio"] label:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                }
                div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p {
                    font-size: 15px;
                    font-weight: 500;
                    margin: 0;
                    padding: 0;
                }
                /* Hide the radio circles */
                div[data-testid="stRadio"] span[data-baseweb="radio"] {
                    display: none;
                }
            </style>
            """, unsafe_allow_html=True)
            
            page = st.radio(
                "Navigation",
                options=[
                    "📈 Market Insight",
                    "⚖️ Rate & Parity Insight",
                    "🎯 Yield & Positioning",
                    "📊 STR Benchmark",
                    "🧠 RMS Forecasting",
                    "⭐ Reputation Intel",
                    "⚙️ Configuration"
                ],
                label_visibility="collapsed"
            )
            
            # Map the radio visual choices back to the original engine names
            page_mapping = {
                "📈 Market Insight": "Market Insight",
                "⚖️ Rate & Parity Insight": "Rate & Parity Insight",
                "🎯 Yield & Positioning": "Yield & Positioning",
                "📊 STR Benchmark": "STR Benchmark",
                "🧠 RMS Forecasting": "RMS Forecasting",
                "⭐ Reputation Intel": "Reputation Intel",
                "⚙️ Configuration": "Configuration"
            }
            page = page_mapping[page]

        with st.sidebar:
            st.markdown("---")
            st.markdown("<h4 style='font-size:1rem;'>🔍 Filtres Globaux</h4>", unsafe_allow_html=True)
                    
            if page != "Configuration":
                # min_date and max_date are now defined globally
                real_today = datetime.now().date()
                # Safe start date logic so the df isn't completely empty if the generated data is outdated
                safe_today = min(real_today, max_date - timedelta(days=30))
                
                # Le filtre de date dépend du module
                if page == "STR Benchmark":
                    filter_title = "Période Analysée (Passé)"
                    start_dt = min_date
                    end_dt = safe_today
                else:
                    filter_title = "Horizon de Prévision (Futur)"
                    start_dt = safe_today
                    end_dt = max_date
                    
                date_val = st.date_input(filter_title, [start_dt, end_dt])
                if isinstance(date_val, tuple) and len(date_val) == 2:
                    start_dt, end_dt = date_val
                elif isinstance(date_val, tuple) and len(date_val) == 1:
                    start_dt = date_val[0]
                    end_dt = date_val[0]
                else:
                    start_dt = date_val
                    end_dt = date_val

        # ==========================================
        # DATA PROCESSING
        # ==========================================
        if page != "Configuration":
            mask_date = (df_raw['Date'] >= pd.to_datetime(start_dt)) & (df_raw['Date'] <= pd.to_datetime(end_dt))
            df = df_raw.loc[mask_date]
            
            # Séparation de NOS données (Base 100) vs Marché
            df_our = df[~df['Is_Compset']].copy()
            
            if df_our.empty:
                st.warning("⚠️ Aucune donnée disponible pour cette plage de dates.")
                st.stop()
                
            competitors = df_raw[df_raw['Is_Compset'] == True]['Hotel'].unique()
            with st.sidebar:
                selected_comps = st.multiselect("Set Concurrentiel (CompSet)", competitors, default=competitors)
            
            df_comp = df[(df['Hotel'].isin(selected_comps)) & (df['Is_Compset'] == True)]
            
            if not df_comp.empty:
                df_market_avg = df_comp.groupby('Date')['Price'].mean().reset_index()
                df_market_avg.rename(columns={'Price': 'Total_Market_Avg'}, inplace=True)
                df_our = pd.merge(df_our, df_market_avg, on='Date', how='left')
            else:
                df_our['Total_Market_Avg'] = df_our['Price']
    
        # ==========================================
        # ROUTING MAIN CONTENT
        # ==========================================
        
        if "current_data" in st.session_state and page != "Configuration":
            if page == "Market Insight":
                st.title("📈 Market Insight (Predictive Demand)")
                st.markdown(f"Analyse des volumes de recherche de vols/hôtels et de la pression de la demande sur votre marché cible (**{current_market}**).")
                st.info("💡 **Pourquoi le Market Insight ?** C'est l'indicateur avancé par excellence. Avant même de recevoir des réservations, vous observez l'intention d'achat (Vols vers votre ville, recherches d'hôtels). Si l'indice monte fortement sur une date future, il faut augmenter vos prix *avant* que votre hôtel ne se remplisse trop vite à bas prix.")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_our['Date'], y=df_our['Search_Volume'],
                    fill='tozeroy',
                    mode='lines',
                    name='Indice de Recherche (Vols/Hôtels)',
                    line=dict(color='#38bdf8', width=2),
                    fillcolor='rgba(56, 189, 248, 0.2)'
                ))
                
                # Initialize pagination state for 3-month views
                if "market_viz_start_date" not in st.session_state:
                    st.session_state.market_viz_start_date = df_our['Date'].min()
                else:
                    # Sanity check: Ensure the saved start date is within the currently filtered df_our['Date'] bounds
                    if pd.to_datetime(st.session_state.market_viz_start_date) < df_our['Date'].min() or pd.to_datetime(st.session_state.market_viz_start_date) > df_our['Date'].max():
                        st.session_state.market_viz_start_date = df_our['Date'].min()

                # Pagination controls above the graph
                col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
                with col_nav1:
                    if st.button("⬅️ 3 Mois Précédents", use_container_width=True):
                        st.session_state.market_viz_start_date = max(df_our['Date'].min(), st.session_state.market_viz_start_date - timedelta(days=90))
                with col_nav3:
                    if st.button("3 Mois Suivants ➡️", use_container_width=True):
                        st.session_state.market_viz_start_date = min(df_our['Date'].max() - timedelta(days=90), st.session_state.market_viz_start_date + timedelta(days=90))
                        
                # Add real events from PredictHQ or Generator
                mask_events = df_our['Event'].notna() & (df_our['Event'] != "") & (df_our['Event'].str.lower() != "non")
                event_dates = df_our[mask_events]['Date'].tolist()
                event_titles = df_our[mask_events]['Event'].tolist()
                
                if event_dates:
                    for edate, etitle in zip(event_dates, event_titles):
                        # Vertical dotted line for the event
                        fig.add_vline(x=edate, line_width=1, line_dash="dash", line_color="#ef4444")
                        # Text annotation rotated to avoid overlap
                        fig.add_annotation(
                            x=edate, y=df_our['Search_Volume'].max() * 0.95,
                            text=f"🚩 {etitle}", showarrow=False,
                            textangle=-90, font=dict(color="#ef4444", size=11, family="Inter"),
                            xanchor="right", yanchor="top"
                        )
                    st.success(f"📡 Radar Connecté : {len(event_dates)} événements réels majeurs détectés à {current_market} via PredictHQ.")
                else:
                    st.info("ℹ️ Aucun événement marquant détecté par l'API pour cette période.")
                
                # Apply the current 3-month window to the graph
                current_view_start = pd.to_datetime(st.session_state.market_viz_start_date)
                current_view_end = current_view_start + timedelta(days=90)
                
                fig.update_layout(
                    height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(title="Volume de Recherche"), 
                    xaxis=dict(
                        range=[current_view_start, current_view_end],
                        type="date"
                    ),
                    margin=dict(t=10, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
            
                st.markdown("---")
                st.markdown(f"### 🎯 Radar Connecté : Événements à {current_market}")
                st.markdown("Flux en temps réel de l'API PredictHQ. Détection automatique des générateurs de demande locaux.")
                st.markdown("### ✈️ Signal de Demande Avancé (Live Amadeus GDS)")
                st.markdown("Interrogation en temps réel de l'API Amadeus pour détecter la compression du marché aérien vers votre ville.")
                
                with st.expander("🔍 Lancer un Scan Radar Aérien", expanded=True):
                    colA, colB, colC, colD = st.columns([1, 1, 1, 1])
                    
                    # Airport code mapping for the simulated cities
                    city_to_airport = {
                        "Paris": "PAR",
                        "Marseille": "MRS",
                        "Lyon": "LYS",
                        "Bordeaux": "BOD",
                        "Nice": "NCE"
                    }
                    
                    # Get current hotel city from custom session or default to Paris
                    dest_default = city_to_airport.get(current_city, "PAR")
                    
                    with colA:
                        flight_origin = st.selectbox("Origine (Code IATA)", ["PAR", "LON", "NYC", "DBX", "FRA"], index=0)
                    with colB:
                        flight_dest = st.text_input("Destination (Code IATA)", value=dest_default)
                    with colC:
                        flight_date = st.date_input("Date du Vol", datetime.now().date() + timedelta(days=14))
                    with colD:
                        st.markdown("<br>", unsafe_allow_html=True)
                        scan_btn = st.button("Scanner les Vols 🛫", type="primary", use_container_width=True)
                        
                    if scan_btn:
                        result = get_flight_market_demand(flight_origin, flight_dest, flight_date.strftime('%Y-%m-%d'))
                        
                        if result.get("status") == "success":
                            st.success("✅ Connexion API Amadeus Établie")
                            rm1, rm2, rm3 = st.columns(3)
                            
                            if result["offers_count"] > 0:
                                rm1.metric("Vols Disponibles", result["offers_count"], help="Moins il y a de vols, plus la compression (demande) est forte.")
                                rm2.metric("Prix Moyen Aérien", f"{result['avg_price']} {result['currency']}", help="Indicateur de la 'Willingness to Pay' des voyageurs sur cette date.")
                                rm3.metric("Prix Minimum", f"{result['min_price']} {result['currency']}")
                                
                                if result['avg_price'] > 150: # Arbitrary high price logic for demo
                                    st.warning("⚠️ **Alerte RMS** : Forte tension sur les prix aériens. Recommandation d'augmenter vos tarifs hôteliers pour cette date (Prix inélastique).")
                                else:
                                    st.info("ℹ️ **RMS Normal** : Pression aérienne standard. Maintenez la stratégie de Pace actuelle.")
                            else:
                                st.warning("Aucun vol trouvé ou liaison fermée pour cette date exacte.")
                        else:
                            st.error(f"❌ Erreur API : {result.get('message')}")
        
            elif page == "Rate & Parity Insight":
                st.title("⚖️ Rate & Parity Insight")
                st.markdown("Détection des disparités tarifaires (OTAs type Booking/Expedia vendant moins cher que votre site direct).")
                
                kpi1, kpi2, kpi3 = st.columns(3)
                parity_issues = df_our[df_our['OTA_Price'] < df_our['Price']]
                loss_est = ((df_our['Price'] - df_our['OTA_Price']) * df_our['Rooms_Sold'])[df_our['OTA_Price'] < df_our['Price']].sum()
                
                kpi1.metric("Jours avec Fuite de Parité", f"{len(parity_issues)} j", help="Nombre de jours où un distributeur casse vos prix.")
                kpi2.metric("Perte de Marge Estimée (Booking)", f"- {loss_est:,.0f} €", help="Perte sèche car le client réserve sur l'OTA moins cher au lieu de votre site direct.")
                kpi3.metric("Statut Parité Global", "⚠️ Risque" if len(parity_issues) > 5 else "✅ Sécurisé", help="Si vous avez trop de disparités, les OTAs vous pénalisent dans leur algorithme de visibilité.")
                
                st.info("💡 **Pourquoi la parité est vitale ?** Si Booking propose la chambre à 100€ et votre site web à 110€, 100% des clients réserveront sur Booking. Vous perdez non seulement 10€, mais vous payez en plus 18% de commission à Booking. La règle d'or du RM est d'avoir le prix direct toujours égal ou inférieur aux OTAs.")
            
                st.markdown("### Évolution Direct Web vs OTA")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_our['Date'], y=df_our['Price'],
                    mode='lines', name='Prix Direct Web (B2C)',
                    line=dict(color='#D4AF37', width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=df_our['Date'], y=df_our['OTA_Price'],
                    mode='lines', name='Prix OTA (Booking)',
                    line=dict(color='#ef4444', width=2, dash='dot')
                ))
                
                fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10))
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                st.warning("📊 **Actionabilité** : Si la courbe rouge passe en dessous de la courbe or, vous perdez des ventes directes ! Baissez immédiatement votre prix direct ou fermez la disponibilité sur cet OTA pour ces dates précises.")
            
            elif page == "Yield & Positioning":
                st.title("🎯 Yield & Positioning (CompSet View)")
                st.markdown("Où se situe votre hôtel par rapport à la moyenne du marché en termes de prix ? Êtes-vous le choix de la raison ou du luxe ?")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Votre ADR Moyen (Simulé)", f"{df_our['Price'].mean():.0f} €", help="Votre prix moyen sur la période.")
                col2.metric("Moyenne Marché concurrentiel", f"{df_our['Total_Market_Avg'].mean():.0f} €", help="Le prix de la chambre de vos 5-10 voisins.")
                
                st.markdown("### Comparatif Tarifaire")
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_our['Date'], y=df_our['Price'], mode='lines', name='Notre Hôtel', line=dict(color='#D4AF37', width=3)))
                fig2.add_trace(go.Scatter(x=df_our['Date'], y=df_our['Total_Market_Avg'], mode='lines', name='Moyenne CompSet', line=dict(color='#94a3b8', width=2, dash='dash')))
                fig2.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10))
                st.plotly_chart(fig2, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 🎛️ Simulateur d'Élasticité Prix (Yield)")
                st.markdown("Testez l'impact d'un changement de prix sur votre remplissage et votre revenu.")
                
                col_sim1, col_sim2 = st.columns(2)
                price_change_pct = col_sim1.slider("Ajustement Tarifaire Suggéré (%)", min_value=-30, max_value=30, value=0, step=5, help="Si je baisse/augmente mes prix de X%...")
                
                # Simulation basique d'élasticité (très simplifiée pour l'UI)
                elasticity_factor = -1.5 # Une hausse de 10% fait baisser l'occ de 15%
                avg_price = df_our['Price'].mean()
                avg_occ = df_our['Occupancy_Rate'].mean() * 100
                
                sim_price = avg_price * (1 + price_change_pct/100)
                sim_occ = max(0, min(100, avg_occ * (1 + (price_change_pct/100 * elasticity_factor))))
                
                sim_rev = sim_price * (sim_occ/100) * 50 * 30 # Rev pour un hotel de 50 ch sur 30j
                base_rev = avg_price * (avg_occ/100) * 50 * 30
                rev_delta = sim_rev - base_rev
                
                with col_sim2:
                    st.markdown(f"**Projections avec action tarifaire de {price_change_pct:+}% :**")
                    mk1, mk2, mk3 = st.columns(3)
                    mk1.metric("Nouvel ADR", f"{sim_price:.0f} €", f"{sim_price - avg_price:+.0f} €")
                    mk2.metric("Nouvelle Occ.", f"{sim_occ:.0f}%", f"{sim_occ - avg_occ:+.0f}%")
                    
                    rev_color = "normal" if rev_delta >= 0 else "inverse"
                    mk3.metric("Revenu Total Projeté (30j)", f"{sim_rev:,.0f} €", f"{rev_delta:+,.0f} €", delta_color=rev_color)
                    
                if price_change_pct < 0 and rev_delta > 0:
                    st.success("✅ **Stratégie Valide :** La baisse de prix est compensée par un fort gain en volume. Le revenu total augmente.")
                elif price_change_pct > 0 and rev_delta > 0:
                    st.success("✅ **Stratégie Valide :** La hausse de prix cause une légère perte de volume, mais le gain unitaire (ADR) compense largement.")
                elif price_change_pct != 0 and rev_delta < 0:
                    st.error("❌ **Stratégie Destructrice :** Cet ajustement détruit du revenu. L'élasticité n'est pas favorable à cette action.")
                    
            elif page == "STR Benchmark":
                st.title("📉 STR Benchmark (Rétrospective)")
                st.markdown("Comparaison de vos performances passées (Parts de marché) par rapport au pool concurrentiel.")
                
                avg_occ = df_our['Occupancy_Rate'].mean() * 100
                avg_adr = df_our['Price'].mean()
                avg_revpar = df_our['RevPAR'].mean()
                market_adr = df_our['Total_Market_Avg'].mean()
                
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                kpi1.metric("Occupancy", f"{avg_occ:.1f}%", help="Taux d'occupation moyen sur la période.")
                kpi2.metric("ADR Global", f"{avg_adr:.2f} €", f"{(avg_adr/market_adr - 1)*100:.1f}% vs Marché", help="Average Daily Rate. Affiché en vert si vous vendez plus cher que le marché.")
                kpi3.metric("RevPAR", f"{avg_revpar:.2f} €", help="Revenue Per Available Room (ADR x Occupancy). Le KPI roi de l'hôtellerie.")
                
                ari = (avg_adr / market_adr) * 100 if market_adr > 0 else 100
                kpi4.metric("ARI (Average Rate Index)", f"{ari:.1f}", "Base 100 = Fair Share", help="Indice de Pénétration Prix. Un ARI de 110 signifie que vous captez 10% de prix pur en plus que votre part loyale.")
                
                st.info("💡 **Le Rapport STR (Smith Travel Research)** est l'étalon-or mondial. Il ne vous dit pas *combien* vous gagnez, il vous dit *si vous gagnez face aux autres*. Si le marché entier baisse de -10% mais que vous ne baissez que de -5%, votre performance relative (Index) est positive, c'est une victoire RM.")
                
                st.markdown("### Performances Comparées")
                fig_str = px.area(df_our, x="Date", y=["Price", "Total_Market_Avg"], 
                              labels={"value": "ADR (€)", "variable": "Légende"},
                              color_discrete_sequence=['#D4AF37', '#475569'])
                fig_str.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10))
                st.plotly_chart(fig_str, use_container_width=True)
                
            elif page == "RMS Forecasting":
                st.title("🧠 RMS AI Forecasting")
                st.markdown(f"Calcul mathématique du mix Prix/Occupation optimal (Booking Curve) pour **{current_market}**.")
                
                st.info("💡 **Comment raisonne l'Algorithme ?** Le système analyse le *Pace* (vitesse de remplissage). Si vous êtes rempli à 70% pour une date dans 2 mois, la demande est anormalement forte : l'algorithme recommande une forte hausse (+15%). À l'inverse, une date proche vide déclenche une recommandation de promotion (-10%) pour stimuler le volume (pickup).")
            
                # Live Weather Context for Last Minute Pickup
                weather_forecast = get_real_weather(current_city)
                
                if weather_forecast:
                    st.markdown("### 🌤️ Contexte Météo (Impact Pickup Dernière Minute)")
                    st.markdown(f"Prévisions à 5 jours pour **{current_market}** (OpenWeatherMap API). *Une belle météo sur le week-end augmente la probabilité de réservation 'Last Minute' de 15% à 25%.*")
                    
                    w_cols = st.columns(len(weather_forecast))
                    for i, (date, w_data) in enumerate(weather_forecast.items()):
                        with w_cols[i]:
                            st.markdown(f"**{date[5:]}**") # Show MM-DD
                            st.image(f"http://openweathermap.org/img/wn/{w_data['icon']}@2x.png", width=50)
                            st.markdown(f"{w_data['temp']}°C")
                            st.caption(w_data['description'])
                    st.markdown("---")
            
                # Inject real events into dataframe for visualization
                today_str = datetime.now().strftime('%Y-%m-%d')
                next_month_str = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                live_events = get_real_events(current_city, today_str, next_month_str)
                
                if live_events:
                    for e in live_events:
                        # Map the real event title to the dataframe's Event column for that date
                        df_our.loc[df_our['Date'] == e['date'], 'Event'] = f"{e['title']} (API)"
            
                # Advanced AI Algorithm Logic (Velocity + Elasticity)
                df_our['Recommendation'] = "Maintenir"
                df_our['Prix_Suggere'] = df_our['Price']
                df_our['Decision_Logic'] = "Marché Stable"
                
                for idx, row in df_our.iterrows():
                    occ = row.get('Occupancy_Rate', 0)
                    pace = row.get('Pace_Velocity_Pct', 0)
                    elast = row.get('Price_Elasticity', -1.0)
                    wtp = row.get('Willingness_To_Pay', row['Price'])
                    
                    # 1. Forte Vélocité et Inélasticité (Augmentation Forte)
                    if pace > 2 and elast > -1.5:
                        df_our.at[idx, 'Recommendation'] = "↗️ Augmenter (+15%)"
                        df_our.at[idx, 'Prix_Suggere'] = min(row['Price'] * 1.15, wtp)
                        df_our.at[idx, 'Decision_Logic'] = "Forte Vélocité + Inélastique (WTP Élevé)"
                        
                    # 2. Remplissage haut et Pace positif (Augmentation Modérée)
                    elif occ > 0.50 and pace > -2:
                        df_our.at[idx, 'Recommendation'] = "↗️ Augmenter (+5%)"
                        df_our.at[idx, 'Prix_Suggere'] = min(row['Price'] * 1.05, wtp)
                        df_our.at[idx, 'Decision_Logic'] = "Compression Stock + Pace Positif"
                        
                    # 3. Retard de Pace et Forte Élasticité (Promotion requise)
                    elif pace < 0 and elast < -0.8 and occ < 0.60:
                        df_our.at[idx, 'Recommendation'] = "↘️ Baisser (-10%)"
                        df_our.at[idx, 'Prix_Suggere'] = row['Price'] * 0.90
                        df_our.at[idx, 'Decision_Logic'] = "Retard Pace + Forte Sensibilité Prix"
                        
                urgent = df_our[df_our['Recommendation'] != "Maintenir"]
                st.warning(f"🔔 {len(urgent)} dates nécessitent un ajustement tarifaire basé sur l'élasticité et le Pace Velocity.")
                
                # Selecting the relevant columns to show advanced AI logic
                cols_to_show = ['Date', 'Event', 'Occupancy_Rate', 'Pace_Velocity_Pct', 'Price_Elasticity', 'Price', 'Prix_Suggere', 'Decision_Logic']
                # Check if we have the new columns before displaying (for safe fallback during live dev)
                valid_cols = [c for c in cols_to_show if c in urgent.columns]
                
                st.dataframe(
                    urgent[valid_cols].style.background_gradient(cmap='Blues', subset=['Pace_Velocity_Pct'] if 'Pace_Velocity_Pct' in valid_cols else []).format({"Occupancy_Rate": "{:.0%}"}),
                    use_container_width=True, height=250
                )
                
                # Boutons d'exportation (Automated Strategy Report)
                st.markdown("#### 📥 Exporter le Rapport Matinal")
                col_dl1, col_dl2, _ = st.columns([1, 1, 2])
                with col_dl1:
                    try:
                        excel_data = export_utils.generate_excel_report(urgent[valid_cols], current_city)
                        st.download_button(
                            label="📊 Télécharger Excel",
                            data=excel_data,
                            file_name=f"Strat_Report_{current_city}_{today_str}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Excel export failed {e}")
                with col_dl2:
                    try:
                        pdf_data = export_utils.generate_pdf_report(urgent[valid_cols], current_city)
                        st.download_button(
                            label="📄 Télécharger PDF",
                            data=pdf_data,
                            file_name=f"Strat_Report_{current_city}_{today_str}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur génération PDF : veuillez vérifier les dépendances fpdf. ({e})")
                        
                st.markdown("### Booking Demand Chart (Heatmap)")
                # Remplacement du Scatter3D difficile à lire par un Graphique Combiné très visuel (Barres de Pace + Ligne de Prix)
                fig_combo = go.Figure()
                fig_combo.add_trace(go.Bar(
                    x=df_our['Date'], y=df_our['Occupancy_Rate']*100, 
                    name="Occupation (%)", marker_color='rgba(56, 189, 248, 0.4)',
                    yaxis="y1"
                ))
                fig_combo.add_trace(go.Scatter(
                    x=df_our['Date'], y=df_our['Price'],
                    name="Prix Analysé (€)", line=dict(color='#D4AF37', width=3),
                    yaxis="y2"
                ))
                # Ajout de la suggestion de l'algorithme uniquement quand il y a changement
                changes = df_our[df_our['Recommendation'] != "Maintenir"]
                fig_combo.add_trace(go.Scatter(
                    x=changes['Date'], y=changes['Prix_Suggere'],
                    name="Cible IA (€)", line=dict(color='#ef4444', width=2, dash='dot'),
                    mode="lines+markers",
                    yaxis="y2"
                ))
                
                fig_combo.update_layout(
                    title="Relation Occupation vs Élasticité Prix",
                    yaxis=dict(title="Occupation (%)", range=[0, 100]),
                    yaxis2=dict(title="Prix (€)", overlaying="y", side="right"),
                height=500, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_combo, use_container_width=True)

            elif page == "Reputation Intel":
                st.title("⭐ Reputation Intel (Sentiments & Avis)")
                st.markdown("Analyse sémantique des retours clients pour anticiper l'impact sur votre *Pricing Power*.")
                
                st.info("💡 **Impact RM :** Un hôtel perçu comme un '4 étoiles' par ses clients peut vendre plus cher qu'un hôtel 4 étoiles officiel mal noté. L'algorithme lit les avis en temps réel et ajuste l'élasticité prix. Si votre e-réputation grimpe, votre prix plafond grimpe aussi.")
                
                # Simulated fake data for Reputation
                st.markdown("### 📊 Synthèse Globale (30 Derniers Jours)")
                col_rep1, col_rep2, col_rep3 = st.columns(3)
                col_rep1.metric("Score Global (TrustYou Eq.)", "8.9 / 10", "+0.2 vs M-1")
                col_rep2.metric("Volume d'Avis Analysés", "142", "+15 avis")
                col_rep3.metric("Impact Pricing Power", "+ 3.5% premium", "Capacité à vendre plus cher", delta_color="normal")
                
                st.markdown("---")
                
                # Dynamic Sentiment Chart
                st.markdown("### 📈 Évolution du Sentiment Client")
                fig_rep = go.Figure()
                fig_rep.add_trace(go.Scatter(
                    x=df_our['Date'], y=df_our['Review_Score'],
                    mode='lines',
                    name='Trust Score',
                    line=dict(color='#a855f7', width=3, shape='spline'), # Purple curve
                    fill='tozeroy',
                    fillcolor='rgba(168, 85, 247, 0.15)'
                ))
                fig_rep.update_layout(
                    height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(title="Score / 10", range=[max(0, df_our['Review_Score'].min() - 1), 10]),
                    margin=dict(t=10, b=10)
                )
                st.plotly_chart(fig_rep, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 🗣️ Analyse Sémantique (Points de Friction / Valorisation)")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.success("✅ **Top 3 Thèmes Positifs (À mettre en avant)**")
                    st.markdown("- **Localisation** (Marseille Vieux-Port) : 92% positifs\n- **Propreté** : 88% positifs\n- **Literie** : 85% positifs")
                with c2:
                    st.error("❌ **Top 3 Thèmes Négatifs (Freins à la conversion)**")
                    st.markdown("- **Petit-déjeuner** : -12% sentiment ce mois-ci\n- **Wifi** (3ème étage) : signalements fréquents\n- **Bruit** (côté rue) : récurrent le week-end")

        elif page == "Configuration":
            st.markdown("<br>", unsafe_allow_html=True)
            st.title("⚙️ Configuration du Marché")
            st.markdown("Personnalisez les paramètres de votre hôtel et de votre demande locale pour ajuster l'algorithme de tarification dynamique.")
            st.markdown("---")
            
            neighborhoods = {
                "Paris": ["Tous", "8ème (Champs-Élysées)", "1er (Louvre)", "11ème (Bastille)", "Montmartre", "15ème (Tour Eiffel)"],
                "Lyon": ["Tous", "Presqu'île", "Vieux Lyon", "Part-Dieu", "Confluence"],
                "Marseille": ["Tous", "Vieux-Port", "Prado-Périer", "Euroméditerranée", "Le Panier"],
                "Bordeaux": ["Tous", "Chartrons", "Centre-Ville", "Saint-Jean (Gare)", "Bastide"],
                "Nice": ["Tous", "Promenade des Anglais", "Vieux-Nice", "Cimiez", "Port Lympia"]
            }
            
            with st.container():
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    custom_name = st.text_input("Nom de l'établissement", value="Grand Hotel Alpha")
                    custom_city = st.selectbox("Ville (Macro-Marché)", list(neighborhoods.keys()))
                    
                    # Safe fallback if custom_city resets during Streamlit render cycles
                    safe_city = custom_city if custom_city in neighborhoods else "Paris"
                    custom_neighborhood = st.selectbox("Quartier (Micro-Marché CompSet)", neighborhoods[safe_city])
                    
                    # Combine city and neighborhood for the generator if a specific one is chosen
                    final_market_name = custom_city if custom_neighborhood == "Tous" else f"{custom_city} - {custom_neighborhood}"
                    
                with sc2:
                    custom_stars = st.slider("Catégorie (Étoiles)", 1, 5, 4)
                    custom_rooms = st.number_input("Capacité (Chambres)", min_value=10, max_value=500, value=120)
                with sc3:
                    custom_base_price = st.number_input("Tarif Plancher / ADR Moyen (€)", min_value=40, max_value=800, value=180)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Lancer la Modélisation Experte 🚀", type="primary", use_container_width=True):
                    with st.spinner(f"Génération du jumeau numérique et scan du micro-marché {final_market_name}..."):
                        new_df = data_generator.generate_custom_data(
                            hotel_name=custom_name,
                            stars=custom_stars,
                            total_rooms=custom_rooms,
                            base_price=custom_base_price,
                            city=final_market_name
                        )
                        new_df['Date'] = pd.to_datetime(new_df['Date']) # FIX: Ensure DateTime
                        st.session_state.current_data = new_df
                        st.session_state.is_custom = True
                        
                        # Update global sessions with the macro city (for APIs) and macro+micro name for labels
                        st.session_state.custom_city = custom_city # APIs need standard 'Paris', not 'Paris - 8eme'
                        st.session_state.custom_market_name = final_market_name
                        st.session_state.custom_hotel = custom_name
                        
                        st.success("Configuration experte appliquée avec succès ! ✅")
                        st.rerun()
        
                st.markdown("---")
                st.markdown("#### Mode Administrateur")
                if st.button("🔄 Réinitialiser les données (Défaut)"):
                    st.session_state.current_data = load_default_data()
                    st.session_state.is_custom = False
                    st.session_state.pop('custom_city', None)
                    st.session_state.pop('custom_market_name', None)
                    st.session_state.pop('custom_hotel', None)
                    st.success("Données réinitialisées vers la simulation par défaut.")
                    st.rerun()
                    
# ==========================================
# APP EXECUTION ENTRY POINT
# ==========================================
if not st.session_state.logged_in:
    render_landing_page()
else:
    render_dashboard()
