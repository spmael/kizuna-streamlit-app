import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np



def ttc_to_ht(prix_ttc, taux_tva=0.1925):
    return prix_ttc / (1 + taux_tva)
st.set_page_config(page_title="Simulation Financière KIZUNA", layout="wide")

st.title("💼 Optimisation Rentabilité - Restaurant KIZUNA")

# Sidebar pour les paramètres financiers
st.sidebar.header("🔧 Paramètres Financiers")

# Paramètres globaux
ca_actuel = st.sidebar.number_input("Chiffre d'affaires mensuel actuel (FCFA)", value=1976150)
marge_brute_visee_pct = st.sidebar.slider("Marge brute visée (%)", min_value=30, max_value=70, value=50, step=5)
cout_matiere_actuel = st.sidebar.number_input("Coût matière actuel (FCFA)", value=1321893)
cout_variable = st.sidebar.number_input("Coûts variables (FCFA)", value=27540)

st.sidebar.markdown("### Coûts fixes")
st.sidebar.markdown("#### Coûts fixes personnel")
salaire_directeur = st.sidebar.number_input("Salaire Directeur", value=200000)
salaire_serveuse = st.sidebar.number_input("Salaire Serveuse", value=40000)

st.sidebar.markdown("#### Coûts fixes divers")
electricite = st.sidebar.number_input("Facture Electricité", value=67593)
abonnement_canal = st.sidebar.number_input("Abonnement CANAL+", value=54000)
transport = st.sidebar.number_input("Transport", value=50000)
recharge_infinity = st.sidebar.number_input("Recharge Infinity BOX", value=30000)
carnet_recu = st.sidebar.number_input("Carnet de Reçus", value=2050)
boite_cure_dents = st.sidebar.number_input("Boite de cure dents", value=100)
emballage_oumbe = st.sidebar.number_input("Emballage oumbe", value=100)

# Coûts fixes projetés
st.sidebar.markdown("#### Coûts fixes projetés")
salaire_serveuse_1 = st.sidebar.number_input("Serveuse 1", value=60000)
salaire_serveuse_2 = st.sidebar.number_input("Serveuse 2", value=60000)
loyer = st.sidebar.number_input("Loyer", value=400000)
erp = st.sidebar.number_input("ERP (2 utilisateurs)", value=90000)
web_email = st.sidebar.number_input("Site web + email", value=40000)

# Calcul des coûts totaux
total_fixes_actuels = salaire_directeur + salaire_serveuse + electricite + abonnement_canal + transport + recharge_infinity + carnet_recu + boite_cure_dents + emballage_oumbe
total_fixes_projetes = total_fixes_actuels + salaire_serveuse_1 + salaire_serveuse_2 + loyer + erp + web_email - salaire_serveuse  # On remplace le salaire actuel

# Paramètres d'optimisation
st.sidebar.markdown("### 🎯 Paramètres d'Optimisation")
mode_optimisation = st.sidebar.radio(
    "Mode d'optimisation",
    ["Équilibré", "Maximiser les produits rentables", "Augmentation uniforme"]
)

facteur_prod_forte_marge = st.sidebar.slider(
    "Facteur d'augmentation produits forte marge (>50%)",
    min_value=1.0, 
    max_value=5.0, 
    value=2.5, 
    step=0.5,
    help="Coefficient multiplicateur des ventes pour les produits ayant une marge >50%"
)

facteur_prod_moy_marge = st.sidebar.slider(
    "Facteur d'augmentation produits marge moyenne (35-50%)",
    min_value=1.0, 
    max_value=4.0, 
    value=2.0, 
    step=0.5
)

facteur_prod_faible_marge = st.sidebar.slider(
    "Facteur d'augmentation produits faible marge (20-35%)",
    min_value=1.0, 
    max_value=4.0, 
    value=1.5, 
    step=0.5
)

facteur_prod_tres_faible_marge = st.sidebar.slider(
    "Facteur d'augmentation produits très faible marge (<20%)",
    min_value=0.0, 
    max_value=2.0, 
    value=0.9, 
    step=0.1,
    help="Valeur 0 pour arrêter de vendre les produits non rentables"
)

st.sidebar.markdown("### 📊 Affichage")

with st.sidebar.expander("📘 Guide d'utilisation"):
    st.markdown("""
    **🎯 Objectif**  
    Simule la rentabilité de KIZUNA en ajustant les prix, marges et volumes.

    **🔧 Étapes principales**  
    1. Paramétrer les coûts fixes, variables, CA, etc.  
    2. Choisir un **mode d’optimisation** :  
       - 🎯 Équilibré : augmente selon la marge  
       - 💹 Maximiser les produits rentables  
       - 📈 Uniforme : même facteur pour tous  
    3. Modifier les **prix TTC** (conversion HT auto)  
    4. Lancer la simulation → Voir CA optimisé, marges, seuil de rentabilité  
    5. Consulter les **recommandations & plan d'action**

    **💡 Astuce**  
    Active “Détails par produit” ou “Dépenses” pour une analyse fine.
    """)

afficher_details = st.sidebar.checkbox("Afficher les détails par produit", value=False)
afficher_depenses = st.sidebar.checkbox("Afficher les depenses par produit", value=False)

# Fonction pour charger et préparer les données
@st.cache_data
def charger_donnees():
    try:
        df = pd.read_csv("produits_par_categorie_avril.csv")

        # Calcul des métriques par produit
        df['Prix Unitaire HT'] = ttc_to_ht(df['Prix Unitaire (FCFA)'])
        df['CA'] = df['Prix Unitaire HT'] * df['Quantité Avril']
        df['CA TTC'] = df['Prix Unitaire (FCFA)'] * df['Quantité Avril']
        df['Marge Valeur'] = df['CA'] * (df['Marge (%)'] / 100)
        df['Marge Valeur TTC'] = df['CA TTC'] * (df['Marge (%)'] / 100)
        df['Coût Unitaire'] = df['Prix Unitaire HT'] * (1 - df['Marge (%)'] / 100)
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return None

# Chargement des données
df = charger_donnees()

# Calcul des métriques financières actuelles
if df is not None:  
    st.header("🛠️ Modification des Prix de Vente (TTC)")
    st.markdown("Modifiez les prix **TTC** par produit. Les conversions HT seront faites automatiquement pour l'optimisation.")
    prix_modifiables = {}

    categories = df['Catégorie'].unique()
    for cat in categories:
        st.subheader(f"📦 {cat}")
        cat_df = df[df['Catégorie'] == cat]

        cols = st.columns(6)

        for i, (idx, row) in enumerate(cat_df.iterrows()):
            with cols[i % 6]:
                prix_ttc = st.number_input(
                    f"{row['Produit']}",
                    value=float(f"{row['Prix Unitaire (FCFA)']:.0f}"),
                    key=f"prix_{cat}_{i}",
                    help="Prix TTC en FCFA"
                )
                prix_ht = prix_ttc / (1 + 0.1925)
                df.at[idx, 'Prix Unitaire HT'] = prix_ht
                df.at[idx, 'Prix Unitaire (FCFA)'] = prix_ttc  # mise à jour pour affichage cohérent
                # Recalcul de la marge (%) en fonction du coût unitaire et nouveau prix HT
                cout_unitaire = df.at[idx, 'Coût Unitaire']
                if prix_ht > 0:
                    marge_pct = (1 - (cout_unitaire / prix_ht)) * 100
                else:
                    marge_pct = 0
                df.at[idx, 'Marge (%)'] = marge_pct


    # Recalcul des métriques après modification
    df['CA'] = df['Prix Unitaire HT'] * df['Quantité Avril']
    df['Marge Valeur'] = df['CA'] * (df['Marge (%)'] / 100)
    df['Coût Unitaire'] = df['Prix Unitaire HT'] * (1 - df['Marge (%)'] / 100)

    df['CA'] = df['Prix Unitaire HT'] * df['Quantité Avril']
    df['Marge Valeur'] = df['CA'] * (df['Marge (%)'] / 100)
    df['Coût Unitaire'] = df['Prix Unitaire HT'] * (1 - df['Marge (%)'] / 100)

    # Calculs financiers actuels
    ca_total_actuel = df['CA TTC'].sum()
    marge_brute_actuelle = df['Marge Valeur TTC'].sum()
    marge_brute_pct_actuelle = (marge_brute_actuelle / ca_total_actuel) * 100 if ca_total_actuel > 0 else 0
    cout_total_actuel = ca_total_actuel - marge_brute_actuelle
    
    # Coûts totaux et résultat
    total_charges_actuel = cout_total_actuel + total_fixes_actuels + cout_variable
    resultat_net_actuel = ca_total_actuel - total_charges_actuel
    resultat_net_pct_actuel = (resultat_net_actuel / ca_total_actuel) * 100 if ca_total_actuel > 0 else 0
    
    # Seuil de rentabilité
    cout_fixe_total = total_fixes_projetes + cout_variable
    seuil_rentabilite = cout_fixe_total / (marge_brute_visee_pct / 100)
    
    # Affichage des métriques actuelles
    st.header("📊 Situation Financière Actuelle")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Chiffre d'Affaires", f"{ca_total_actuel:,.0f} FCFA")
        st.metric("Coûts Fixes", f"{total_fixes_actuels:,.0f} FCFA")
    with col2:
        st.metric("Marge Brute", f"{marge_brute_actuelle:,.0f} FCFA", f"{marge_brute_pct_actuelle:.2f}%")
        st.metric("Coûts Variables", f"{cout_variable:,.0f} FCFA")
    with col3:
        st.metric("Résultat Net", f"{resultat_net_actuel:,.0f} FCFA", f"{resultat_net_pct_actuel:.2f}%")
        st.metric("Seuil de Rentabilité Visé", f"{seuil_rentabilite:,.0f} FCFA")
    
    # Ligne de séparation
    st.markdown("---")
    
    # Algorithme d'optimisation des ventes
    st.header("🧠 Optimisation des Ventes pour une Marge de 50%")
    
    # Créer une copie du dataframe pour l'optimisation
    df_optimise = df.copy()
    
    # Appliquer les facteurs d'augmentation selon la stratégie choisie
    if mode_optimisation == "Équilibré":
        # Stratégie équilibrée - basée sur la marge
        df_optimise['Facteur Augmentation'] = df_optimise['Marge (%)'].apply(
            lambda x: facteur_prod_tres_faible_marge if x < 20 else
                     (facteur_prod_faible_marge if x < 35 else
                     (facteur_prod_moy_marge if x < 50 else facteur_prod_forte_marge))
        )
    elif mode_optimisation == "Maximiser les produits rentables":
        # Favoriser les produits rentables, réduire les produits à faible marge
        df_optimise['Score'] = df_optimise['Marge (%)'] * df_optimise['Prix Unitaire (FCFA)'] / 1000
        max_score = df_optimise['Score'].max()
        df_optimise['Facteur Augmentation'] = df_optimise.apply(
            lambda row: facteur_prod_tres_faible_marge if row['Marge (%)'] < 20 else
                      (facteur_prod_faible_marge if row['Marge (%)'] < 35 else
                      (facteur_prod_moy_marge if row['Marge (%)'] < 50 else 
                       facteur_prod_forte_marge * (0.8 + 0.4 * (row['Score'] / max_score)))), axis=1
        )
    else:  # Augmentation uniforme
        # Appliquer un facteur d'augmentation uniforme basé sur le ratio requis
        ratio_augmentation_requis = seuil_rentabilite / ca_total_actuel
        facteur_uniforme = min(4.0, max(1.1, ratio_augmentation_requis * 0.8))  # Limité entre 1.1 et 4.0
        df_optimise['Facteur Augmentation'] = facteur_uniforme
        # Mais garder facteur_prod_tres_faible_marge pour les produits non rentables
        df_optimise.loc[df_optimise['Marge (%)'] < 0, 'Facteur Augmentation'] = facteur_prod_tres_faible_marge
    
    # Si le facteur est 0 pour les produits à très faible marge, mettre à 0 les quantités
    df_optimise.loc[(df_optimise['Marge (%)'] < 0) & (facteur_prod_tres_faible_marge == 0), 'Facteur Augmentation'] = 0
    
    # Calculer les nouvelles quantités et métriques
    df_optimise['Quantité Optimisée'] = (df_optimise['Quantité Avril'] * df_optimise['Facteur Augmentation']).round().astype(int)
    df_optimise['CA Optimisé'] = df_optimise['Quantité Optimisée'] * df_optimise['Prix Unitaire (FCFA)']
    df_optimise['Marge Valeur Optimisée'] = df_optimise['CA Optimisé'] * (df_optimise['Marge (%)'] / 100)
    
    # Calculer les variations et dépenses additionnelles
    df_optimise['Variation Quantité'] = df_optimise['Quantité Optimisée'] - df_optimise['Quantité Avril']
    df_optimise['Dépenses Additionnelles'] = df_optimise['Variation Quantité'] * df_optimise['Coût Unitaire']
    df_optimise['CA Additionnel'] = df_optimise['Variation Quantité'] * df_optimise['Prix Unitaire (FCFA)']
    
    # Calcul des totaux après optimisation
    ca_optimise = df_optimise['CA Optimisé'].sum()
    marge_optimisee = df_optimise['Marge Valeur Optimisée'].sum()
    marge_pct_optimisee = (marge_optimisee / ca_optimise) * 100 if ca_optimise > 0 else 0
    cout_matiere_optimise = ca_optimise - marge_optimisee
    depenses_additionnelles_total = df_optimise['Dépenses Additionnelles'].sum()
    
    # Résultat avec coûts projetés
    total_charges_optimise = cout_matiere_optimise + total_fixes_projetes + cout_variable
    resultat_net_optimise = ca_optimise - total_charges_optimise
    resultat_net_pct_optimise = (resultat_net_optimise / ca_optimise) * 100 if ca_optimise > 0 else 0
    
    # Affichage des résultats de l'optimisation
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("CA Optimisé", f"{ca_optimise:,.0f} FCFA", f"{((ca_optimise/ca_total_actuel)-1)*100:.1f}%")
        st.metric("Coûts Fixes Projetés", f"{total_fixes_projetes:,.0f} FCFA")
    with col2:
        st.metric("Marge Brute Optimisée", f"{marge_optimisee:,.0f} FCFA", f"{marge_pct_optimisee:.2f}%")
        st.metric("Coût Matière Optimisé", f"{cout_matiere_optimise:,.0f} FCFA")
    with col3:
        st.metric("Résultat Net Projeté", f"{resultat_net_optimise:,.0f} FCFA", f"{resultat_net_pct_optimise:.2f}%")
        st.metric("Écart au Seuil", f"{ca_optimise - seuil_rentabilite:,.0f} FCFA")
    
    # Évaluation de l'atteinte de l'objectif
    if ca_optimise >= seuil_rentabilite:
        st.success(f"✅ OBJECTIF ATTEINT : Le CA optimisé ({ca_optimise:,.0f} FCFA) dépasse le seuil de rentabilité ({seuil_rentabilite:,.0f} FCFA)")
    else:
        st.warning(f"⚠️ OBJECTIF NON ATTEINT : Il manque encore {seuil_rentabilite - ca_optimise:,.0f} FCFA pour atteindre le seuil de rentabilité")
        st.info("Suggestions : Augmenter les prix des produits ou réduire les coûts fixes projetés")
    
    # Visualisation par catégorie
    st.header("📈 Analyse par Catégorie")
    
    # Agrégation par catégorie
    cat_actuel = df.groupby('Catégorie').agg({
        'CA': 'sum',
        'Marge Valeur': 'sum'
    }).reset_index()
    cat_actuel['Marge %'] = (cat_actuel['Marge Valeur'] / cat_actuel['CA']) * 100
    
    cat_optimise = df_optimise.groupby('Catégorie').agg({
        'CA Optimisé': 'sum',
        'Marge Valeur Optimisée': 'sum'
    }).reset_index()
    cat_optimise['Marge % Optimisée'] = (cat_optimise['Marge Valeur Optimisée'] / cat_optimise['CA Optimisé']) * 100
    
    # Fusion des données
    cat_compare = pd.merge(cat_actuel, cat_optimise, on='Catégorie')
    cat_compare['Variation CA %'] = ((cat_compare['CA Optimisé'] / cat_compare['CA']) - 1) * 100
    cat_compare['Variation Marge %'] = cat_compare['Marge % Optimisée'] - cat_compare['Marge %']
    
    # Tri par CA optimisé décroissant
    cat_compare = cat_compare.sort_values(by='CA Optimisé', ascending=False)
    
    # Visualisation graphique - Comparaison CA par catégorie
    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        x=cat_compare['Catégorie'],
        y=cat_compare['CA'],
        name='CA Actuel',
        marker_color='lightgray'
    ))
    fig1.add_trace(go.Bar(
        x=cat_compare['Catégorie'],
        y=cat_compare['CA Optimisé'],
        name='CA Optimisé',
        marker_color='royalblue'
    ))
    fig1.update_layout(
        title="Comparaison du CA par Catégorie",
        xaxis_title="Catégorie",
        yaxis_title="Chiffre d'Affaires (FCFA)",
        barmode='group'
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Visualisation graphique - Comparaison Marge % par catégorie
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=cat_compare['Catégorie'],
        y=cat_compare['Marge %'],
        name='Marge % Actuelle',
        marker_color='coral'
    ))
    fig2.add_trace(go.Bar(
        x=cat_compare['Catégorie'],
        y=cat_compare['Marge % Optimisée'],
        name='Marge % Optimisée',
        marker_color='green'
    ))
    # Ligne de référence pour la marge visée
    fig2.add_shape(
        type="line",
        x0=-0.5,
        y0=marge_brute_visee_pct,
        x1=len(cat_compare)-0.5,
        y1=marge_brute_visee_pct,
        line=dict(color="red", width=2, dash="dash")
    )
    fig2.add_annotation(
        x=len(cat_compare)-1,
        y=marge_brute_visee_pct,
        text=f"Objectif: {marge_brute_visee_pct}%",
        showarrow=False,
        yshift=10
    )
    fig2.update_layout(
        title="Comparaison de la Marge % par Catégorie",
        xaxis_title="Catégorie",
        yaxis_title="Marge (%)",
        barmode='group'
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Détails par produit
    if afficher_details:
        st.header("🔍 Analyse Détaillée par Produit")
        
        # Tri par catégorie et marge optimisée
        df_details = df_optimise.sort_values(by=['Catégorie', 'Marge Valeur Optimisée'], ascending=[True, False])
        
        # Sélection des colonnes à afficher
        df_details_affichage = df_details[[
            'Catégorie', 'Produit', 'Prix Unitaire (FCFA)', 'Marge (%)', 
            'Quantité Avril', 'Quantité Optimisée', 'CA', 'CA Optimisé',
            'Marge Valeur', 'Marge Valeur Optimisée'
        ]].copy()
        
        # Calcul de la variation
        df_details_affichage['Variation Quantité'] = df_details_affichage['Quantité Optimisée'] - df_details_affichage['Quantité Avril']
        df_details_affichage['Variation CA'] = df_details_affichage['CA Optimisé'] - df_details_affichage['CA']
        
        # Affichage par catégorie
        categories = df_details_affichage['Catégorie'].unique()
        
        cat_selectionnee = st.selectbox(
            "Sélectionner une catégorie pour l'analyse détaillée",
            ["Toutes les catégories"] + list(categories)
        )
        
        if cat_selectionnee == "Toutes les catégories":
            df_affichage = df_details_affichage
        else:
            df_affichage = df_details_affichage[df_details_affichage['Catégorie'] == cat_selectionnee]
        
        # Graphique des produits par quantité
        fig3 = px.bar(
            df_affichage.sort_values('Quantité Optimisée', ascending=False).head(15),
            x='Produit',
            y=['Quantité Avril', 'Quantité Optimisée'],
            barmode='group',
            title=f"Top 15 Produits par Quantité - {cat_selectionnee}",
            labels={'value': 'Quantité', 'variable': 'Période'}
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # Tableau détaillé
        df_table = df_affichage.copy()
        df_table['Variation %'] = (df_table['Variation Quantité'] / df_table['Quantité Avril'] * 100).fillna(0)
        
        # Formatage des colonnes
        df_table = df_table.rename(columns={
            'Prix Unitaire (FCFA)': 'Prix',
            'Quantité Avril': 'Qté Avril',
            'Quantité Optimisée': 'Qté Optimisée',
            'Variation Quantité': 'Var. Qté',
            'Variation %': 'Var. %',
            'Marge Valeur': 'Marge Actuelle',
            'Marge Valeur Optimisée': 'Marge Optimisée'
        })
        
        # Ordre des colonnes
        colonnes_affichage = [
            'Produit', 'Prix', 'Marge (%)', 'Qté Avril', 'Qté Optimisée', 
            'Var. Qté', 'Var. %', 'CA', 'CA Optimisé', 'Marge Actuelle', 'Marge Optimisée'
        ]
        
        if cat_selectionnee == "Toutes les catégories":
            colonnes_affichage = ['Catégorie'] + colonnes_affichage
        
        df_table = df_table[colonnes_affichage]
        
        # Formatage numérique pour la lisibilité
        for col in ['Prix', 'CA', 'CA Optimisé', 'Marge Actuelle', 'Marge Optimisée']:
            df_table[col] = df_table[col].apply(lambda x: f"{x:,.0f} FCFA")
        
        df_table['Marge (%)'] = df_table['Marge (%)'].apply(lambda x: f"{x:.2f}%")
        df_table['Var. %'] = df_table['Var. %'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_table, use_container_width=True)
    
    # Recommandations
    st.header("💡 Recommandations d'Action")
    
    # Identifier les produits à forte amélioration
    top_amelioration = df_optimise.copy()
    top_amelioration['Gain CA'] = top_amelioration['CA Optimisé'] - top_amelioration['CA']
    top_amelioration['Gain Marge'] = top_amelioration['Marge Valeur Optimisée'] - top_amelioration['Marge Valeur']
    
    # Top produits par gain de marge
    top_marge = top_amelioration.sort_values('Gain Marge', ascending=False).head(5)
    
    # Produits à faible/négative marge
    produits_problematiques = df[(df['Marge (%)'] < 20) & (df['Quantité Avril'] > 5)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Produits à Prioriser")
        for i, row in top_marge.iterrows():
            st.write(f"**{row['Produit']}** ({row['Catégorie']})")
            st.write(f"- Prix: {row['Prix Unitaire HT']:,.0f} FCFA, Marge: {row['Marge (%)']:.2f}%")
            st.write(f"- Qté actuelle: {row['Quantité Avril']} → Qté optimisée: {row['Quantité Optimisée']} (+{row['Quantité Optimisée']-row['Quantité Avril']})")
            st.write(f"- Gain potentiel: {row['Gain Marge']:,.0f} FCFA")
            st.write(f"- Dépenses additionnelles: {row['Dépenses Additionnelles']:,.0f} FCFA")
            st.markdown("---")
    
    with col2:
        st.subheader("Produits à Revoir")
        if len(produits_problematiques) > 0:
            for i, row in produits_problematiques.iterrows():
                st.write(f"**{row['Produit']}** ({row['Catégorie']})")
                st.write(f"- Prix: {row['Prix Unitaire HT']:,.0f} FCFA, **Marge: {row['Marge (%)']:.2f}%**")
                nouveau_prix = row['Coût Unitaire'] / (1 - 0.35)
                prix_ttc_suggere = nouveau_prix * 1.1925  # Pour une marge de 35%
                st.write(f"- Prix suggéré pour 35% de marge: {prix_ttc_suggere:,.0f} FCFA TTC (+{prix_ttc_suggere - row['Prix Unitaire HT']:,.0f} FCFA)")
                st.markdown("---")
        else:
            st.write("Aucun produit problématique identifié (marge < 20% et ventes > 5)")
    
        # Détails des dépenses additionnelles par produit
    if afficher_depenses:
        st.header("💰 Dépenses Additionnelles par Produit")
        
        # Top produits par dépenses additionnelles
        top_depenses = df_optimise.sort_values('Dépenses Additionnelles', ascending=False).head(15)
        
        fig_top_depenses = px.bar(
            top_depenses,
            x='Produit',
            y='Dépenses Additionnelles',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_top_depenses, use_container_width=True)
        
    # Suggestions générales
    st.subheader("Plan d'Action Recommandé")
    
    actions = [
        "**1. Révision des prix**: Augmenter les prix des produits à marge faible ou négative, en particulier dans la catégorie des Plats Chauds.",
        "**2. Planification des achats**: Prévoir un budget d'approvisionnement de {depenses_additionnelles_total:,.0f} FCFA pour atteindre les objectifs de vente.",
        "**3. Promotions ciblées**: Mettre en avant les produits à forte marge comme les Ailes de Poulet, l'Eau Tangui et les autres boissons non-alcoolisées.",
        "**4. Standardisation des portions**: Établir des fiches techniques précises pour contrôler les coûts matière, notamment pour les plats cuisinés.",
        "**5. Ventes croisées**: Encourager l'association des grillades avec les boissons à forte marge.",
        "**6. Happy Hours stratégiques**: Lancer des promotions sur les produits à forte marge pour augmenter le volume de ventes."
    ]
    
    actions[1] = actions[1].format(depenses_additionnelles_total=depenses_additionnelles_total)
    
    for action in actions:
        st.markdown(f"{action}")
    
    # Calendrier suggéré
    st.subheader("Calendrier d'Implémentation Suggéré")
    
    st.markdown("""
    | Semaine | Actions | Budget Requis |
    |---------|---------|--------------|
    | Semaine 1 | Révision des prix et mise à jour de la carte | Minimal |
    | Semaine 2 | Formation du personnel et premières promotions | {form_budget:,.0f} FCFA |
    | Semaine 3 | Premier réapprovisionnement majeur | {reappro_budget:,.0f} FCFA |
    | Semaine 4 | Lancement des happy hours et second réapprovisionnement | {happy_budget:,.0f} FCFA |
    """.format(
        form_budget=10000,
        reappro_budget=depenses_additionnelles_total * 0.4,
        happy_budget=depenses_additionnelles_total * 0.6
    ))
        
    # Tableau détaillé des dépenses par produit
    col1, col2 = st.columns([1, 2])
    
    with col1:
        categorie_filtree = st.selectbox(
            "Filtrer par catégorie",
            ["Toutes les catégories"] + sorted(df_optimise['Catégorie'].unique().tolist())
        )
    
    with col2:
        seuil_depenses = st.slider(
            "Afficher les produits avec des dépenses supérieures à",
            min_value=0,
            max_value=int(df_optimise['Dépenses Additionnelles'].max()),
            value=5000,
            step=1000,
            format="%d FCFA"
        )
    
    # Filtrage des données
    if categorie_filtree == "Toutes les catégories":
        df_depenses = df_optimise[df_optimise['Dépenses Additionnelles'] >= seuil_depenses].copy()
    else:
        df_depenses = df_optimise[(df_optimise['Catégorie'] == categorie_filtree) & 
                                    (df_optimise['Dépenses Additionnelles'] >= seuil_depenses)].copy()
    
    # Tri par dépenses additionnelles décroissantes
    df_depenses = df_depenses.sort_values('Dépenses Additionnelles', ascending=False)
    
    # Sélection et renommage des colonnes pour l'affichage
    df_depenses_aff = df_depenses[[
        'Catégorie', 'Produit', 'Prix Unitaire (FCFA)', 'Coût Unitaire', 'Marge (%)',
        'Quantité Avril', 'Quantité Optimisée', 'Variation Quantité', 
        'Dépenses Additionnelles', 'CA Additionnel'
    ]].copy()
    
    df_depenses_aff = df_depenses_aff.rename(columns={
        'Prix Unitaire (FCFA)': 'Prix',
        'Quantité Avril': 'Qté Actuelle',
        'Quantité Optimisée': 'Qté Optimisée',
        'Variation Quantité': 'Var. Qté'
    })
    
    # Formatage des colonnes monétaires et pourcentages
    for col in ['Prix', 'Coût Unitaire', 'Dépenses Additionnelles', 'CA Additionnel']:
        df_depenses_aff[col] = df_depenses_aff[col].apply(lambda x: f"{x:,.0f} FCFA")
    
    df_depenses_aff['Marge (%)'] = df_depenses_aff['Marge (%)'].apply(lambda x: f"{x:.2f}%")
    
    # Calcul du total des dépenses additionnelles filtrées
    total_depenses_filtrees = df_depenses['Dépenses Additionnelles'].sum()
    pct_total = (total_depenses_filtrees / depenses_additionnelles_total) * 100
    
    st.write(f"**Total des dépenses additionnelles sélectionnées:** {total_depenses_filtrees:,.0f} FCFA ({pct_total:.1f}% du total)")
    
    # Affichage du tableau
    st.dataframe(df_depenses_aff, use_container_width=True)
    
    # Conseil sur les achats
    st.subheader("💡 Conseils pour la gestion des achats")
    
    st.write("""
    Pour gérer efficacement les achats additionnels:
    1. **Planifiez vos commandes** par priorité de dépenses et fréquence de livraison
    2. **Négociez des remises sur volume** avec vos fournisseurs pour les produits à forte dépense
    3. **Surveillez vos stocks** pour éviter les ruptures des produits populaires
    4. **Échelonnez vos achats** sur plusieurs semaines pour répartir la charge financière
    """)
    
    # Résumé par fournisseur (simulé)
    st.subheader("Répartition estimée des dépenses par type de fournisseur")
    
    # Classification simplifiée par catégorie
    fournisseurs = {
        "Bières": "Distributeur de boissons",
        "Grillades": "Boucher / Fournisseur de viande",
        "Plats Chauds": "Fournisseur alimentaire",
        "Accompagnements": "Fournisseur alimentaire",
        "Boissons Gazeuses": "Distributeur de boissons",
        "Eau Minérale et Gazeuse": "Distributeur de boissons",
        "Alcool Mix": "Distributeur de boissons",
        "Liqueur": "Distributeur de boissons",
        "Services": "Non applicable"
    }
    
    # Créer un DataFrame pour les fournisseurs
    df_fournisseurs = df_optimise.copy()
    df_fournisseurs['Fournisseur'] = df_fournisseurs['Catégorie'].map(fournisseurs)
    
    # Agréger les dépenses par fournisseur
    fournisseur_sum = df_fournisseurs.groupby('Fournisseur')['Dépenses Additionnelles'].sum().reset_index()
    fournisseur_sum = fournisseur_sum.sort_values('Dépenses Additionnelles', ascending=False)
    
    # Graphique de répartition des dépenses par fournisseur
    fig_fournisseurs = px.pie(
        fournisseur_sum, 
        values='Dépenses Additionnelles', 
        names='Fournisseur',
        title="Répartition des dépenses additionnelles par fournisseur",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig_fournisseurs, use_container_width=True)
else:
    st.error("Impossible de charger les données. Vérifiez que le fichier CSV est présent dans le dossier de l'application.")