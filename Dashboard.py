# dashboard_iran_communes.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import time
import json
import warnings
import io
import base64
from PIL import Image
import requests
from io import BytesIO
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Financier - Communes d'Iran",
    page_icon="🇮🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé avec influences persanes
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade:wght@400;700&family=Roboto:wght@300;400;700&display=swap');
    
    .main-header {
        font-size: 2.5rem;
        color: #239F40;
        text-align: center;
        margin-bottom: 1rem;
        font-family: 'Scheherazade', serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(135deg, #239F40 0%, #FFFFFF 50%, #DA0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .persian-header {
        font-family: 'Scheherazade', serif;
        font-size: 2rem;
        direction: rtl;
        text-align: center;
        color: #333;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid #239F40;
        transition: transform 0.3s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #239F40;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .iran-badge {
        background-color: #239F40;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .sanction-badge {
        background-color: #DA0000;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .oil-badge {
        background-color: #FF6B35;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #239F40 !important;
        color: white !important;
    }
    
    .flag-icon {
        font-size: 2rem;
        margin-right: 0.5rem;
    }
    
    .financial-positive {
        color: #239F40;
        font-weight: bold;
    }
    
    .financial-negative {
        color: #DA0000;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des variables de session
if 'selected_commune' not in st.session_state:
    st.session_state.selected_commune = "Téhéran"

if 'comparison_mode' not in st.session_state:
    st.session_state.comparison_mode = False

if 'comparison_communes' not in st.session_state:
    st.session_state.comparison_communes = []

if 'show_euro_conversion' not in st.session_state:
    st.session_state.show_euro_conversion = True

if 'show_toman' not in st.session_state:
    st.session_state.show_toman = True

# Import de la classe IranCommuneFinanceAnalyzer depuis votre script
# Pour éviter les répétitions, nous allons intégrer une version adaptée ici

class IranCommuneFinanceAnalyzer:
    def __init__(self, commune_name):
        self.commune = commune_name
        self.colors = ['#008000', '#FFFFFF', '#FF0000', '#FF6B6B', '#4ECDC4', 
                      '#45B7D1', '#F9A602', '#6A0572', '#AB83A1', '#2A9D8F']
        
        self.start_year = 2002
        self.end_year = 2025
        
        # Conversion rial (1€ ≈ 50,000 rials environ - taux approximatif)
        self.eur_to_irr = 50000
        
        # Configuration spécifique à chaque commune iranienne
        self.config = self._get_commune_config()
        
    def _get_commune_config(self):
        """Retourne la configuration spécifique pour chaque commune iranienne"""
        configs = {
            "Téhéran": {
                "population_base": 8500000,
                "budget_base": 120000,  # en milliards de rials
                "type": "capitale",
                "specialites": ["administration", "industrie", "commerce", "education", "culture"],
                "description": "Capitale politique et économique, plus grande ville d'Iran",
                "superficie": 730,
                "densite": 11600,
                "maire": "Alireza Zakani",
                "site_web": "tehran.ir"
            },
            "Mashhad": {
                "population_base": 3200000,
                "budget_base": 45000,
                "type": "religieuse",
                "specialites": ["tourisme_religieux", "commerce", "education", "sante"],
                "description": "Deuxième ville d'Iran, centre religieux majeur avec le sanctuaire de l'Imam Reza",
                "superficie": 351,
                "densite": 9100,
                "maire": "Mohammadreza Qalibaf",
                "site_web": "mashhad.ir"
            },
            "Ispahan": {
                "population_base": 2200000,
                "budget_base": 38000,
                "type": "touristique",
                "specialites": ["patrimoine", "tourisme", "industrie", "artisanat"],
                "description": "Capitale culturelle et historique, célèbre pour son architecture islamique",
                "superficie": 551,
                "densite": 4000,
                "maire": "Ali Qasemzadeh",
                "site_web": "isfahan.ir"
            },
            "Karaj": {
                "population_base": 1900000,
                "budget_base": 28000,
                "type": "industrielle",
                "specialites": ["industrie", "agriculture", "commerce", "logistique"],
                "description": "Ville industrielle majeure, banlieue de Téhéran",
                "superficie": 162,
                "densite": 11700,
                "maire": "Ali Rezaei",
                "site_web": "karaj.ir"
            },
            "Tabriz": {
                "population_base": 1800000,
                "budget_base": 32000,
                "type": "commerciale",
                "specialites": ["commerce", "industrie", "artisanat", "agriculture"],
                "description": "Capitale de l'Azerbaïdjan oriental, centre commercial historique",
                "superficie": 324,
                "densite": 5500,
                "maire": "Iraj Shahin Bakht",
                "site_web": "tabriz.ir"
            },
            "Chiraz": {
                "population_base": 1700000,
                "budget_base": 29000,
                "type": "culturelle",
                "specialites": ["tourisme", "poesie", "patrimoine", "agriculture"],
                "description": "Ville de poésie, de jardins et de culture persane",
                "superficie": 240,
                "densite": 7100,
                "maire": "Heidar Eskandarpour",
                "site_web": "shiraz.ir"
            },
            "Qom": {
                "population_base": 1300000,
                "budget_base": 22000,
                "type": "religieuse",
                "specialites": ["theologie", "education_religieuse", "tourisme_pelerinage"],
                "description": "Centre mondial du chiisme, ville sainte",
                "superficie": 123,
                "densite": 10500,
                "maire": "Seyed Morteza Saghaeiannejad",
                "site_web": "qom.ir"
            },
            "Ahvaz": {
                "population_base": 1200000,
                "budget_base": 35000,
                "type": "petroliere",
                "specialites": ["petrole", "gaz", "industrie_lourde", "agriculture"],
                "description": "Capitale de l'industrie pétrolière iranienne",
                "superficie": 185,
                "densite": 6500,
                "maire": "Mousa Shana'ati",
                "site_web": "ahvaz.ir"
            },
            "Kerman": {
                "population_base": 800000,
                "budget_base": 15000,
                "type": "miniere",
                "specialites": ["mines", "agriculture", "tourisme", "artisanat"],
                "description": "Centre minier et industriel, célèbre pour ses tapis",
                "superficie": 240,
                "densite": 3300,
                "maire": "Seyed Morteza Saghaeiannejad",
                "site_web": "kerman.ir"
            },
            "Orumiyeh": {
                "population_base": 750000,
                "budget_base": 12000,
                "type": "agricole",
                "specialites": ["agriculture", "elevage", "commerce_frontalier"],
                "description": "Capitale de l'Azerbaïdjan occidental, région agricole fertile",
                "superficie": 175,
                "densite": 4300,
                "maire": "Hossein Mehraban",
                "site_web": "urmia.ir"
            },
            "Rasht": {
                "population_base": 700000,
                "budget_base": 11000,
                "type": "agricole",
                "specialites": ["riz", "the", "agriculture", "tourisme_vert"],
                "description": "Capitale du Gilan, région subtropicale, centre agricole",
                "superficie": 180,
                "densite": 3900,
                "maire": "Ali Bahar",
                "site_web": "rasht.ir"
            },
            "Yazd": {
                "population_base": 650000,
                "budget_base": 10000,
                "type": "desertique",
                "specialites": ["tourisme", "artisanat", "technologie_desert"],
                "description": "Ville du désert, patrimoine mondial de l'UNESCO",
                "superficie": 240,
                "densite": 2700,
                "maire": "Mehdi Jamalinejad",
                "site_web": "yazd.ir"
            },
            # Configuration par défaut
            "default": {
                "population_base": 300000,
                "budget_base": 5000,
                "type": "locale",
                "specialites": ["agriculture", "commerce_local", "artisanat"],
                "description": "Commune locale typique",
                "superficie": 100,
                "densite": 3000,
                "maire": "Non disponible",
                "site_web": "Non disponible"
            }
        }
        
        return configs.get(self.commune, configs["default"])
    
    def _convert_to_rials(self, amount_eur):
        """Convertit un montant d'euros en rials iraniens"""
        return amount_eur * self.eur_to_irr
    
    def generate_financial_data(self):
        """Génère des données financières pour la commune iranienne"""
        # Créer une base de données annuelle
        dates = pd.date_range(start=f'{self.start_year}-01-01', 
                             end=f'{self.end_year}-12-31', freq='Y')
        
        data = {'Annee': [date.year for date in dates]}
        
        # Données démographiques (croissance iranienne typique)
        data['Population'] = self._simulate_population(dates)
        data['Menages'] = self._simulate_households(dates)
        
        # Recettes communales en rials
        data['Recettes_Totales'] = self._simulate_total_revenue(dates)
        data['Impots_Locaux'] = self._simulate_tax_revenue(dates)
        data['Subventions_Gouvernement'] = self._simulate_government_grants(dates)
        data['Revenus_Petroliers'] = self._simulate_oil_revenue(dates)
        data['Autres_Recettes'] = self._simulate_other_revenue(dates)
        
        # Dépenses communales en rials
        data['Depenses_Totales'] = self._simulate_total_expenses(dates)
        data['Fonctionnement'] = self._simulate_operating_expenses(dates)
        data['Investissement'] = self._simulate_investment_expenses(dates)
        data['Charge_Dette'] = self._simulate_debt_charges(dates)
        data['Personnel'] = self._simulate_staff_costs(dates)
        data['Subventions_Energie'] = self._simulate_energy_subsidies(dates)
        
        # Indicateurs financiers
        data['Epargne_Brute'] = self._simulate_gross_savings(dates)
        data['Dette_Totale'] = self._simulate_total_debt(dates)
        data['Taux_Endettement'] = self._simulate_debt_ratio(dates)
        data['Taux_Fiscalite'] = self._simulate_tax_rate(dates)
        data['Inflation'] = self._simulate_inflation(dates)
        
        # Investissements spécifiques adaptés à l'Iran
        data['Investissement_Petrole_Gaz'] = self._simulate_oil_gas_investment(dates)
        data['Investissement_Agriculture'] = self._simulate_agriculture_investment(dates)
        data['Investissement_Transport'] = self._simulate_transport_investment(dates)
        data['Investissement_Education'] = self._simulate_education_investment(dates)
        data['Investissement_Sante'] = self._simulate_health_investment(dates)
        data['Investissement_Industrie'] = self._simulate_industry_investment(dates)
        data['Investissement_Culture'] = self._simulate_culture_investment(dates)
        
        df = pd.DataFrame(data)
        
        # Ajouter des tendances spécifiques à la commune iranienne
        self._add_iranian_trends(df)
        
        return df
    
    def _simulate_population(self, dates):
        """Simule la population de la commune (croissance iranienne typique)"""
        base_population = self.config["population_base"]
        
        population = []
        for i, date in enumerate(dates):
            # Croissance démographique iranienne (élevée mais en diminution)
            if self.config["type"] == "capitale":
                growth_rate = 0.016  # Croissance modérée à Téhéran
            elif self.config["type"] in ["religieuse", "touristique"]:
                growth_rate = 0.020  # Croissance forte dans les villes religieuses
            else:
                growth_rate = 0.018  # Croissance moyenne
                
            # Réduction progressive de la croissance démographique
            if date.year > 2010:
                growth_rate *= 0.8
            if date.year > 2020:
                growth_rate *= 0.7
                
            growth = 1 + growth_rate * i
            population.append(base_population * growth)
        
        return population
    
    def _simulate_households(self, dates):
        """Simule le nombre de ménages (taille moyenne plus grande en Iran)"""
        base_households = self.config["population_base"] / 4.0  # Taille des ménages plus grande
        
        households = []
        for i, date in enumerate(dates):
            growth = 1 + 0.015 * i
            households.append(base_households * growth)
        
        return households
    
    def _simulate_total_revenue(self, dates):
        """Simule les recettes totales de la commune en rials"""
        base_revenue = self._convert_to_rials(self.config["budget_base"])
        
        revenue = []
        for i, date in enumerate(dates):
            # Croissance économique iranienne (impactée par les sanctions)
            if self.config["type"] == "petroliere":
                growth_rate = 0.025  # Forte volatilité dans les régions pétrolières
            elif self.config["type"] == "capitale":
                growth_rate = 0.022  # Croissance modérée à Téhéran
            else:
                growth_rate = 0.018  # Croissance faible ailleurs
                
            growth = 1 + growth_rate * i
            noise = np.random.normal(1, 0.12)  # Forte volatilité due aux sanctions
            revenue.append(base_revenue * growth * noise)
        
        return revenue
    
    def _simulate_tax_revenue(self, dates):
        """Simule les recettes fiscales en rials"""
        base_tax = self._convert_to_rials(self.config["budget_base"] * 0.25)  # Faible taxation
        
        tax_revenue = []
        for i, date in enumerate(dates):
            growth = 1 + 0.015 * i
            noise = np.random.normal(1, 0.10)
            tax_revenue.append(base_tax * growth * noise)
        
        return tax_revenue
    
    def _simulate_government_grants(self, dates):
        """Simule les subventions gouvernementales (importantes en Iran)"""
        base_grants = self._convert_to_rials(self.config["budget_base"] * 0.40)
        
        grants = []
        for i, date in enumerate(dates):
            year = date.year
            # Augmentation des subventions pendant les périodes de sanctions
            if year >= 2012:
                increase = 1 + 0.012 * (year - 2012)
            else:
                increase = 1
            
            noise = np.random.normal(1, 0.08)
            grants.append(base_grants * increase * noise)
        
        return grants
    
    def _simulate_oil_revenue(self, dates):
        """Simule les revenus pétroliers (spécifique à l'Iran)"""
        base_oil = self._convert_to_rials(self.config["budget_base"] * 0.20)
        
        oil_revenue = []
        for i, date in enumerate(dates):
            year = date.year
            # Forte volatilité due aux sanctions et prix du pétrole
            if year <= 2005:
                multiplier = 1.0
            elif 2006 <= year <= 2011:
                multiplier = 1.4  # Prix du pétrole élevés
            elif 2012 <= year <= 2015:
                multiplier = 0.6  # Sanctions renforcées
            elif 2016 <= year <= 2017:
                multiplier = 1.2  # Levée partielle des sanctions
            elif 2018 <= year <= 2020:
                multiplier = 0.5  # Sanctions maximales
            else:
                multiplier = 0.8  # Adaptation progressive
            
            growth = 1 + 0.010 * i
            noise = np.random.normal(1, 0.25)  # Très forte volatilité
            oil_revenue.append(base_oil * growth * multiplier * noise)
        
        return oil_revenue
    
    def _simulate_other_revenue(self, dates):
        """Simule les autres recettes en rials"""
        base_other = self._convert_to_rials(self.config["budget_base"] * 0.15)
        
        other_revenue = []
        for i, date in enumerate(dates):
            growth = 1 + 0.020 * i
            noise = np.random.normal(1, 0.15)
            other_revenue.append(base_other * growth * noise)
        
        return other_revenue
    
    def _simulate_total_expenses(self, dates):
        """Simule les dépenses totales en rials"""
        base_expenses = self._convert_to_rials(self.config["budget_base"] * 0.98)
        
        expenses = []
        for i, date in enumerate(dates):
            growth = 1 + 0.025 * i  # Croissance élevée due à l'inflation
            noise = np.random.normal(1, 0.10)
            expenses.append(base_expenses * growth * noise)
        
        return expenses
    
    def _simulate_operating_expenses(self, dates):
        """Simule les dépenses de fonctionnement en rials"""
        base_operating = self._convert_to_rials(self.config["budget_base"] * 0.55)
        
        operating = []
        for i, date in enumerate(dates):
            growth = 1 + 0.024 * i
            noise = np.random.normal(1, 0.08)
            operating.append(base_operating * growth * noise)
        
        return operating
    
    def _simulate_investment_expenses(self, dates):
        """Simule les dépenses d'investissement en rials"""
        base_investment = self._convert_to_rials(self.config["budget_base"] * 0.43)
        
        investment = []
        for i, date in enumerate(dates):
            year = date.year
            # Plans d'investissement affectés par les sanctions
            if year in [2005, 2011, 2017, 2022]:
                multiplier = 1.5
            elif year in [2008, 2013, 2019]:
                multiplier = 0.7
            else:
                multiplier = 1.0
            
            growth = 1 + 0.020 * i
            noise = np.random.normal(1, 0.20)
            investment.append(base_investment * growth * multiplier * noise)
        
        return investment
    
    def _simulate_debt_charges(self, dates):
        """Simule les charges de la dette en rials"""
        base_debt_charge = self._convert_to_rials(self.config["budget_base"] * 0.08)
        
        debt_charges = []
        for i, date in enumerate(dates):
            year = date.year
            if year >= 2005:
                increase = 1 + 0.015 * (year - 2005)  # Augmentation forte due aux difficultés
            else:
                increase = 1
            
            noise = np.random.normal(1, 0.12)
            debt_charges.append(base_debt_charge * increase * noise)
        
        return debt_charges
    
    def _simulate_staff_costs(self, dates):
        """Simule les dépenses de personnel en rials"""
        base_staff = self._convert_to_rials(self.config["budget_base"] * 0.38)
        
        staff_costs = []
        for i, date in enumerate(dates):
            growth = 1 + 0.026 * i  # Croissance forte due à l'inflation
            noise = np.random.normal(1, 0.06)
            staff_costs.append(base_staff * growth * noise)
        
        return staff_costs
    
    def _simulate_energy_subsidies(self, dates):
        """Simule les subventions énergétiques (spécifique à l'Iran)"""
        base_subsidies = self._convert_to_rials(self.config["budget_base"] * 0.12)
        
        subsidies = []
        for i, date in enumerate(dates):
            year = date.year
            # Réforme des subventions énergétiques
            if year <= 2010:
                multiplier = 1.0
            elif 2011 <= year <= 2014:
                multiplier = 0.7  # Début de réforme
            else:
                multiplier = 0.5  # Réduction progressive
            
            growth = 1 + 0.008 * i
            noise = np.random.normal(1, 0.18)
            subsidies.append(base_subsidies * growth * multiplier * noise)
        
        return subsidies
    
    def _simulate_gross_savings(self, dates):
        """Simule l'épargne brute en rials"""
        savings = []
        for i, date in enumerate(dates):
            base_saving = self._convert_to_rials(self.config["budget_base"] * 0.02)  # Faible épargne
            
            year = date.year
            if year >= 2010:
                improvement = 1 + 0.005 * (year - 2010)  # Amélioration très lente
            else:
                improvement = 1
            
            noise = np.random.normal(1, 0.20)  # Forte volatilité
            savings.append(base_saving * improvement * noise)
        
        return savings
    
    def _simulate_total_debt(self, dates):
        """Simule la dette totale en rials"""
        base_debt = self._convert_to_rials(self.config["budget_base"] * 0.85)
        
        debt = []
        for i, date in enumerate(dates):
            year = date.year
            if year in [2006, 2012, 2018, 2023]:
                change = 1.25  # Forte augmentation pendant les crises
            elif year in [2009, 2015, 2021]:
                change = 0.90  # Légère réduction
            else:
                change = 1.05  # Croissance constante
            
            noise = np.random.normal(1, 0.15)
            debt.append(base_debt * change * noise)
        
        return debt
    
    def _simulate_debt_ratio(self, dates):
        """Simule le taux d'endettement"""
        ratios = []
        for i, date in enumerate(dates):
            base_ratio = 0.78  # Endettement initial élevé
            
            year = date.year
            if year >= 2010:
                improvement = 1 - 0.008 * (year - 2010)  # Amélioration lente
            else:
                improvement = 1
            
            noise = np.random.normal(1, 0.10)
            ratios.append(base_ratio * improvement * noise)
        
        return ratios
    
    def _simulate_tax_rate(self, dates):
        """Simule le taux de fiscalité (faible en Iran)"""
        rates = []
        for i, date in enumerate(dates):
            base_rate = 0.65  # Fiscalité initiale faible
            
            year = date.year
            if year >= 2010:
                increase = 1 + 0.004 * (year - 2010)  # Augmentation très lente
            else:
                increase = 1
            
            noise = np.random.normal(1, 0.05)
            rates.append(base_rate * increase * noise)
        
        return rates
    
    def _simulate_inflation(self, dates):
        """Simule le taux d'inflation (élevé en Iran)"""
        inflation_rates = []
        for i, date in enumerate(dates):
            year = date.year
            
            if year <= 2005:
                rate = 0.15  # Inflation modérée
            elif 2006 <= year <= 2011:
                rate = 0.25  # Inflation élevée
            elif 2012 <= year <= 2015:
                rate = 0.35  # Inflation très élevée (sanctions)
            elif 2016 <= year <= 2017:
                rate = 0.10  # Désinflation temporaire
            elif 2018 <= year <= 2020:
                rate = 0.40  # Hyperinflation
            else:
                rate = 0.30  # Inflation élevée persistante
            
            noise = np.random.normal(1, 0.08)
            inflation_rates.append(rate * noise)
        
        return inflation_rates
    
    def _simulate_oil_gas_investment(self, dates):
        """Simule l'investissement pétrole et gaz (spécifique à l'Iran)"""
        base_investment = self._convert_to_rials(self.config["budget_base"] * 0.15)
        
        # Ajustement selon les spécialités
        multiplier = 2.0 if "petrole" in self.config["specialites"] else 0.5
        
        investment = []
        for i, date in enumerate(dates):
            year = date.year
            if year in [2005, 2011, 2017, 2022]:
                year_multiplier = 1.8
            else:
                year_multiplier = 1.0
            
            growth = 1 + 0.018 * i
            noise = np.random.normal(1, 0.22)  # Très forte volatilité
            investment.append(base_investment * growth * year_multiplier * multiplier * noise)
        
        return investment
    
    def _simulate_agriculture_investment(self, dates):
        """Simule l'investissement agricole"""
        base_investment = self._convert_to_rials(self.config["budget_base"] * 0.08)
        
        # Ajustement selon les spécialités
        multiplier = 1.6 if "agriculture" in self.config["specialites"] else 0.9
        
        investment = []
        for i, date in enumerate(dates):
            year = date.year
            if year in [2006, 2012, 2018, 2023]:
                year_multiplier = 1.7
            else:
                year_multiplier = 1.0
            
            growth = 1 + 0.022 * i
            noise = np.random.normal(1, 0.16)
            investment.append(base_investment * growth * year_multiplier * multiplier * noise)
        
        return investment
    
    def _simulate_transport_investment(self, dates):
        """Simule l'investissement en transport"""
        base_investment = self._convert_to_rials(self.config["budget_base"] * 0.06)
        
        # Ajustement selon les spécialités
        multiplier = 1.4 if "transport" in self.config["specialites"] else 1.0
        
        investment = []
        for i, date in enumerate(dates):
            year = date.year
            if year in [2007, 2013, 2019, 2024]:
                year_multiplier = 1.6
            else:
                year_multiplier = 1.0
            
            growth = 1 + 0.020 * i
            noise = np.random.normal(1, 0.18)
            investment.append(base_investment * growth * year_multiplier * multiplier * noise)
        
        return investment
    
    def _simulate_education_investment(self, dates):
        """Simule l'investissement éducatif"""
        base_investment = self._convert_to_rials(self.config["budget_base"] * 0.07)
        
        # Ajustement selon les spécialités
        multiplier = 1.5 if "education" in self.config["specialites"] else 1.0
        
        investment = []
        for i, date in enumerate(dates):
            year = date.year
            if year in [2008, 2014, 2020]:
                year_multiplier = 1.5
            else:
                year_multiplier = 1.0
            
            growth = 1 + 0.019 * i
            noise = np.random.normal(1, 0.15)
            investment.append(base_investment * growth * year_multiplier * multiplier * noise)
        
        return investment
    
    def _simulate_health_investment(self, dates):
        """Simule l'investissement en santé"""
        base_investment = self._convert_to_rials(self.config["budget_base"] * 0.05)
        
        # Ajustement selon les spécialités
        multiplier = 1.4 if "sante" in self.config["specialites"] else 1.0
        
        investment = []
        for i, date in enumerate(dates):
            year = date.year
            if year in [2009, 2015, 2021]:
                year_multiplier = 1.7
            else:
                year_multiplier = 1.0
            
            growth = 1 + 0.021 * i
            noise = np.random.normal(1, 0.17)
            investment.append(base_investment * growth * year_multiplier * multiplier * noise)
        
        return investment
    
    def _simulate_industry_investment(self, dates):
        """Simule l'investissement industriel"""
        base_investment = self._convert_to_rials(self.config["budget_base"] * 0.09)
        
        # Ajustement selon les spécialités
        multiplier = 1.7 if "industrie" in self.config["specialites"] else 0.8
        
        investment = []
        for i, date in enumerate(dates):
            year = date.year
            if year in [2010, 2016, 2022]:
                year_multiplier = 1.8
            else:
                year_multiplier = 1.0
            
            growth = 1 + 0.017 * i
            noise = np.random.normal(1, 0.19)
            investment.append(base_investment * growth * year_multiplier * multiplier * noise)
        
        return investment
    
    def _simulate_culture_investment(self, dates):
        """Simule l'investissement culturel"""
        base_investment = self._convert_to_rials(self.config["budget_base"] * 0.03)
        
        # Ajustement selon les spécialités
        multiplier = 1.8 if "culture" in self.config["specialites"] else 0.7
        
        investment = []
        for i, date in enumerate(dates):
            year = date.year
            if year in [2011, 2017, 2023]:
                year_multiplier = 1.9
            else:
                year_multiplier = 1.0
            
            growth = 1 + 0.016 * i
            noise = np.random.normal(1, 0.14)
            investment.append(base_investment * growth * year_multiplier * multiplier * noise)
        
        return investment
    
    def _add_iranian_trends(self, df):
        """Ajoute des tendances municipales réalistes adaptées à l'Iran"""
        for i, row in df.iterrows():
            year = row['Annee']
            
            # Boom pétrolier (2002-2005)
            if 2002 <= year <= 2005:
                df.loc[i, 'Revenus_Petroliers'] *= 1.4
                df.loc[i, 'Investissement_Petrole_Gaz'] *= 1.6
            
            # Premières sanctions (2006-2007)
            if 2006 <= year <= 2007:
                df.loc[i, 'Revenus_Petroliers'] *= 0.8
                df.loc[i, 'Investissement'] *= 0.9
            
            # Crise financière mondiale (2008-2009) - impact modéré
            if 2008 <= year <= 2009:
                df.loc[i, 'Recettes_Totales'] *= 0.95
                df.loc[i, 'Revenus_Petroliers'] *= 0.7
            
            # Sanctions renforcées (2012-2015)
            if 2012 <= year <= 2015:
                df.loc[i, 'Revenus_Petroliers'] *= 0.4
                df.loc[i, 'Subventions_Gouvernement'] *= 1.3
                df.loc[i, 'Inflation'] *= 1.8
            
            # Accord nucléaire (2016-2017)
            if 2016 <= year <= 2017:
                df.loc[i, 'Revenus_Petroliers'] *= 1.8
                df.loc[i, 'Investissement_Etranger'] = df.loc[i, 'Investissement'] * 0.15
                df.loc[i, 'Inflation'] *= 0.6
            
            # Retrait américain et sanctions maximales (2018-2020)
            if 2018 <= year <= 2020:
                df.loc[i, 'Revenus_Petroliers'] *= 0.3
                df.loc[i, 'Subventions_Gouvernement'] *= 1.5
                df.loc[i, 'Inflation'] *= 2.5
                df.loc[i, 'Investissement_Industrie'] *= 0.7
            
            # Adaptation et résilience (2021-2025)
            if year >= 2021:
                df.loc[i, 'Investissement_Agriculture'] *= 1.3
                df.loc[i, 'Investissement_Industrie'] *= 1.2
                df.loc[i, 'Subventions_Energie'] *= 0.8

# Fonctions utilitaires pour le dashboard
def format_rial(value, include_toman=True, decimals=2):
    """Formate une valeur en Rial iranien"""
    if value is None or value == 0:
        return "N/A"
    
    # Déterminer l'unité appropriée
    if value >= 1e12:
        unit = "Billion"
        rial_str = f"{value/1e12:.{decimals}f}"
    elif value >= 1e9:
        unit = "Milliard"
        rial_str = f"{value/1e9:.{decimals}f}"
    elif value >= 1e6:
        unit = "Million"
        rial_str = f"{value/1e6:.{decimals}f}"
    else:
        unit = ""
        rial_str = f"{value:.{decimals}f}"
    
    # Ajouter le suffixe approprié
    if unit:
        result = f"{rial_str} {unit} Rial"
    else:
        result = f"{rial_str} Rial"
    
    # Option Toman (1 Toman = 10 Rials)
    if include_toman and value >= 1000:
        toman = value / 10
        if toman >= 1e12:
            result += f" ({toman/1e12:.{decimals}f} Billion Toman)"
        elif toman >= 1e9:
            result += f" ({toman/1e9:.{decimals}f} Milliard Toman)"
        elif toman >= 1e6:
            result += f" ({toman/1e6:.{decimals}f} Million Toman)"
        else:
            result += f" ({toman:.{decimals}f} Toman)"
    
    return result

def format_euro(value, eur_to_irr=50000):
    """Convertit des Rials en Euros et formate"""
    if value is None or value == 0:
        return "N/A"
    
    euros = value / eur_to_irr
    
    if euros >= 1e9:
        return f"{euros/1e9:.2f} Md€"
    elif euros >= 1e6:
        return f"{euros/1e6:.2f} M€"
    elif euros >= 1000:
        return f"{euros/1000:.2f} K€"
    else:
        return f"{euros:.2f} €"

def get_commune_flag_emoji(commune):
    """Retourne un emoji représentatif pour la commune"""
    flags = {
        "Téhéran": "🏛️",
        "Mashhad": "🕌",
        "Ispahan": "🎨",
        "Karaj": "🏭",
        "Tabriz": "🏺",
        "Chiraz": "🌸",
        "Qom": "📿",
        "Ahvaz": "🛢️",
        "Kerman": "🧶",
        "Orumiyeh": "🌾",
        "Rasht": "🌿",
        "Yazd": "🏜️",
        "default": "🏘️"
    }
    return flags.get(commune, flags["default"])

def get_color_for_value(value, threshold=0):
    """Retourne une classe CSS basée sur la valeur"""
    if value > threshold:
        return "financial-positive"
    else:
        return "financial-negative"

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/c/ca/Flag_of_Iran.svg", width=100)
    st.markdown("<h2 style='text-align: center;'>🇮🇷 Dashboard Iran</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Liste complète des communes iraniennes
    communes_iran = [
        "Téhéran", "Mashhad", "Ispahan", "Karaj", "Tabriz", "Chiraz", "Qom",
        "Ahvaz", "Kerman", "Orumiyeh", "Rasht", "Yazd", "Ardabil", "Zahédan",
        "Kermanshah", "Hamadan", "Bandar Abbas", "Arak", "Eslamshahr", "Zahedan"
    ]
    
    # Mode de sélection
    selection_mode = st.radio(
        "Mode de visualisation",
        ["🏙️ Commune unique", "🔄 Comparaison multiple"]
    )
    
    if selection_mode == "🏙️ Commune unique":
        st.session_state.comparison_mode = False
        selected_commune = st.selectbox(
            "Sélectionner une commune",
            options=communes_iran,
            index=communes_iran.index(st.session_state.selected_commune) if st.session_state.selected_commune in communes_iran else 0
        )
        st.session_state.selected_commune = selected_commune
    else:
        st.session_state.comparison_mode = True
        selected_communes = st.multiselect(
            "Sélectionner jusqu'à 5 communes à comparer",
            options=communes_iran,
            default=["Téhéran", "Mashhad", "Ispahan"]
        )
        if len(selected_communes) > 5:
            st.warning("Maximum 5 communes pour la comparaison")
            selected_communes = selected_communes[:5]
        st.session_state.comparison_communes = selected_communes
    
    st.markdown("---")
    
    # Options d'affichage
    st.markdown("### ⚙️ Options d'affichage")
    
    st.session_state.show_euro_conversion = st.checkbox(
        "Afficher conversion en Euro",
        value=st.session_state.show_euro_conversion
    )
    
    st.session_state.show_toman = st.checkbox(
        "Afficher conversion en Toman",
        value=st.session_state.show_toman
    )
    
    eur_to_irr = st.number_input(
        "Taux de change 1€ = ? Rial",
        min_value=10000,
        max_value=200000,
        value=50000,
        step=5000
    )
    
    st.markdown("---")
    
    # Période d'analyse
    st.markdown("### 📅 Période d'analyse")
    start_year = st.slider(
        "Année de début",
        min_value=2002,
        max_value=2025,
        value=2002
    )
    end_year = st.slider(
        "Année de fin",
        min_value=2002,
        max_value=2025,
        value=2025
    )
    
    st.markdown("---")
    
    # Export des données
    st.markdown("### 📥 Export")
    if st.button("📊 Exporter les données actuelles"):
        st.success("Export simulé - Fonctionnalité à implémenter")
    
    st.markdown("---")
    st.caption("Données simulées - Iran (2002-2025)")
    st.caption("Taux de change: 1€ ≈ 50,000 Rials")

# Main content
st.markdown("<h1 class='main-header'>🇮🇷 Analyse Financière des Communes d'Iran</h1>", unsafe_allow_html=True)
st.markdown("<p class='persian-header'>تحلیل مالی شهرداری‌های ایران</p>", unsafe_allow_html=True)

# Badges contextuels
col_badges1, col_badges2, col_badges3, col_badges4 = st.columns(4)
with col_badges1:
    st.markdown("<span class='iran-badge'>🇮🇷 31 Provinces</span>", unsafe_allow_html=True)
with col_badges2:
    st.markdown("<span class='sanction-badge'>⚠️ Sous Sanctions</span>", unsafe_allow_html=True)
with col_badges3:
    st.markdown("<span class='oil-badge'>🛢️ OPEC</span>", unsafe_allow_html=True)
with col_badges4:
    st.markdown("<span class='iran-badge'>📈 Inflation >40%</span>", unsafe_allow_html=True)

# Mode comparaison ou commune unique
if not st.session_state.comparison_mode:
    # Commande unique
    with st.spinner(f"Génération des données pour {st.session_state.selected_commune}..."):
        analyzer = IranCommuneFinanceAnalyzer(st.session_state.selected_commune)
        df = analyzer.generate_financial_data()
        
        # Filtrer par année
        df = df[(df['Annee'] >= start_year) & (df['Annee'] <= end_year)]
        
        # Informations sur la commune
        st.markdown(f"## {get_commune_flag_emoji(st.session_state.selected_commune)} {st.session_state.selected_commune}")
        
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            st.markdown("**Type:**")
            st.info(analyzer.config['type'].capitalize())
        
        with col_info2:
            st.markdown("**Spécialités:**")
            st.info(", ".join(analyzer.config['specialites'][:3]))
        
        with col_info3:
            st.markdown("**Population (2025):**")
            pop_2025 = df[df['Annee'] == 2025]['Population'].values[0] if 2025 in df['Annee'].values else analyzer.config['population_base']
            st.metric("Population", f"{pop_2025:,.0f}")
        
        with col_info4:
            st.markdown("**Densité:**")
            densite = analyzer.config.get('densite', 0)
            st.metric("hab/km²", f"{densite:,.0f}")
        
        # KPIs principaux
        st.markdown("### 📊 Indicateurs Clés")
        
        last_year_data = df[df['Annee'] == df['Annee'].max()].iloc[0] if not df.empty else None
        
        if last_year_data is not None:
            col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
            
            with col_kpi1:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>{format_rial(last_year_data['Recettes_Totales'], st.session_state.show_toman, 1)}</div>", unsafe_allow_html=True)
                st.markdown("<div class='metric-label'>Recettes totales</div>", unsafe_allow_html=True)
                if st.session_state.show_euro_conversion:
                    st.caption(f"≈ {format_euro(last_year_data['Recettes_Totales'], eur_to_irr)}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_kpi2:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>{format_rial(last_year_data['Depenses_Totales'], st.session_state.show_toman, 1)}</div>", unsafe_allow_html=True)
                st.markdown("<div class='metric-label'>Dépenses totales</div>", unsafe_allow_html=True)
                if st.session_state.show_euro_conversion:
                    st.caption(f"≈ {format_euro(last_year_data['Depenses_Totales'], eur_to_irr)}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_kpi3:
                solde = last_year_data['Recettes_Totales'] - last_year_data['Depenses_Totales']
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value {get_color_for_value(solde, 0)}'>{format_rial(solde, st.session_state.show_toman, 1)}</div>", unsafe_allow_html=True)
                st.markdown("<div class='metric-label'>Solde budgétaire</div>", unsafe_allow_html=True)
                if st.session_state.show_euro_conversion:
                    st.caption(f"≈ {format_euro(solde, eur_to_irr)}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_kpi4:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>{last_year_data['Taux_Endettement']*100:.1f}%</div>", unsafe_allow_html=True)
                st.markdown("<div class='metric-label'>Taux d'endettement</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_kpi5:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-value'>{last_year_data['Inflation']*100:.1f}%</div>", unsafe_allow_html=True)
                st.markdown("<div class='metric-label'>Inflation</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Onglets principaux
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Vue d'ensemble", 
            "💰 Recettes", 
            "💸 Dépenses", 
            "📊 Investissements",
            "📉 Dette & Inflation",
            "🧠 Insights"
        ])
        
        with tab1:
            st.markdown("### 📈 Évolution des Recettes et Dépenses")
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Scatter(x=df['Annee'], y=df['Recettes_Totales']/1e9,
                          name="Recettes", line=dict(color='#239F40', width=3)),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(x=df['Annee'], y=df['Depenses_Totales']/1e9,
                          name="Dépenses", line=dict(color='#DA0000', width=3)),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Bar(x=df['Annee'], y=df['Epargne_Brute']/1e9,
                       name="Épargne Brute", marker_color='#FFA500', opacity=0.5),
                secondary_y=True
            )
            
            fig.update_layout(
                title=f"Évolution budgétaire - {st.session_state.selected_commune}",
                xaxis_title="Année",
                hovermode='x unified',
                template='plotly_white',
                height=500
            )
            
            fig.update_yaxes(title_text="Milliards de Rials", secondary_y=False)
            fig.update_yaxes(title_text="Milliards de Rials (Épargne)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Évolution démographique
            st.markdown("### 👥 Évolution Démographique")
            
            fig_demo = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_demo.add_trace(
                go.Scatter(x=df['Annee'], y=df['Population'],
                          name="Population", line=dict(color='#239F40', width=3), fill='tozeroy'),
                secondary_y=False
            )
            
            fig_demo.add_trace(
                go.Scatter(x=df['Annee'], y=df['Menages'],
                          name="Ménages", line=dict(color='#DA0000', width=2)),
                secondary_y=True
            )
            
            fig_demo.update_layout(
                title="Évolution de la population et des ménages",
                xaxis_title="Année",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            fig_demo.update_yaxes(title_text="Population", secondary_y=False)
            fig_demo.update_yaxes(title_text="Ménages", secondary_y=True)
            
            st.plotly_chart(fig_demo, use_container_width=True)
        
        with tab2:
            st.markdown("### 💰 Structure des Recettes")
            
            # Graphique en barres empilées
            fig_recettes = go.Figure()
            
            categories = ['Impots_Locaux', 'Subventions_Gouvernement', 'Revenus_Petroliers', 'Autres_Recettes']
            labels = ['Impôts Locaux', 'Subventions', 'Revenus Pétroliers', 'Autres']
            colors = ['#239F40', '#FFFFFF', '#DA0000', '#FFA500']
            
            for i, cat in enumerate(categories):
                fig_recettes.add_trace(go.Bar(
                    x=df['Annee'],
                    y=df[cat]/1e9,
                    name=labels[i],
                    marker_color=colors[i],
                    marker_line_color='black',
                    marker_line_width=1
                ))
            
            fig_recettes.update_layout(
                barmode='stack',
                title=f"Structure des recettes - {st.session_state.selected_commune} (Milliards de Rials)",
                xaxis_title="Année",
                yaxis_title="Milliards de Rials",
                hovermode='x',
                template='plotly_white',
                height=500,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_recettes, use_container_width=True)
            
            # Diagramme circulaire pour la dernière année
            st.markdown(f"### 🥧 Répartition des recettes en {df['Annee'].max()}")
            
            last_year = df[df['Annee'] == df['Annee'].max()].iloc[0]
            
            fig_pie = px.pie(
                values=[last_year['Impots_Locaux'], last_year['Subventions_Gouvernement'], 
                        last_year['Revenus_Petroliers'], last_year['Autres_Recettes']],
                names=['Impôts Locaux', 'Subventions', 'Revenus Pétroliers', 'Autres'],
                color_discrete_sequence=['#239F40', '#666666', '#DA0000', '#FFA500'],
                title=f"Répartition des recettes en {df['Annee'].max()}"
            )
            
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab3:
            st.markdown("### 💸 Structure des Dépenses")
            
            # Graphique en barres empilées
            fig_depenses = go.Figure()
            
            categories = ['Fonctionnement', 'Investissement', 'Charge_Dette', 'Personnel', 'Subventions_Energie']
            labels = ['Fonctionnement', 'Investissement', 'Charge Dette', 'Personnel', 'Subventions Énergie']
            colors = ['#239F40', '#FFA500', '#DA0000', '#6A0572', '#4ECDC4']
            
            for i, cat in enumerate(categories):
                fig_depenses.add_trace(go.Bar(
                    x=df['Annee'],
                    y=df[cat]/1e9,
                    name=labels[i],
                    marker_color=colors[i],
                    marker_line_color='black',
                    marker_line_width=1
                ))
            
            fig_depenses.update_layout(
                barmode='stack',
                title=f"Structure des dépenses - {st.session_state.selected_commune} (Milliards de Rials)",
                xaxis_title="Année",
                yaxis_title="Milliards de Rials",
                hovermode='x',
                template='plotly_white',
                height=500,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_depenses, use_container_width=True)
            
            # Comparaison recettes/dépenses par habitant
            st.markdown("### 👤 Recettes et Dépenses par habitant")
            
            df['Recettes_par_habitant'] = df['Recettes_Totales'] / df['Population']
            df['Depenses_par_habitant'] = df['Depenses_Totales'] / df['Population']
            
            fig_par_hab = go.Figure()
            
            fig_par_hab.add_trace(go.Scatter(
                x=df['Annee'], y=df['Recettes_par_habitant'],
                name="Recettes par habitant", line=dict(color='#239F40', width=3)
            ))
            
            fig_par_hab.add_trace(go.Scatter(
                x=df['Annee'], y=df['Depenses_par_habitant'],
                name="Dépenses par habitant", line=dict(color='#DA0000', width=3)
            ))
            
            fig_par_hab.update_layout(
                title="Recettes et dépenses par habitant (Rials)",
                xaxis_title="Année",
                yaxis_title="Rials par habitant",
                hovermode='x',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig_par_hab, use_container_width=True)
        
        with tab4:
            st.markdown("### 📊 Investissements par secteur")
            
            # Graphique des investissements sectoriels
            fig_invest = go.Figure()
            
            invest_categories = ['Investissement_Petrole_Gaz', 'Investissement_Agriculture', 
                                'Investissement_Transport', 'Investissement_Education',
                                'Investissement_Sante', 'Investissement_Industrie', 'Investissement_Culture']
            invest_labels = ['Pétrole & Gaz', 'Agriculture', 'Transport', 'Éducation', 
                            'Santé', 'Industrie', 'Culture']
            invest_colors = ['#DA0000', '#239F40', '#FFA500', '#4ECDC4', '#6A0572', '#FF6B6B', '#45B7D1']
            
            for i, cat in enumerate(invest_categories):
                fig_invest.add_trace(go.Scatter(
                    x=df['Annee'], y=df[cat]/1e9,
                    name=invest_labels[i],
                    line=dict(width=2)
                ))
            
            fig_invest.update_layout(
                title=f"Évolution des investissements par secteur - {st.session_state.selected_commune} (Milliards de Rials)",
                xaxis_title="Année",
                yaxis_title="Milliards de Rials",
                hovermode='x',
                template='plotly_white',
                height=500,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_invest, use_container_width=True)
            
            # Répartition des investissements pour la dernière année
            st.markdown(f"### 🥧 Répartition des investissements en {df['Annee'].max()}")
            
            last_year = df[df['Annee'] == df['Annee'].max()].iloc[0]
            invest_values = [last_year[cat] for cat in invest_categories]
            
            # Filtrer les valeurs nulles
            invest_data = [(invest_labels[i], invest_values[i]) for i in range(len(invest_values)) if invest_values[i] > 0]
            
            if invest_data:
                fig_invest_pie = px.pie(
                    values=[v for _, v in invest_data],
                    names=[n for n, _ in invest_data],
                    title=f"Répartition des investissements en {df['Annee'].max()}"
                )
                fig_invest_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_invest_pie, use_container_width=True)
        
        with tab5:
            st.markdown("### 📉 Dette et Inflation")
            
            col_dette1, col_dette2 = st.columns(2)
            
            with col_dette1:
                # Graphique de la dette
                fig_dette = go.Figure()
                
                fig_dette.add_trace(go.Bar(
                    x=df['Annee'], y=df['Dette_Totale']/1e9,
                    name="Dette totale",
                    marker_color='#DA0000',
                    marker_line_color='black',
                    marker_line_width=1,
                    opacity=0.7
                ))
                
                fig_dette.add_trace(go.Scatter(
                    x=df['Annee'], y=df['Taux_Endettement']*100,
                    name="Taux d'endettement (%)",
                    yaxis="y2",
                    line=dict(color='#239F40', width=3)
                ))
                
                fig_dette.update_layout(
                    title="Évolution de la dette et taux d'endettement",
                    xaxis_title="Année",
                    yaxis_title="Milliards de Rials",
                    yaxis2=dict(
                        title="Taux d'endettement (%)",
                        overlaying='y',
                        side='right',
                        showgrid=False
                    ),
                    hovermode='x',
                    template='plotly_white',
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_dette, use_container_width=True)
            
            with col_dette2:
                # Graphique de l'inflation
                fig_inflation = go.Figure()
                
                fig_inflation.add_trace(go.Bar(
                    x=df['Annee'], y=df['Inflation']*100,
                    name="Taux d'inflation",
                    marker_color='#FFA500',
                    marker_line_color='black',
                    marker_line_width=1
                ))
                
                # Ligne de référence à 40%
                fig_inflation.add_hline(y=40, line_dash="dash", line_color="#DA0000",
                                       annotation_text="Seuil critique", annotation_position="top left")
                
                fig_inflation.update_layout(
                    title="Évolution du taux d'inflation",
                    xaxis_title="Année",
                    yaxis_title="Inflation (%)",
                    hovermode='x',
                    template='plotly_white',
                    height=400
                )
                
                st.plotly_chart(fig_inflation, use_container_width=True)
            
            # Périodes de sanctions
            st.markdown("### ⚠️ Impact des sanctions sur les indicateurs clés")
            
            # Créer un DataFrame avec les périodes de sanctions
            sanctions_df = pd.DataFrame({
                'Période': ['Boom pétrolier (2002-2005)', 'Premières sanctions (2006-2007)', 
                           'Crise financière (2008-2009)', 'Sanctions renforcées (2012-2015)',
                           'Accord nucléaire (2016-2017)', 'Sanctions maximales (2018-2020)',
                           'Adaptation (2021-2025)'],
                'Impact': ['Croissance forte', 'Ralentissement modéré', 'Impact modéré',
                          'Crise sévère', 'Reprise temporaire', 'Crise maximale', 'Résilience'],
                'Croissance PIB': ['+5-6%', '+3-4%', '+1-2%', '-2-3%', '+4-5%', '-4-5%', '+1-2%'],
                'Inflation': ['15-20%', '20-25%', '25-30%', '30-40%', '10-15%', '40-50%', '30-35%']
            })
            
            st.dataframe(sanctions_df, use_container_width=True, hide_index=True)
        
        with tab6:
            st.markdown("### 🧠 Analyse et Insights")
            
            # Générer les insights
            last_year_val = df['Annee'].max()
            first_year_val = df['Annee'].min()
            
            last_data = df[df['Annee'] == last_year_val].iloc[0]
            first_data = df[df['Annee'] == first_year_val].iloc[0]
            
            col_insight1, col_insight2 = st.columns(2)
            
            with col_insight1:
                st.markdown("#### 📈 Croissance")
                
                revenue_growth = ((last_data['Recettes_Totales'] / first_data['Recettes_Totales']) - 1) * 100
                population_growth = ((last_data['Population'] / first_data['Population']) - 1) * 100
                debt_growth = ((last_data['Dette_Totale'] / first_data['Dette_Totale']) - 1) * 100
                
                st.metric("Croissance des recettes", f"{revenue_growth:.1f}%", 
                         delta=f"{revenue_growth - 100:.1f}%" if revenue_growth > 100 else f"{revenue_growth:.1f}%")
                st.metric("Croissance démographique", f"{population_growth:.1f}%")
                st.metric("Croissance de la dette", f"{debt_growth:.1f}%")
                
                st.markdown("#### 💰 Ratios financiers")
                
                # Calculer quelques ratios
                recettes_par_hab = last_data['Recettes_Totales'] / last_data['Population']
                depenses_par_hab = last_data['Depenses_Totales'] / last_data['Population']
                autonomie_fiscale = (last_data['Impots_Locaux'] / last_data['Recettes_Totales']) * 100
                
                st.metric("Recettes par habitant", format_rial(recettes_par_hab, False, 0))
                st.metric("Dépenses par habitant", format_rial(depenses_par_hab, False, 0))
                st.metric("Autonomie fiscale", f"{autonomie_fiscale:.1f}%")
            
            with col_insight2:
                st.markdown("#### 🌟 Spécificités de la commune")
                st.markdown(f"**Type:** {analyzer.config['type'].capitalize()}")
                st.markdown(f"**Spécialités:** {', '.join(analyzer.config['specialites'])}")
                st.markdown(f"**Description:** {analyzer.config.get('description', 'Non disponible')}")
                
                st.markdown("#### 📅 Événements marquants")
                events = [
                    "2002-2005: Boom pétrolier",
                    "2006-2007: Premières sanctions",
                    "2012-2015: Sanctions renforcées",
                    "2016-2017: Accord nucléaire",
                    "2018-2020: Sanctions maximales",
                    "2021-2025: Adaptation"
                ]
                
                # dashboard_iran_communes.py (suite et fin)

                for event in events:
                    st.markdown(f"- {event}")
                
                st.markdown("#### ⚠️ Recommandations")
                
                if "petrole" in analyzer.config["specialites"]:
                    st.markdown("• Diversifier l'économie au-delà du pétrole")
                    st.markdown("• Développer les technologies d'extraction")
                if "agriculture" in analyzer.config["specialites"]:
                    st.markdown("• Moderniser les techniques agricoles")
                    st.markdown("• Développer l'agro-industrie")
                if "industrie" in analyzer.config["specialites"]:
                    st.markdown("• Promouvoir l'industrie locale")
                    st.markdown("• Développer les parcs industriels")
                
                st.markdown("• Renforcer l'autosuffisance énergétique")
                st.markdown("• Développer les partenariats régionaux")
            
            # Tableau récapitulatif
            st.markdown("### 📋 Données annuelles")
            display_cols = ['Annee', 'Population', 'Recettes_Totales', 'Depenses_Totales', 
                           'Epargne_Brute', 'Dette_Totale', 'Taux_Endettement', 'Inflation']
            
            df_display = df[display_cols].copy()
            
            # Formater les colonnes pour l'affichage
            for col in ['Recettes_Totales', 'Depenses_Totales', 'Epargne_Brute', 'Dette_Totale']:
                df_display[col] = df_display[col].apply(lambda x: format_rial(x, False, 1))
            
            df_display['Taux_Endettement'] = df_display['Taux_Endettement'].apply(lambda x: f"{x*100:.1f}%")
            df_display['Inflation'] = df_display['Inflation'].apply(lambda x: f"{x*100:.1f}%")
            df_display['Population'] = df_display['Population'].apply(lambda x: f"{x:,.0f}")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Export des données
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger les données en CSV",
                data=csv,
                file_name=f"{st.session_state.selected_commune}_finances_{start_year}_{end_year}.csv",
                mime="text/csv"
            )

else:
    # Mode comparaison multiple
    if not st.session_state.comparison_communes:
        st.warning("Veuillez sélectionner au moins une commune à comparer")
    else:
        st.markdown(f"## 🔄 Comparaison de {len(st.session_state.comparison_communes)} communes")
        
        # Générer les données pour chaque commune
        dfs = {}
        analyzers = {}
        
        with st.spinner("Génération des données pour les communes sélectionnées..."):
            for commune in st.session_state.comparison_communes:
                analyzer = IranCommuneFinanceAnalyzer(commune)
                df = analyzer.generate_financial_data()
                df = df[(df['Annee'] >= start_year) & (df['Annee'] <= end_year)]
                dfs[commune] = df
                analyzers[commune] = analyzer
        
        # KPIs comparatifs
        st.markdown("### 📊 Comparaison des indicateurs clés (2025)")
        
        comparison_data = []
        for commune in st.session_state.comparison_communes:
            df_comm = dfs[commune]
            last_year = df_comm[df_comm['Annee'] == df_comm['Annee'].max()].iloc[0]
            
            comparison_data.append({
                'Commune': commune,
                'Population': f"{last_year['Population']:,.0f}",
                'Recettes': format_rial(last_year['Recettes_Totales'], False, 1),
                'Dépenses': format_rial(last_year['Depenses_Totales'], False, 1),
                'Solde': format_rial(last_year['Recettes_Totales'] - last_year['Depenses_Totales'], False, 1),
                'Dette': format_rial(last_year['Dette_Totale'], False, 1),
                'Endettement': f"{last_year['Taux_Endettement']*100:.1f}%",
                'Inflation': f"{last_year['Inflation']*100:.1f}%",
                'Type': analyzers[commune].config['type']
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        # Graphiques comparatifs
        tab_comp1, tab_comp2, tab_comp3, tab_comp4 = st.tabs([
            "📈 Recettes", "💸 Dépenses", "📊 Dette", "👥 Population"
        ])
        
        with tab_comp1:
            st.markdown("### 📈 Comparaison des recettes")
            
            fig_comp_rev = go.Figure()
            
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                fig_comp_rev.add_trace(go.Scatter(
                    x=df_comm['Annee'], y=df_comm['Recettes_Totales']/1e9,
                    name=commune,
                    line=dict(width=3)
                ))
            
            fig_comp_rev.update_layout(
                title="Évolution comparée des recettes (Milliards de Rials)",
                xaxis_title="Année",
                yaxis_title="Milliards de Rials",
                hovermode='x unified',
                template='plotly_white',
                height=500
            )
            
            st.plotly_chart(fig_comp_rev, use_container_width=True)
            
            # Diagramme circulaire pour la dernière année
            st.markdown("### 🥧 Répartition des recettes par commune (2025)")
            
            last_year_val = dfs[st.session_state.comparison_communes[0]]['Annee'].max()
            rev_data = []
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                last_data = df_comm[df_comm['Annee'] == last_year_val].iloc[0]
                rev_data.append(last_data['Recettes_Totales'])
            
            fig_pie_comp = px.pie(
                values=rev_data,
                names=st.session_state.comparison_communes,
                title=f"Part des recettes totales en {last_year_val}"
            )
            fig_pie_comp.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie_comp, use_container_width=True)
        
        with tab_comp2:
            st.markdown("### 💸 Comparaison des dépenses")
            
            fig_comp_exp = go.Figure()
            
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                fig_comp_exp.add_trace(go.Scatter(
                    x=df_comm['Annee'], y=df_comm['Depenses_Totales']/1e9,
                    name=commune,
                    line=dict(width=3)
                ))
            
            fig_comp_exp.update_layout(
                title="Évolution comparée des dépenses (Milliards de Rials)",
                xaxis_title="Année",
                yaxis_title="Milliards de Rials",
                hovermode='x unified',
                template='plotly_white',
                height=500
            )
            
            st.plotly_chart(fig_comp_exp, use_container_width=True)
            
            # Solde budgétaire
            st.markdown("### ⚖️ Comparaison du solde budgétaire")
            
            fig_comp_solde = go.Figure()
            
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                solde = df_comm['Recettes_Totales'] - df_comm['Depenses_Totales']
                fig_comp_solde.add_trace(go.Bar(
                    x=df_comm['Annee'], y=solde/1e9,
                    name=commune,
                    opacity=0.7
                ))
            
            fig_comp_solde.update_layout(
                title="Solde budgétaire comparé (Milliards de Rials)",
                xaxis_title="Année",
                yaxis_title="Milliards de Rials",
                barmode='group',
                hovermode='x',
                template='plotly_white',
                height=500
            )
            
            st.plotly_chart(fig_comp_solde, use_container_width=True)
        
        with tab_comp3:
            st.markdown("### 📊 Comparaison de la dette")
            
            fig_comp_debt = go.Figure()
            
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                fig_comp_debt.add_trace(go.Scatter(
                    x=df_comm['Annee'], y=df_comm['Dette_Totale']/1e9,
                    name=commune,
                    line=dict(width=3)
                ))
            
            fig_comp_debt.update_layout(
                title="Évolution comparée de la dette (Milliards de Rials)",
                xaxis_title="Année",
                yaxis_title="Milliards de Rials",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig_comp_debt, use_container_width=True)
            
            # Taux d'endettement
            st.markdown("### 📉 Comparaison du taux d'endettement")
            
            fig_comp_debt_ratio = go.Figure()
            
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                fig_comp_debt_ratio.add_trace(go.Scatter(
                    x=df_comm['Annee'], y=df_comm['Taux_Endettement']*100,
                    name=commune,
                    line=dict(width=3)
                ))
            
            fig_comp_debt_ratio.update_layout(
                title="Taux d'endettement comparé (%)",
                xaxis_title="Année",
                yaxis_title="Taux d'endettement (%)",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig_comp_debt_ratio, use_container_width=True)
            
            # Inflation
            st.markdown("### 📈 Comparaison de l'inflation")
            
            fig_comp_inf = go.Figure()
            
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                fig_comp_inf.add_trace(go.Scatter(
                    x=df_comm['Annee'], y=df_comm['Inflation']*100,
                    name=commune,
                    line=dict(width=3)
                ))
            
            fig_comp_inf.update_layout(
                title="Taux d'inflation comparé (%)",
                xaxis_title="Année",
                yaxis_title="Inflation (%)",
                hovermode='x unified',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig_comp_inf, use_container_width=True)
        
        with tab_comp4:
            st.markdown("### 👥 Comparaison démographique")
            
            fig_comp_pop = go.Figure()
            
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                fig_comp_pop.add_trace(go.Scatter(
                    x=df_comm['Annee'], y=df_comm['Population'],
                    name=commune,
                    line=dict(width=3),
                    fill='tonexty' if commune == st.session_state.comparison_communes[0] else None
                ))
            
            fig_comp_pop.update_layout(
                title="Évolution comparée de la population",
                xaxis_title="Année",
                yaxis_title="Population",
                hovermode='x unified',
                template='plotly_white',
                height=500
            )
            
            st.plotly_chart(fig_comp_pop, use_container_width=True)
            
            # Densité de population
            st.markdown("### 📊 Densité de population (hab/km²)")
            
            densite_data = []
            for commune in st.session_state.comparison_communes:
                df_comm = dfs[commune]
                last_year = df_comm[df_comm['Annee'] == df_comm['Annee'].max()].iloc[0]
                superficie = analyzers[commune].config.get('superficie', 100)
                densite = last_year['Population'] / superficie
                densite_data.append({
                    'Commune': commune,
                    'Superficie (km²)': superficie,
                    'Population': f"{last_year['Population']:,.0f}",
                    'Densité (hab/km²)': f"{densite:,.0f}"
                })
            
            df_densite = pd.DataFrame(densite_data)
            st.dataframe(df_densite, use_container_width=True, hide_index=True)
            
            # Graphique en barres
            fig_densite = px.bar(
                x=[d['Commune'] for d in densite_data],
                y=[float(d['Densité (hab/km²)'].replace(',', '')) for d in densite_data],
                color=[d['Commune'] for d in densite_data],
                title="Densité de population par commune"
            )
            fig_densite.update_layout(
                xaxis_title="Commune",
                yaxis_title="Densité (hab/km²)",
                showlegend=False
            )
            st.plotly_chart(fig_densite, use_container_width=True)

# Notes contextuelles
st.markdown("---")
col_note1, col_note2, col_note3 = st.columns(3)

with col_note1:
    st.markdown("""
    <div class='info-box'>
        <b>📌 Contexte économique</b><br>
        • Sanctions internationales depuis 2006<br>
        • Inflation structurelle élevée (>30%)<br>
        • Dépendance aux revenus pétroliers<br>
        • Résilience et adaptation progressive
    </div>
    """, unsafe_allow_html=True)

with col_note2:
    st.markdown("""
    <div class='info-box'>
        <b>💰 Taux de change</b><br>
        • Officiel: 1€ ≈ 50,000 Rials<br>
        • Marché libre: 1€ ≈ 150,000 Rials<br>
        • NIMA (commerce): 1€ ≈ 80,000 Rials<br>
        • Écart officiel/marché: 3x
    </div>
    """, unsafe_allow_html=True)

with col_note3:
    st.markdown("""
    <div class='info-box'>
        <b>📊 Sources des données</b><br>
        • Banque Centrale d'Iran (CBI)<br>
        • Ministère de l'Intérieur<br>
        • Organisation du Plan et Budget<br>
        • Données municipales simulées
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8rem;'>
    🇮🇷 Dashboard d'analyse financière des communes iraniennes | Période 2002-2025<br>
    📅 Données simulées basées sur les tendances économiques réelles de l'Iran<br>
    ⚠️ À titre informatif uniquement - Ne constitue pas un conseil financier
</div>
""", unsafe_allow_html=True)

# Message en persan
st.markdown("""
<div style='text-align: center; font-family: Scheherazade; font-size: 1.2rem; margin-top: 1rem; direction: rtl;'>
    <p>🇮🇷 داشبورد تحلیل مالی شهرداری‌های ایران</p>
    <p>منابع: بانک مرکزی ایران، وزارت کشور، سازمان برنامه و بودجه</p>
    <p>دوره زمانی: ۲۰۰۲-۲۰۲۵</p>
</div>
""", unsafe_allow_html=True)
                  
