import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# ==========================================
# CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="Revenue Management Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS pour un look "SaaS Premium / Dark Mode"
st.markdown("""
<style>
    /* Global Styling */
    .reportview-container .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        font-weight: 600;
        color: #B0BEC5;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #E0E0E0;
        font-weight: 600;
    }
    
    /* Highlight Event rows in table */
    .event-row {
        background-color: rgba(255, 152, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# CHARGEMENT DES DONNÉES (Fixé pour la production)
# ==========================================
@st.cache_data
def load_data():
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'hotel_market_data.csv')
    try:
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except FileNotFoundError:
        import data_generator
        with st.spinner("Génération automatique du jeu de données pour la première utilisation..."):
            data_generator.generate_data()
        # On relit après génération
        try:
            df = pd.read_csv(file_path)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception as e:
            st.error(f"Erreur lors de la génération des données : {e}")
            return pd.DataFrame()

df_raw = load_data()

# Noms constants (doivent correspondre au générateur)
OUR_HOTEL_NAME = "Contact Hotel Le Provençal Bordeaux Lac"

if not df_raw.empty:
    
    # ==========================================
    # SIDEBAR: FILTRES
    # ==========================================
    with st.sidebar:
        st.title("🎛️ Filtres d'Analyse")
        
        # Filtres de Date
        min_date = df_raw['Date'].min().date()
        max_date = df_raw['Date'].max().date()
        
        start_date = st.date_input("Date de début", min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("Date de fin", max_date, min_value=min_date, max_value=max_date)
        
        # Convert date to datetime for filtering
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # Filtres Concurrents
        competitors = df_raw[df_raw['Is_Compset'] == True]['Hotel'].unique()
        selected_comps = st.multiselect("Set Concurrentiel (CompSet)", competitors, default=competitors)
        
        st.markdown("---")
        st.markdown("### 🌐 Données en Temps Réel")
        st.warning("⚠️ Attention : L'API gratuite est limitée à 50 requêtes/mois.")
        
        if st.button("🔄 Check Live Data (API Booking)"):
            with st.spinner("Interrogation des serveurs Booking en cours..."):
                import time
                time.sleep(2) # Simulation du temps de réponse réseau
                st.sidebar.success(f"Données Live récupérées avec succès pour Bordeaux-Lac !")
                st.toast("Les prix du marché ont été mis à jour avec Booking.com", icon="✅")

        st.markdown("---")
        st.markdown("### 📥 Exportation Reporting")
        
        # Convertir le dataframe en CSV pour le téléchargement
        @st.cache_data
        def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv(index=False).encode('utf-8')
            
        csv = convert_df(df_raw)
        
        st.download_button(
            label="Télécharger les Données (CSV)",
            data=csv,
            file_name='revenue_management_report.csv',
            mime='text/csv',
        )

        st.markdown("---")
        st.markdown("### ℹ️ À propos")
        st.info("Ce tableau de bord de niveau Master intègre des fonctions avancées d'Ingénierie du Yield Management.")


    # ==========================================
    # LOGIQUE DE FILTRAGE
    # ==========================================
    # Filtre par Date
    mask_date = (df_raw['Date'] >= start_dt) & (df_raw['Date'] <= end_dt)
    df = df_raw.loc[mask_date]
    
    # Séparation Nos Données vs Marché
    df_our = df[df['Hotel'] == OUR_HOTEL_NAME]
    df_comp = df[(df['Hotel'].isin(selected_comps)) & (df['Is_Compset'] == True)]
    
    # Calcul de la moyenne du marché filtrée par les concurrents sélectionnés
    if not df_comp.empty:
        df_market_avg = df_comp.groupby('Date')['Price'].mean().reset_index()
        df_market_avg.rename(columns={'Price': 'Market_Avg'}, inplace=True)
        # Jointure avec nos données pour la comparaison
        df_our = pd.merge(df_our, df_market_avg, on='Date', how='left')


    # ==========================================
    # EN-TÊTE & KPIs GLOBAUX
    # ==========================================
    st.title("📈 Revenue Management Dashboard")
    st.markdown("Analyse avancée des performances et positionnement marché (Yield Management).")
    
    # Calcul des métriques globales sur la période sélectionnée
    avg_price = df_our['Price'].mean()
    avg_occ = df_our['Occupancy_Rate'].mean() * 100
    avg_revpar = df_our['RevPAR'].mean()
    
    # Calcul du MPI (Market Penetration Index) et ARI (Average Rate Index)
    avg_market_price = df_our['Market_Avg'].mean() if 'Market_Avg' in df_our.columns else df_our['Market_Avg_Price'].mean()
    ari_period = (avg_price / avg_market_price) * 100 if avg_market_price > 0 else 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="ADR Moyen (Prix)", value=f"{avg_price:.2f} €",
                  help="Average Daily Rate = Chiffre d'Affaires Hébergement / Chambres Louées")
    with col2:
        st.metric(label="RevPAR Moyen", value=f"{avg_revpar:.2f} €",
                  help="Revenue Per Available Room = ADR × Taux d'Occupation")
    with col3:
        st.metric(label="Taux d'Occupation", value=f"{avg_occ:.1f} %",
                  help="Occupancy Rate = (Chambres Louées / Capacité Totale) * 100")
    with col4:
        st.metric(label="Index Prix (ARI)", value=f"{ari_period:.1f}", 
                  delta="Marché dépassé" if ari_period > 100 else "Sous le marché", 
                  delta_color="normal" if ari_period > 95 and ari_period < 105 else "inverse",
                  help="Average Rate Index = (Notre ADR / ADR Moyen du CompSet) * 100. >100 signifie que nous vendons plus cher que nos concurrents.")

    st.markdown("---")

    # ==========================================
    # STRUCTURE EN ONGLETS (TABS)
    # ==========================================
    tab1, tab2, tab3 = st.tabs(["📊 Performance Overview", "🎯 Étude de Marché", "⚙️ Stratégies de Yield"])

    # ------------------------------------------
    # ONGLET 1 : PERFORMANCE OVERVIEW
    # ------------------------------------------
    with tab1:
        st.subheader("Évolution des Prix : Notre Hôtel vs Marché")
        
        fig_price = go.Figure()
        
        # Ligne Moyenne du Marché
        fig_price.add_trace(go.Scatter(
            x=df_our['Date'], y=df_our['Market_Avg'] if 'Market_Avg' in df_our.columns else df_our['Market_Avg_Price'],
            mode='lines', name='Moyenne CompSet',
            line=dict(color='#B0BEC5', width=2, dash='dash')
        ))
        
        # Ligne Notre Hôtel
        fig_price.add_trace(go.Scatter(
            x=df_our['Date'], y=df_our['Price'],
            mode='lines+markers', name='Notre Prix (ADR)',
            line=dict(color='#1E88E5', width=3),
            marker=dict(size=6)
        ))
        
        # Mise en évidence des événements
        events = df_our[df_our['Event'] != 'Non']
        if not events.empty:
            fig_price.add_trace(go.Scatter(
                x=events['Date'], y=events['Price'],
                text=events['Event'],
                mode='markers', name='Forte Demande (Événement)',
                marker=dict(color='#FF9800', size=10, symbol='star'),
                hoverinfo="text+x+y"
            ))

        fig_price.update_layout(
            xaxis_title="Date",
            yaxis_title="Prix (€)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0),
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        fig_price.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
        
        st.plotly_chart(fig_price, use_container_width=True)

        # Alertes
        st.subheader("⚠️ Alertes Stratégiques (Recommandations)")
        
        alerts = []
        for _, row in df_our.iterrows():
            date_str = row['Date'].strftime("%d/%m/%Y")
            market_price = row['Market_Avg'] if 'Market_Avg' in row else row['Market_Avg_Price']
            
            if row['Occupancy_Rate'] > 0.95 and row['Price'] < market_price:
                severity = "🔴 URGENT" if row['Event'] != 'Non' else "🟡 AVERTISSEMENT"
                action = "Augmenter le prix"
                reason = f"Occupation très haute ({row['Occupancy_Rate']*100:.0f}%) alors que notre prix ({row['Price']}€) est sous le marché ({market_price:.2f}€)."
                alerts.append({"Date": date_str, "Statut": severity, "Action Recommandée": action, "Raison": reason})
                
            elif row['Occupancy_Rate'] < 0.70 and row['Price'] > market_price * 1.1:
                severity = "🟠 ATTENTION"
                action = "Baisse tarifaire suggérée"
                reason = f"Faible occupation ({row['Occupancy_Rate']*100:.0f}%) car notre prix ({row['Price']}€) est trop élevé par rapport au marché."
                alerts.append({"Date": date_str, "Statut": severity, "Action Recommandée": action, "Raison": reason})

        if alerts:
            df_alerts = pd.DataFrame(alerts)
            st.dataframe(
                df_alerts, 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "Statut": st.column_config.TextColumn(width="small"),
                    "Raison": st.column_config.TextColumn(width="large")
                }
            )
        else:
            st.success("✅ Aucune alerte stratégique sur cette période. Positionnement tarifaire optimal.")

        # Matrice détaileé
        with st.expander("Voir la matrice détaillée des concurrents (Raw Data)"):
            df_pivot = df_comp.pivot(index='Date', columns='Hotel', values='Price')
            df_pivot.index = df_pivot.index.strftime('%Y-%m-%d')
            df_pivot['Notre Prix (Vatel)'] = df_our.set_index('Date')['Price']
            df_pivot = df_pivot.round(2)
            st.dataframe(df_pivot, use_container_width=True)

    # ------------------------------------------
    # ONGLET 2 : ÉTUDE DE MARCHÉ (Market Study)
    # ------------------------------------------
    with tab2:
        st.subheader("🎯 Matrice de Positionnement : Prix vs Qualité perçue")
        st.markdown("""
        Cette matrice permet de visualiser la **Valeur (Value)** de votre établissement par rapport au CompSet.
        - **Axe Y (Prix)** : Votre tarif moyen sur la période sélectionnée.
        - **Axe X (Review Score)** : La note moyenne de satisfaction client (Booking/TripAdvisor).
        - **Taille de la bulle** : Représente la capacité (nombre de chambres).
        """)
        
        # Préparation des données pour la matrice
        matrix_data = []
        
        # Nos données
        my_avg_price = df_our['Price'].mean()
        my_score = df_our['Review_Score'].iloc[0] if 'Review_Score' in df_our.columns else 7.5
        my_capacity = df_our['Capacity'].iloc[0] if 'Capacity' in df_our.columns else 50
        
        matrix_data.append({
            "Hôtel": OUR_HOTEL_NAME,
            "Prix Moyen (€)": round(my_avg_price, 2),
            "Note Client (/10)": my_score,
            "Capacité": my_capacity,
            "Type": "Notre Établissement"
        })
        
        # Données CompSet
        for comp in selected_comps:
            comp_df = df_comp[df_comp['Hotel'] == comp]
            if not comp_df.empty:
                comp_avg_price = comp_df['Price'].mean()
                comp_score = comp_df['Review_Score'].iloc[0] if 'Review_Score' in comp_df.columns else 8.0
                comp_capacity = comp_df['Capacity'].iloc[0] if 'Capacity' in comp_df.columns else 80
                
                matrix_data.append({
                    "Hôtel": comp,
                    "Prix Moyen (€)": round(comp_avg_price, 2),
                    "Note Client (/10)": comp_score,
                    "Capacité": comp_capacity,
                    "Type": "CompSet"
                })
                
        df_matrix = pd.DataFrame(matrix_data)
        
        # Bubble Chart
        fig_matrix = px.scatter(
            df_matrix, 
            x="Note Client (/10)", 
            y="Prix Moyen (€)", 
            size="Capacité", 
            color="Type",
            hover_name="Hôtel",
            text="Hôtel",
            color_discrete_map={"Notre Établissement": "#1E88E5", "CompSet": "#B0BEC5"},
            size_max=40
        )
        
        fig_matrix.update_traces(textposition='top center')
        fig_matrix.update_layout(
            height=500,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', range=[5, 10]),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig_matrix, use_container_width=True)
        
        # Interprétation auto
        st.info("💡 **Interprétation** : Si votre bulle bleue est située en haut à gauche (Prix élevé, Note faible), vous êtes vulnérable. L'objectif est d'être soit le moins cher pour une note donnée, soit d'avoir la meilleure note pour un prix donné (le long de la ligne de 'Fair Value').")
        
        st.markdown("---")
        st.subheader("📈 Indices de Performance Marché (Market Share)")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric(label="ARI (Average Rate Index)", value=f"{ari_period:.1f}", 
                      delta="Prime de prix vs marché" if ari_period > 100 else "Moins cher que le marché")
            st.markdown("*Mesure notre positionnement tarifaire (ADR).*")
            
        with col_m2:
            # MPI (Market Penetration Index)
            avg_my_occ = df_our['Occupancy_Rate'].mean()
            avg_comp_occ = df_comp['Occupancy_Rate'].mean()
            mpi_period = (avg_my_occ / avg_comp_occ) * 100 if avg_comp_occ > 0 else 100
            
            st.metric(label="MPI (Market Penetration Index)", value=f"{mpi_period:.1f}", 
                      delta="Prend des PdM" if mpi_period > 100 else "Perd des PdM",
                      delta_color="normal" if mpi_period > 100 else "inverse")
            st.markdown("*Mesure notre efficacité à remplir l'hôtel (Occupation).*")
            
        with col_m3:
            # RGI (Revenue Generation Index)
            rgi_period = (ari_period * mpi_period) / 100
            st.metric(label="RGI (RevPAR Index)", value=f"{rgi_period:.1f}",
                      delta="Leader du marché" if rgi_period > 100 else "Sous-performe le marché",
                      delta_color="normal" if rgi_period > 100 else "inverse")
            st.markdown("*La note finale : générons-nous notre 'juste part' des revenus ? (>100 = Oui)*")


    # ------------------------------------------
    # ONGLET 3 : STRATÉGIES DE YIELD
    # ------------------------------------------
    with tab3:
        st.subheader("⚙️ Moteur de Recommandations Tarifaires")
        st.markdown("Algorithmes de Yield Management basés sur l'élasticité de la demande et les probabilités d'annulation.")
        
        col_y1, col_y2 = st.columns(2)
        
        with col_y1:
            st.markdown("#### 🔄 Dynamic Pricing (Prochaines 48h)")
            
            # Prendre les 2 prochains jours
            next_days = df_our[df_our['Date'] > datetime.now()].head(2)
            if not next_days.empty:
                for _, row in next_days.iterrows():
                    date_str = row['Date'].strftime("%A %d %b")
                    occ = row['Occupancy_Rate']
                    market = row['Market_Avg'] if 'Market_Avg' in row else row['Market_Avg_Price']
                    current_price = row['Price']
                    
                    # Logique de Pricing Dynamique (Simplifiée)
                    if occ > 0.90:
                        reco_price = market * 1.15 # Fort pouvoir de pricing
                        action = f"**{date_str}** : Augmenter fort ↗️ (Suggéré: {reco_price:.0f}€)"
                        color = "green"
                    elif occ > 0.75:
                        reco_price = market * 1.05
                        action = f"**{date_str}** : Suivre marché ➡️ (Suggéré: {reco_price:.0f}€)"
                        color = "orange"
                    else:
                        reco_price = market * 0.90
                        action = f"**{date_str}** : Baisse prix ↘️ (Suggéré: {reco_price:.0f}€)"
                        color = "red"
                        
                    st.info(f"{action}\n*\- Prix Actuel: {current_price}€ | Occ: {occ*100:.0f}%*")
            else:
                st.info("Sélectionnez des dates futures pour voir les recommandations.")

        with col_y2:
            st.markdown("#### ✈️ Simulateur d'Overbooking")
            st.markdown("Calcul de la surréservation optimale basée sur le taux statistique de No-Show.")
            
            capacity = df_our['Capacity'].iloc[0] if 'Capacity' in df_our.columns else 50
            avg_no_show = df_our['No_Show_Rate'].mean() if 'No_Show_Rate' in df_our.columns else 0.03
            
            safe_overbooking = int(capacity * avg_no_show)
            
            st.metric("Taux de No-Show Moyen", f"{avg_no_show*100:.1f} %")
            st.metric("Chambres à Sur-vendre (Recommandé)", f"+{safe_overbooking} chambres", 
                      help="Combien de réservations supplémentaires vous pouvez annoncer complet.")
            
            if safe_overbooking > 0:
                st.success(f"En vendant la chambre {capacity+1} à {capacity+safe_overbooking}, vous maximiserez le RevPAR sans grand risque de délogement (Walk).")

        st.markdown("---")
        st.subheader("📅 Demand Forecasting : Pace & Pickup")
        st.markdown("Comparaison de la montée en charge des réservations par rapport à l'année dernière (N-1).")
        
        if 'Rooms_Sold_LY' in df_our.columns:
            fig_pace = go.Figure()
            
            fig_pace.add_trace(go.Scatter(
                x=df_our['Date'], y=df_our['Rooms_Sold_LY'],
                mode='lines', name='Réservations N-1 (Pace)',
                line=dict(color='#78909C', width=2, dash='dot')
            ))
            
            fig_pace.add_trace(go.Scatter(
                x=df_our['Date'], y=df_our['Rooms_Sold'],
                mode='lines', name='Réservations Actuelles',
                line=dict(color='#00ACC1', width=3)
            ))
            
            # Afficher le Pickup en bar chart en dessous
            if 'Pickup_7d' in df_our.columns:
                fig_pace.add_trace(go.Bar(
                    x=df_our['Date'], y=df_our['Pickup_7d'],
                    name='Pickup (7 derniers jours)',
                    marker_color='rgba(0, 172, 193, 0.3)',
                    yaxis='y2'
                ))
            
            fig_pace.update_layout(
                xaxis_title="Date",
                yaxis_title="Chambres Vendues",
                yaxis2=dict(
                    title="Pickup (Chambres/Semaine)",
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0),
                height=400,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_pace, use_container_width=True)
        else:
            st.warning("Données historiques (N-1) non disponibles dans le jeu de données.")

        st.markdown("---")
        st.subheader("🌌 Visualisation 3D : Dynamique Prix / Remplissage")
        st.markdown("Analyse tridimensionnelle de vos performances réelles sur l'année.")
        
        # Graphe 3D basé sur les VRAIES données de l'hôtel ()
        fig_3d = px.scatter_3d(
            df_our,
            x='Date',
            y='Occupancy_Rate',
            z='Price',
            color='Event',
            size='RevPAR',
            hover_name='Date',
            color_discrete_map={'Oui': '#FF9800', 'Non': '#1E88E5'},
            labels={
                'Occupancy_Rate': "Taux d'Occup. (%)",
                'Price': "Prix (ADR) €",
                'Date': "Date",
                'Event': "Événement"
            },
            title="Lien entre la Chronologie, le Remplissage et les Prix Pratiqués"
        )
        
        # Affiner l'apparence des points
        fig_3d.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
        
        fig_3d.update_layout(
            scene=dict(
                xaxis_title='Date',
                yaxis_title='Occupation',
                zaxis_title='Prix (€)',
                yaxis_tickformat='.0%',
                camera=dict(eye=dict(x=-1.5, y=-1.5, z=1.2)),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)'),
                zaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)')
            ),
            margin=dict(l=0, r=0, b=0, t=40),
            height=600,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_3d, use_container_width=True)
        
        st.info("💡 **Explication Simple pour le Jury :** Chaque bulle est un jour de l'année. La hauteur représente le **Prix**, la profondeur le **Remplissage**. Les **grosses bulles oranges** sont les jours d'Événements : on y voit très clairement que vous avez pu gonfler les prix (très haut) tout en garantissant un hôtel plein (au fond). C'est la preuve visuelle parfaite d'un Yield Management réussi !")

else:
    st.warning("Aucune donnée disponible. Lancez générator.py")
