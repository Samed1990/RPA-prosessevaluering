import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
import json

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="RPA Prosessevaluering",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SUPABASE CONFIGURATION ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

supabase: Client = init_supabase()

def create_table_if_not_exists():
    """Create the prosesser table if it doesn't exist"""
    try:
        # Try to select from the table to see if it exists
        supabase.table("prosesser").select("*").limit(1).execute()
    except Exception as e:
        st.error(f"Table 'prosesser' might not exist. Please create it in your Supabase dashboard with the following SQL:")
        st.code("""
CREATE TABLE prosesser (
    id SERIAL PRIMARY KEY,
    prosessnavn TEXT NOT NULL,
    prosesseier TEXT NOT NULL,
    avdeling TEXT NOT NULL,
    prosessbeskrivelse TEXT NOT NULL,
    trigger TEXT,
    frekvens TEXT,
    antall_prosesser INTEGER,
    behandlingstid INTEGER,
    personer_involvert INTEGER,
    feilrate INTEGER,
    kostnad_per_time INTEGER,
    arsvolum INTEGER,
    arslig_tidsbesparing INTEGER,
    kostnadsbesparelse INTEGER,
    it_systemer TEXT,
    datakilder TEXT,
    filformater TEXT,
    api_tilgang TEXT,
    tidsbesparelse INTEGER,
    volum INTEGER,
    kvalitetsforbedring INTEGER,
    teknisk_kompleksitet INTEGER,
    datakompleksitet INTEGER,
    regelstabilitet INTEGER,
    org_pavirkning INTEGER,
    brukerpavirkning INTEGER,
    regelverksoverholdelse INTEGER,
    gevinst_score INTEGER,
    gjennomforbarhet_score INTEGER,
    strategisk_score INTEGER,
    total_score INTEGER,
    justert_score INTEGER,
    volum_bonus INTEGER,
    prioritet TEXT,
    risiko_faktorer TEXT,
    bonus_faktorer TEXT,
    registrert_dato TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
        """)
        return False
    return True

def to_int(x):
    try:
        return int(round(float(x)))
    except Exception:
        return 0


@st.cache_data(ttl=30)  # Cache for 30 seconds
def last_data():
    """Load data from Supabase"""
    try:
        if not create_table_if_not_exists():
            return pd.DataFrame()
        
        response = supabase.table("prosesser").select("*").order("created_at", desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data from Supabase: {str(e)}")
        return pd.DataFrame()

def lagre_data_to_supabase(data_dict):
    """Save data to Supabase as pure integers for all numeric fields"""
    try:
        # Remove 'id' if it exists (Supabase will auto-generate)
        if 'id' in data_dict:
            del data_dict['id']

        # Convert lists to comma-separated strings for risiko_faktorer and bonus_faktorer
        if 'risiko_faktorer' in data_dict and isinstance(data_dict['risiko_faktorer'], list):
            data_dict['risiko_faktorer'] = ', '.join(data_dict['risiko_faktorer'])
        if 'bonus_faktorer' in data_dict and isinstance(data_dict['bonus_faktorer'], list):
            data_dict['bonus_faktorer'] = ', '.join(data_dict['bonus_faktorer'])

        # List of ALL numeric fields to be forced as int
        integer_fields = [
            'antall_prosesser', 'behandlingstid', 'personer_involvert', 'kostnad_per_time',
            'arsvolum', 'tidsbesparelse', 'volum', 'kvalitetsforbedring', 'teknisk_kompleksitet',
            'datakompleksitet', 'regelstabilitet', 'org_pavirkning', 'brukerpavirkning', 'regelverksoverholdelse',
            'arslig_tidsbesparing', 'kostnadsbesparelse', 'feilrate', 'gevinst_score', 'gjennomforbarhet_score',
            'strategisk_score', 'total_score', 'justert_score', 'volum_bonus'
        ]

        # Force all listed fields to int (via float, then round)
        for field in integer_fields:
            if field in data_dict and data_dict[field] is not None:
                try:
                    data_dict[field] = int(round(float(data_dict[field])))
                except Exception:
                    data_dict[field] = 0

        # Uncomment for debugging if you want to see what goes in:
        # st.write({k: f"{v} ({type(v)})" for k, v in data_dict.items()})

        response = supabase.table("prosesser").insert(data_dict).execute()

        if response.data:
            st.cache_data.clear()  # Clear cache after successful insert
            return True
        else:
            st.error("Failed to save data to Supabase")
            return False
    except Exception as e:
        st.error(f"Error saving to Supabase: {str(e)}")
        return False



def oppdater_data_in_supabase(prosess_id, data_dict):
    """Update data in Supabase (convert all numeric fields to int as in lagre_data_to_supabase)"""
    try:
        # Remove 'id' from data_dict to avoid conflicts
        if 'id' in data_dict:
            del data_dict['id']
        
        # Convert lists to comma-separated strings
        if 'risiko_faktorer' in data_dict and isinstance(data_dict['risiko_faktorer'], list):
            data_dict['risiko_faktorer'] = ', '.join(data_dict['risiko_faktorer'])
        if 'bonus_faktorer' in data_dict and isinstance(data_dict['bonus_faktorer'], list):
            data_dict['bonus_faktorer'] = ', '.join(data_dict['bonus_faktorer'])
        
        # Force all listed fields to int (via float, then round)
        integer_fields = [
            'antall_prosesser', 'behandlingstid', 'personer_involvert', 'kostnad_per_time',
            'arsvolum', 'tidsbesparelse', 'volum', 'kvalitetsforbedring', 'teknisk_kompleksitet',
            'datakompleksitet', 'regelstabilitet', 'org_pavirkning', 'brukerpavirkning', 'regelverksoverholdelse',
            'arslig_tidsbesparing', 'kostnadsbesparelse', 'feilrate', 'gevinst_score', 'gjennomforbarhet_score',
            'strategisk_score', 'total_score', 'justert_score', 'volum_bonus'
        ]

        for field in integer_fields:
            if field in data_dict and data_dict[field] is not None:
                try:
                    data_dict[field] = int(round(float(data_dict[field])))
                except Exception:
                    data_dict[field] = 0
        
        # Add updated timestamp
        data_dict['updated_at'] = datetime.now().isoformat()
        
        response = supabase.table("prosesser").update(data_dict).eq("id", prosess_id).execute()
        
        if response.data:
            st.cache_data.clear()  # Clear cache after successful update
            return True
        else:
            st.error("Failed to update data in Supabase")
            return False
    except Exception as e:
        st.error(f"Error updating data in Supabase: {str(e)}")
        return False


def slett_prosess_from_supabase(prosess_id):
    """Delete process from Supabase"""
    try:
        response = supabase.table("prosesser").delete().eq("id", prosess_id).execute()
        
        if response.data:
            st.cache_data.clear()  # Clear cache after successful delete
            return True
        else:
            st.error("Failed to delete data from Supabase")
            return False
    except Exception as e:
        st.error(f"Error deleting data from Supabase: {str(e)}")
        return False

# --- SCORE BEREGNING ---
# 1. NYE HJELPEFUNKSJONER

def beregn_datakompleksitet_score(datakilder, filformater, api_tilgang):
    """
    Beregner datakompleksitet basert på:
    - Antall datakilder 
    - Antall filformater
    - API-tilgang
    (Timekostnad er ikke lenger relevant)
    """
    base_score = 1  # Start lavt

    # Tell antall datakilder (separert med komma)
    antall_datakilder = 0
    if datakilder and datakilder.strip():
        antall_datakilder = len([x.strip() for x in datakilder.split(',') if x.strip()])

    # Tell antall filformater (separert med komma)
    antall_filformater = 0
    if filformater and filformater.strip():
        antall_filformater = len([x.strip() for x in filformater.split(',') if x.strip()])

    # Kompleksitetsbonus
    kompleksitet_bonus = 0

    # Datakilder: +1 per ekstra kilde (utover 1)
    if antall_datakilder > 1:
        kompleksitet_bonus += (antall_datakilder - 1) * 1

    # Filformater: +0.5 per ekstra format (utover 1)
    if antall_filformater > 1:
        kompleksitet_bonus += (antall_filformater - 1) * 0.5

    # API-tilgang: +1 poeng hvis ja
    if api_tilgang and api_tilgang.lower() == "ja":
        kompleksitet_bonus += 1.0

    # Beregn endelig score (maks 5)
    final_score = min(5, base_score + kompleksitet_bonus)

    return int(round(final_score))


def beregn_kvalitetsforbedring_score(behandlingstid, antall_prosesser, brukeropplaering, prosessendring, motstand_forventet):
    """
    Beregner kvalitetsforbedring basert på:
    - Behandlingstid og antall prosesser (grunnlag)
    - Endringsutfordringer (bonus)
    """
    # Grunnlag basert på oppgavekompleksitet (eksisterende logikk)
    if behandlingstid >= 60 and antall_prosesser >= 100:
        base_score = 5
    elif (behandlingstid >= 30 and antall_prosesser >= 50) or behandlingstid >= 90:
        base_score = 4
    elif behandlingstid >= 15 or antall_prosesser >= 20:
        base_score = 3
    elif behandlingstid >= 5 or antall_prosesser >= 10:
        base_score = 2
    else:
        base_score = 1
    
    # Endringsbonus
    endring_bonus = 0
    
    # Opplæringsbehov: +1 hvis lett å implementere
    if brukeropplaering in ["Kort introduksjon", "Strukturert opplæring"]:
        endring_bonus += 1
    
    # Prosessendring: +1 hvis små justeringer
    if prosessendring == "Små justeringer":
        endring_bonus += 1
    
    # Motstand: +1 hvis lav motstand
    if motstand_forventet == "Lav motstand":
        endring_bonus += 1
    
    # Beregn endelig score (maks 5)
    final_score = min(5, base_score + endring_bonus)
    
    return int(round(final_score))

def beregn_realistisk_kostnadsbesparelse(arslig_tidsbesparing, kostnad_per_time, 
                                        lisenskostnad_aarlig, vedlikeholdskostnad_aar):
    """
    Beregner realistisk årlig kostnadsbesparelse:
    - Timebesparing × (kostnad per time × 1.141) [14.1% arbeidsgiveravgift for Oslo]
    - Minus årlige lisenskostnader
    - Minus årlige driftskostnader
    """
    # Arbeidsgiveravgift Oslo-området: 14.1%
    ARBEIDSGIVERAVGIFT = 1.141
    
    # Brutto besparelse med arbeidsgiveravgift
    brutto_besparelse = arslig_tidsbesparing * (kostnad_per_time * ARBEIDSGIVERAVGIFT)
    
    # Trekk fra kostnader
    netto_besparelse = brutto_besparelse - lisenskostnad_aarlig - vedlikeholdskostnad_aar
    
    return int(round(max(0, netto_besparelse)))  # Kan ikke være negativ

def get_val_safe(df, index, col, default):
    """Robust get_val som håndterer missing values og type conversion"""
    if index is None or df is None or df.empty:
        return default
    
    try:
        val = df.iloc[index][col]
        if pd.isna(val) or val == '' or val is None:
            return default
        
        # Type-specific handling
        if isinstance(default, int):
            try:
                return int(float(val))
            except:
                return default
        elif isinstance(default, float):
            try:
                return float(val)
            except:
                return default
        else:
            return str(val) if val is not None else default
            
    except (KeyError, IndexError, TypeError):
        return default
    
def beregn_prioritering(data):
    """Beregner prioriteringsscore basert på inputdata med maks 10 poeng"""
    # Hovedscores (1-5 hver)
    gevinst = (data['tidsbesparelse'] * 0.4 + data['volum'] * 0.4 + data['kvalitetsforbedring'] * 0.2) * 2  # Maks 10
    gjennomforbarhet = (data['teknisk_kompleksitet'] * 0.3 + data['datakompleksitet'] * 0.4 + data['regelstabilitet'] * 0.3) * 2
    strategisk = (data['org_pavirkning'] * 0.3 + data['brukerpavirkning'] * 0.4 + data['regelverksoverholdelse'] * 0.3) * 2  # Maks 10
    
    # Hovedscore er gjennomsnittet av de tre (maks 10)
    total = (gevinst + gjennomforbarhet + strategisk) / 3
    
    # Bonuser og justeringer
    risiko_justering = len(data.get('risiko_faktorer', []))
    bonus_justering = len(data.get('bonus_faktorer', []))
    
    # Volum bonus basert på kvantitative data
    volum_bonus = 0
    if data.get('antall_prosesser', 0) > 500:
        volum_bonus += 1.0
    elif data.get('antall_prosesser', 0) > 200:
        volum_bonus += 0.5
    
    if data.get('behandlingstid', 0) > 60:
        volum_bonus += 1.0
    elif data.get('behandlingstid', 0) > 30:
        volum_bonus += 0.5
    
    if data.get('feilrate', 0) > 15:
        volum_bonus += 1.0
    elif data.get('feilrate', 0) > 5:
        volum_bonus += 0.5
    
    # Justert total (maks 10)
    justert_total = min(10, max(0, total + bonus_justering + volum_bonus - risiko_justering))
    
    return {
        'gevinst_score': round(gevinst, 2),
        'gjennomforbarhet_score': round(gjennomforbarhet, 2),
        'strategisk_score': round(strategisk, 2),
        'total_score': round(total, 2),
        'justert_score': round(justert_total, 2),
        'volum_bonus': round(volum_bonus, 2)
    }

# 2. OPPDATERTE HOVEDFUNKSJONER

def beregn_kvantitative_scores(behandlingstid, antall_prosesser, feilrate, personer_involvert, 
                              kostnad_per_time, filformater, datakilder, api_tilgang,
                              brukeropplaering, prosessendring, motstand_forventet):
    """
    OPPDATERT versjon som bruker nye beregninger
    """
    
    # Tidsbesparelse score (uendret)
    if behandlingstid >= 120:
        tidsbesparelse_score = 5
    elif behandlingstid >= 60:
        tidsbesparelse_score = 4
    elif behandlingstid >= 30:
        tidsbesparelse_score = 3
    elif behandlingstid >= 10:
        tidsbesparelse_score = 2
    else:
        tidsbesparelse_score = 1
    
    # Volum score (uendret)
    if antall_prosesser >= 1000:
        volum_score = 5
    elif antall_prosesser >= 500:
        volum_score = 4
    elif antall_prosesser >= 200:
        volum_score = 3
    elif antall_prosesser >= 50:
        volum_score = 2
    else:
        volum_score = 1
    
    # NY kvalitetsforbedring score
    kvalitet_score = beregn_kvalitetsforbedring_score(
        behandlingstid, antall_prosesser, brukeropplaering, prosessendring, motstand_forventet
    )
    
    # Teknisk kompleksitet (uendret)
    teknisk_score = 3  # Default medium
    if filformater:
        f = filformater.lower()
        if "api" in f:
            teknisk_score = 5
        elif "xml" in f or "json" in f:
            teknisk_score = 4
        elif "pdf" in f or "word" in f or "docx" in f:
            teknisk_score = 3
        elif "excel" in f or "xlsx" in f or "csv" in f:
            teknisk_score = 4
        else:
            teknisk_score = 2
    
    # NY datakompleksitet score (erstatter datakompleksitet)
    datakompleksitet_score = beregn_datakompleksitet_score(
        datakilder, filformater, api_tilgang
    )

    
    # Regelstabilitet (uendret)
    if behandlingstid >= 60 and antall_prosesser >= 100:
        regelstabilitet_score = 5
    elif behandlingstid >= 30 and antall_prosesser >= 50:
        regelstabilitet_score = 4
    elif behandlingstid >= 15 or antall_prosesser >= 20:
        regelstabilitet_score = 3
    else:
        regelstabilitet_score = 2
    
    return tidsbesparelse_score, volum_score, kvalitet_score, teknisk_score, datakompleksitet_score, regelstabilitet_score

def beregn_prioritering(data):
    """Beregner prioriteringsscore basert på inputdata med maks 10 poeng - OPPDATERT"""
    # Hovedscores (1-5 hver) - ENDRET navn fra datakompleksitet til datakompleksitet
    gevinst = (data['tidsbesparelse'] * 0.4 + data['volum'] * 0.4 + data['kvalitetsforbedring'] * 0.2) * 2
    gjennomforbarhet = (data['teknisk_kompleksitet'] * 0.3 + data['datakompleksitet'] * 0.4 + data['regelstabilitet'] * 0.3) * 2
    strategisk = (data['org_pavirkning'] * 0.3 + data['brukerpavirkning'] * 0.4 + data['regelverksoverholdelse'] * 0.3) * 2
    
    # Hovedscore er gjennomsnittet av de tre (maks 10)
    total = (gevinst + gjennomforbarhet + strategisk) / 3
    
    # Bonuser og justeringer (uendret)
    risiko_justering = len(data.get('risiko_faktorer', []))
    bonus_justering = len(data.get('bonus_faktorer', []))
    
    # Volum bonus basert på kvantitative data (uendret)
    volum_bonus = 0
    if data.get('antall_prosesser', 0) > 500:
        volum_bonus += 1.0
    elif data.get('antall_prosesser', 0) > 200:
        volum_bonus += 0.5
    
    if data.get('behandlingstid', 0) > 60:
        volum_bonus += 1.0
    elif data.get('behandlingstid', 0) > 30:
        volum_bonus += 0.5
    
    if data.get('feilrate', 0) > 15:
        volum_bonus += 1.0
    elif data.get('feilrate', 0) > 5:
        volum_bonus += 0.5
    
    # Justert total (maks 10)
    justert_total = min(10, max(0, total + bonus_justering + volum_bonus - risiko_justering))
    
    return {
        'gevinst_score': round(gevinst, 2),
        'gjennomforbarhet_score': round(gjennomforbarhet, 2),
        'strategisk_score': round(strategisk, 2),
        'total_score': round(total, 2),
        'justert_score': round(justert_total, 2),
        'volum_bonus': round(volum_bonus, 2)
    }

def get_prioritet_kategori(score):
    """Returnerer prioritetskategori basert på score (1-10 skala)"""
    if score >= 6.6:
        return "🔴 HØY PRIORITET"
    elif score >= 4.0:
        return "🟡 MEDIUM PRIORITET"
    elif score >= 1.0:
        return "🟢 LAV PRIORITET"
    else:
        return "⚪ IKKE AKTUELL"

# --- ADVANCED RPA ANALYSIS HELPERS ---

def beregn_roi_metrics(kostnadsbesparelse, implementeringskostnad, vedlikeholdskostnad_aar, estimert_implementeringstid, forventet_levetid_aar):
    """Beregner ROI-relaterte metrics"""
    # Total savings over expected lifetime
    total_besparelser = kostnadsbesparelse * forventet_levetid_aar
    total_kostnader = implementeringskostnad + (vedlikeholdskostnad_aar * forventet_levetid_aar)
    # ROI calculation
    roi_percentage = ((total_besparelser - total_kostnader) / total_kostnader) * 100 if total_kostnader > 0 else 0
    # Payback period in months
    monthly_net_savings = (kostnadsbesparelse / 12) - (vedlikeholdskostnad_aar / 12)
    payback_months = implementeringskostnad / monthly_net_savings if monthly_net_savings > 0 else 999
    # NPV calculation (simplified, 8% discount rate)
    discount_rate = 0.08
    npv = 0
    for year in range(1, forventet_levetid_aar + 1):
        annual_net_benefit = kostnadsbesparelse - vedlikeholdskostnad_aar
        npv += annual_net_benefit / ((1 + discount_rate) ** year)
    npv -= implementeringskostnad
    return {
        'roi_percentage': round(roi_percentage, 1),
        'payback_months': round(payback_months, 1),
        'npv': round(npv, 0),
        'total_besparelser': round(total_besparelser, 0),
        'total_kostnader': round(total_kostnader, 0)
    }

def get_technology_recommendation(filformater, api_tilgang, integrasjon_vanskelighet, antall_prosesser):
    """Anbefaler RPA-teknologi basert på prosesskarakteristikker"""
    recommendations = []
    # Volume-based recommendations (prefer Microsoft for your case!)
    if antall_prosesser >= 100:
        recommendations.append("Power Automate Cloud – Skalerbar for større volum")
    else:
        recommendations.append("Power Automate Desktop – Ideell for lavere volum")
    # File format based
    if filformater:
        f = filformater.lower()
        if "api" in f or api_tilgang.lower() == "ja":
            recommendations.append("API-integrasjon anbefales")
        elif "pdf" in f:
            recommendations.append("OCR-funksjonalitet nødvendig (PAD OCR/AI Builder)")
        elif "excel" in f or "csv" in f:
            recommendations.append("Desktop flow anbefales")
        elif "web" in f or "browser" in f:
            recommendations.append("Web automation i Power Automate")
    # Integration complexity
    if "Legacy" in integrasjon_vanskelighet:
        recommendations.append("Skjermskraping med PAD")
    elif "Komplekse" in integrasjon_vanskelighet:
        recommendations.append("Cloud flows + API-integrasjon")
    return "; ".join(recommendations[:3])  # Return top 3

def get_automation_complexity_score(teknisk_kompleksitet, integrasjon_vanskelighet, endringsledelse_pavirkning):
    """Beregner automatiseringskompleksitet (1-5 skala)"""
    integrasjon_score = {
        "Lav - Standard API/Excel": 1,
        "Medium - Noe tilpasning nødvendig": 2,
        "Høy - Komplekse integrasjoner": 4,
        "Meget høy - Legacy systemer": 5
    }.get(integrasjon_vanskelighet, 3)
    endring_score = {
        "Minimal - Ingen endring i daglige rutiner": 1,
        "Lav - Små justeringer i arbeidsflyt": 2,
        "Medium - Noe opplæring nødvendig": 3,
        "Høy - Betydelig prosessendring": 4
    }.get(endringsledelse_pavirkning, 2)
    combined_complexity = min(5, round((teknisk_kompleksitet + integrasjon_score + endring_score) / 3))
    return combined_complexity

def get_seasonal_priority_boost(sesong_mønster):
    """Gir prioritetsboost basert på sesongmønster"""
    current_month = datetime.now().month
    boosts = {
        "Høy aktivitet Q4": 0.5 if current_month in [10, 11, 12] else 0,
        "Høy aktivitet Q1": 0.5 if current_month in [1, 2, 3] else 0,
        "Høy aktivitet sommer": 0.5 if current_month in [6, 7, 8] else 0,
        "Høy aktivitet vinter": 0.5 if current_month in [12, 1, 2] else 0,
        "Månedlige topper": 0.3,
        "Stabilt hele året": 0.2
    }
    return boosts.get(sesong_mønster, 0)

def get_business_criticality_score(forretningskritikalitet):
    """Konverterer forretningskritikalitet til numerisk score"""
    scores = {
        "Støttefunksjon": 2,
        "Viktig for daglig drift": 3,
        "Kritisk for kundeservice": 4,
        "Regulatorisk påkrevd": 5
    }
    return scores.get(forretningskritikalitet, 3)

# --- STREAMLIT APP ---
def main():
    st.title("RPA Prosessevaluering")
    st.markdown("---")
    
    # Test Supabase connection
    try:
        create_table_if_not_exists()
    except Exception as e:
        st.error(f"Could not connect to Supabase: {str(e)}")
        return
    
    # Initialisering av session state
    if 'df' not in st.session_state:
        st.session_state.df = last_data()
    if 'rediger_index' not in st.session_state:
        st.session_state.rediger_index = None
    if 'vis_side' not in st.session_state:
        st.session_state.vis_side = "Hovedside"
    
    # Navigasjon
    col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 8])
    with col_nav1:
        if st.button("📊 Hovedside"):
            st.session_state.vis_side = "Hovedside"
    with col_nav2:
        if st.button("📈 Visualisering"):
            st.session_state.vis_side = "Visualisering"
    
    if st.session_state.vis_side == "Hovedside":
        vis_hovedside()
    elif st.session_state.vis_side == "Visualisering":
        vis_visualisering()

def vis_hovedside():
    """Viser hovedsiden med prosessregistrering og oversikt"""
    col1, col2 = st.columns([1, 1.5])

    # --- VENSTRE KOLONNE: Prosessregistrering ---
    with col1:
        st.subheader("📝 Prosessregistrering")

        # Sjekk om vi er i redigeringsmodus
        rediger_mode = st.session_state.rediger_index is not None
        if rediger_mode:
            current_row = st.session_state.df.iloc[st.session_state.rediger_index]
            st.info(f"Redigerer prosess: {current_row['prosessnavn']}")
            if st.button("❌ Avbryt redigering"):
                st.session_state.rediger_index = None
                st.rerun()

        # Hent verdier for redigering
        def get_val(col, default):
            return get_val_safe(st.session_state.df, st.session_state.rediger_index, col, default)

        # Grunnleggende informasjon
        st.markdown("**Grunnleggende informasjon**")
        prosessnavn = st.text_input("Prosessnavn*", value=get_val('prosessnavn', ""))
        prosesseier = st.text_input("Prosesseier*", value=get_val('prosesseier', ""))
        avdeling = st.text_input("Avdeling/seksjon*", value=get_val('avdeling', ""))
        prosessbeskrivelse = st.text_area("Beskrivelse*", value=get_val('prosessbeskrivelse', ""))

        col1a, col1b = st.columns(2)
        with col1a:
            trigger = st.text_input("Utløser", value=get_val('trigger', ""))
        with col1b:
            frekvens = st.selectbox("Frekvens",
                ["Daglig", "Ukentlig", "Månedlig", "Ved behov", "Sesongbasert"],
                index=["Daglig", "Ukentlig", "Månedlig", "Ved behov", "Sesongbasert"].index(get_val('frekvens', "Daglig"))
            )

        # Kvantitative data
        st.markdown("**Kvantitative data**")
        col2a, col2b = st.columns(2)
        with col2a:
            antall_prosesser = st.number_input("Antall per måned*", min_value=0, value=int(get_val('antall_prosesser', 0)))
            personer_involvert = st.number_input("Personer involvert", min_value=1, value=int(get_val('personer_involvert', 1)))
        with col2b:
            behandlingstid = st.number_input("Behandlingstid (min)*", min_value=0, value=int(get_val('behandlingstid', 0)))
            feilrate = st.number_input("Feilrate (%)", min_value=0.0, max_value=100.0, value=float(get_val('feilrate', 0.0)), step=0.1)

        kostnad_per_time = st.number_input("Kostnad per time (kr)", min_value=0, value=int(get_val('kostnad_per_time', 500)))

        # Teknisk informasjon
        st.markdown("**Teknisk informasjon**")
        it_systemer = st.text_area("IT-systemer", value=get_val('it_systemer', ""))
        datakilder = st.text_area("Datakilder", value=get_val('datakilder', ""))
        filformater = st.text_area("Filformater", value=get_val('filformater', ""))
        api_tilgang = st.selectbox("API-tilgang", ["Ja", "Nei", "Ukjent"],
            index=["Ja", "Nei", "Ukjent"].index(get_val('api_tilgang', "Ja"))
        )

        # --- Endringsutfordringer (organisatorisk) MÅ komme før scoreberegningen! ---
        st.markdown("**Endringsutfordringer (organisatorisk)**")
        col_change1, col_change2 = st.columns(2)
        with col_change1:
            brukeropplaering = st.selectbox(
                "Opplæringsbehov for brukere",
                ["Minimal opplæring", "Kort introduksjon", "Strukturert opplæring", "Omfattende opplæring"],
                index=["Minimal opplæring", "Kort introduksjon", "Strukturert opplæring", "Omfattende opplæring"].index(get_val('brukeropplaering', "Kort introduksjon"))
            )
            prosessendring = st.selectbox(
                "Grad av prosessendring",
                ["Ingen endring", "Små justeringer", "Moderate endringer", "Betydelige endringer"],
                index=["Ingen endring", "Små justeringer", "Moderate endringer", "Betydelige endringer"].index(get_val('prosessendring', "Små justeringer"))
            )
        with col_change2:
            motstand_forventet = st.selectbox(
                "Forventet motstand",
                ["Ingen motstand", "Lav motstand", "Moderat motstand", "Høy motstand"],
                index=["Ingen motstand", "Lav motstand", "Moderat motstand", "Høy motstand"].index(get_val('motstand_forventet', "Lav motstand"))
            )

        # --- Beregn scores NÅ, etter at alle inputfelt er deklarert ---
        auto_tid, auto_vol, auto_kval, auto_tek, auto_datakompleksitet, auto_regel = beregn_kvantitative_scores(
            behandlingstid, antall_prosesser, feilrate, personer_involvert, kostnad_per_time,
            filformater, datakilder, api_tilgang, brukeropplaering, prosessendring, motstand_forventet
        )
        tidsbesparelse = auto_tid
        volum = auto_vol
        kvalitetsforbedring = auto_kval
        teknisk_kompleksitet = auto_tek
        datakompleksitet = auto_datakompleksitet
        regelstabilitet = auto_regel

        # ROI/analyse-felt
        st.markdown("**Avansert RPA-analyse**")
        col_roi1, col_roi2 = st.columns(2)
        with col_roi1:
            estimert_implementeringstid = st.number_input(
                "Estimert implementeringstid (måneder)",
                min_value=1, max_value=24,
                value=int(get_val('estimert_implementeringstid', 3))
            )
            implementeringskostnad = st.number_input(
                "Implementeringskostnad (kr)",
                min_value=0,
                value=int(get_val('implementeringskostnad', 0))
            )
        with col_roi2:
            vedlikeholdskostnad_aar = st.number_input(
                "Årlige driftskostnader (kr)",
                min_value=0,
                value=int(get_val('vedlikeholdskostnad_aar', 0))
            )
            lisenskostnad_aarlig = st.number_input(
                "Årlige lisenskostnader (kr)",
                min_value=0,
                value=int(get_val('lisenskostnad_aarlig', 0))
            )

        # Seasonal Analysis
        st.markdown("**Sesonganalyse**")
        sesong_variasjon = st.selectbox(
            "Sesongvariasjon i prosessvolum",
            ["Ingen variasjon", "Lav variasjon (±20%)", "Moderat variasjon (±50%)", "Høy variasjon (±100%)", "Ekstrem variasjon (>100%)"],
            index=["Ingen variasjon", "Lav variasjon (±20%)", "Moderat variasjon (±50%)", "Høy variasjon (±100%)", "Ekstrem variasjon (>100%)"].index(get_val('sesong_variasjon', "Ingen variasjon"))
        )
        peak_perioder = st.text_input(
            "Peak-perioder (f.eks. 'Q4, Januar, Juni')",
            value=get_val('peak_perioder', "")
        )

        # Integration Difficulty
        st.markdown("**Integrasjonsutfordringer**")
        col_int1, col_int2 = st.columns(2)
        with col_int1:
            antall_systemer = st.number_input(
                "Antall IT-systemer involvert",
                min_value=1, max_value=20,
                value=int(get_val('antall_systemer', 2))
            )
            api_tilgjengelighet = st.selectbox(
                "API-tilgjengelighet",
                ["Alle systemer har API", "De fleste har API", "Noen har API", "Få har API", "Ingen API"],
                index=["Alle systemer har API", "De fleste har API", "Noen har API", "Få har API", "Ingen API"].index(get_val('api_tilgjengelighet', "Noen har API"))
            )
        with col_int2:
            sikkerhetskrav = st.selectbox(
                "Sikkerhetskrav",
                ["Lavt", "Medium", "Høyt", "Kritisk"],
                index=["Lavt", "Medium", "Høyt", "Kritisk"].index(get_val('sikkerhetskrav', "Medium"))
            )
            testmiljo_tilgang = st.selectbox(
                "Testmiljø tilgjengelighet",
                ["Fullt tilgjengelig", "Begrenset tilgang", "Ikke tilgjengelig"],
                index=["Fullt tilgjengelig", "Begrenset tilgang", "Ikke tilgjengelig"].index(get_val('testmiljo_tilgang', "Fullt tilgjengelig"))
            )

        # Prioriteringsmatrise
        st.markdown("**Prioriteringsmatrise (1-5) - Automatisk beregnet fra kvantitative data**")
        col3a, col3b = st.columns(2)
        with col3a:
            st.markdown("**Gevinst-relaterte faktorer:**")
            st.info(f"🕒 **Tidsbesparelse:** {tidsbesparelse}/5\n(Basert på {behandlingstid} min behandlingstid)")
            st.info(f"📊 **Volum:** {volum}/5\n(Basert på {antall_prosesser} prosesser/måned)")
            forklaring_kvalitet = []
            if brukeropplaering in ["Kort introduksjon", "Strukturert opplæring"]:
                forklaring_kvalitet.append("Lett opplæring (+1)")
            if prosessendring == "Små justeringer":
                forklaring_kvalitet.append("Små endringer (+1)")
            if motstand_forventet == "Lav motstand":
                forklaring_kvalitet.append("Lav motstand (+1)")
            kvalitet_tekst = f"✅ **Kvalitetsforbedring:** {kvalitetsforbedring}/5"
            if forklaring_kvalitet:
                kvalitet_tekst += f"\n({', '.join(forklaring_kvalitet)})"
            st.info(kvalitet_tekst)

        with col3b:
            st.markdown("**Gjennomførbarhet-relaterte faktorer:**")
            st.info(f"🔧 **Teknisk kompleksitet:** {teknisk_kompleksitet}/5\n(Basert på filformater)")
            antall_datakilder = len([x.strip() for x in datakilder.split(',') if x.strip()]) if datakilder else 0
            antall_filformater = len([x.strip() for x in filformater.split(',') if x.strip()]) if filformater else 0

            kompleksitet_detaljer = []
            if antall_datakilder > 1:
                kompleksitet_detaljer.append(f"{antall_datakilder} datakilder")
            elif antall_datakilder == 1:
                kompleksitet_detaljer.append("1 datakilde")

            if antall_filformater > 1:
                kompleksitet_detaljer.append(f"{antall_filformater} filformater")
            elif antall_filformater == 1:
                kompleksitet_detaljer.append("1 filformat")

            if api_tilgang and api_tilgang.lower() == "ja":
                kompleksitet_detaljer.append("API-tilgang")

            # Sett sammen tekst uten kroner
            kompleksitet_tekst = f"💾 **Datakompleksitet:** {datakompleksitet}/5\n(Basert på "
            kompleksitet_tekst += ", ".join(kompleksitet_detaljer) if kompleksitet_detaljer else "enkel struktur"
            kompleksitet_tekst += ")"

            st.info(kompleksitet_tekst)

            st.info(f"📋 **Regelstabilitet:** {regelstabilitet}/5\n(Basert på prosessvolum og behandlingstid)")

        # Strategiske faktorer (kan justeres manuelt)
        st.markdown("**Strategiske faktorer (kan justeres manuelt):**")
        col3c, col3d = st.columns(2)
        with col3c:
            org_pavirkning = st.select_slider("Organisatorisk påvirkning", options=[1,2,3,4,5],
                                              value=int(get_val('org_pavirkning', 3)))
            brukerpavirkning = st.select_slider("Brukerpåvirkning", options=[1,2,3,4,5],
                                                value=int(get_val('brukerpavirkning', 3)))
        with col3d:
            regelverksoverholdelse = st.select_slider("Regelverksoverholdelse", options=[1,2,3,4,5],
                                                      value=int(get_val('regelverksoverholdelse', 3)))

        # Risiko og bonus faktorer
        st.markdown("**Risiko og bonus faktorer**")
        risiko_liste = ["Høy organisatorisk motstand", "Kritiske systemavhengigheter", "Komplekse godkjenningsflyter", "Høy sikkerhetstilgang"]
        bonus_liste = ["Pilot-/proof-of-concept verdi", "Synergieffekter", "Eksisterende systemintegrasjoner"]
        current_risiko_str = get_val('risiko_faktorer', "")
        current_bonus_str = get_val('bonus_faktorer', "")
        current_risiko = [item.strip() for item in current_risiko_str.split(",") if item.strip() in risiko_liste] if current_risiko_str else []
        current_bonus = [item.strip() for item in current_bonus_str.split(",") if item.strip() in bonus_liste] if current_bonus_str else []
        risiko_faktorer = st.multiselect("Risikofaktorer (-1 poeng hver)", risiko_liste, default=current_risiko)
        bonus_faktorer = st.multiselect("Bonusfaktorer (+1 poeng hver)", bonus_liste, default=current_bonus)

        # Score preview
        temp_data = {
            'tidsbesparelse': tidsbesparelse, 'volum': volum, 'kvalitetsforbedring': kvalitetsforbedring,
            'teknisk_kompleksitet': teknisk_kompleksitet, 'datakompleksitet': datakompleksitet, 'regelstabilitet': regelstabilitet,
            'org_pavirkning': org_pavirkning, 'brukerpavirkning': brukerpavirkning, 'regelverksoverholdelse': regelverksoverholdelse,
            'risiko_faktorer': risiko_faktorer, 'bonus_faktorer': bonus_faktorer,
            'antall_prosesser': antall_prosesser, 'behandlingstid': behandlingstid, 'feilrate': feilrate
        }
        scoring = beregn_prioritering(temp_data)
        prioritet = get_prioritet_kategori(scoring['justert_score'])
        st.info(f"**Prioritet:** {prioritet}  \n**Score:** {scoring['justert_score']}/10  \n**Gevinst:** {scoring['gevinst_score']}/10 | **Gjennomførbarhet:** {scoring['gjennomforbarhet_score']}/10 | **Strategisk:** {scoring['strategisk_score']}/10")

        # Lagre knapp
        if st.button("💾 Lagre prosess", type="primary"):
            arsvolum = to_int(antall_prosesser) * 12
            arslig_tidsbesparing = to_int((arsvolum * to_int(behandlingstid)) / 60)

            # Her bruker vi "realistisk" kalkyle!
            kostnadsbesparelse = beregn_realistisk_kostnadsbesparelse(
                arslig_tidsbesparing,
                to_int(kostnad_per_time),
                to_int(lisenskostnad_aarlig),
                to_int(vedlikeholdskostnad_aar)
            )



            roi_metrics = beregn_roi_metrics(
                kostnadsbesparelse, implementeringskostnad,
                vedlikeholdskostnad_aar, estimert_implementeringstid, 3  # f.eks. 3 år levetid
            )

            roi_metrics = {k: int(round(v)) for k, v in roi_metrics.items()}

            teknologi_anbefaling = get_technology_recommendation(
                filformater, api_tilgang, "Medium - Noe tilpasning nødvendig", antall_prosesser  # Justér evt. felt
            )
            automation_complexity_score = int(get_automation_complexity_score(
                teknisk_kompleksitet, "Medium - Noe tilpasning nødvendig", "Lav - Små justeringer"  # Justér evt. felt
            ))
            seasonal_boost = int(get_seasonal_priority_boost("Stabilt hele året") * 10)
            forretningskritikalitet_score = int(get_business_criticality_score("Viktig for daglig drift"))

            temp_data.update({
                'automation_complexity_score': automation_complexity_score,
                'seasonal_boost': seasonal_boost,
                'forretningskritikalitet_score': forretningskritikalitet_score,
                'roi_percentage': roi_metrics['roi_percentage'],
            })

            lagre_prosess(
                prosessnavn, prosesseier, avdeling, prosessbeskrivelse, trigger, frekvens,
                antall_prosesser, behandlingstid, personer_involvert, feilrate, kostnad_per_time,
                it_systemer, datakilder, filformater, api_tilgang, tidsbesparelse, volum,
                kvalitetsforbedring, teknisk_kompleksitet, datakompleksitet, regelstabilitet,
                org_pavirkning, brukerpavirkning, regelverksoverholdelse, risiko_faktorer,
                bonus_faktorer, scoring, prioritet, rediger_mode,
                estimert_implementeringstid, implementeringskostnad, vedlikeholdskostnad_aar, lisenskostnad_aarlig, 3,  # forventet_levetid_aar (juster evt. felt)
                "Medium - Noe tilpasning nødvendig", "Lav - Små justeringer", "Stabilt hele året", "Viktig for daglig drift",
                teknologi_anbefaling, automation_complexity_score, seasonal_boost, forretningskritikalitet_score,
                roi_metrics
            )

    # --- HØYRE KOLONNE: Oversikt ---
    with col2:
        vis_oversikt()


def lagre_prosess(
    prosessnavn, prosesseier, avdeling, prosessbeskrivelse, trigger, frekvens,
    antall_prosesser, behandlingstid, personer_involvert, feilrate, kostnad_per_time,
    it_systemer, datakilder, filformater, api_tilgang, tidsbesparelse, volum,
    kvalitetsforbedring, teknisk_kompleksitet, datakompleksitet, regelstabilitet,
    org_pavirkning, brukerpavirkning, regelverksoverholdelse, risiko_faktorer,
    bonus_faktorer, scoring, prioritet, rediger_mode,
    estimert_implementeringstid, implementeringskostnad, vedlikeholdskostnad_aar, lisenskostnad_aarlig, forventet_levetid_aar,
    integrasjon_vanskelighet, endringsledelse_pavirkning, sesong_mönster, forretningskritikalitet,
    teknologi_anbefaling, automation_complexity_score, seasonal_boost, forretningskritikalitet_score,
    roi_metrics
):
    """Lagrer prosessdata til Supabase inkludert avanserte metrikker (kun int der det kreves)"""

    # --- VALIDERING AV PÅKREVDE FELT ---
    mangler = []
    if not prosessnavn: mangler.append("Prosessnavn")
    if not prosesseier: mangler.append("Prosesseier")
    if not avdeling: mangler.append("Avdeling")
    if not prosessbeskrivelse: mangler.append("Beskrivelse")
    if not antall_prosesser: mangler.append("Antall per måned")
    if not behandlingstid: mangler.append("Behandlingstid")
    if mangler:
        st.error(f"Følgende felt mangler: {', '.join(mangler)}")
        return

    # --- TALLFELT - STRIKT INT ENFORCEMENT ---
    def to_int(x):
        try:
            return int(round(float(x)))
        except Exception:
            return 0

    # --- BEREGNDE VERDIER ---
    arsvolum = to_int(antall_prosesser) * 12
    arslig_tidsbesparing = to_int((arsvolum * to_int(behandlingstid)) / 60)
    kostnadsbesparelse = to_int(arslig_tidsbesparing * to_int(kostnad_per_time))
    feilrate_int = to_int(feilrate)

    # --- ROI METRIKKER (bruker int) ---
    roi_dict = {k: to_int(v) for k, v in roi_metrics.items()}

    # --- LAG DATA-DICT ---
    data_dict = {
        'prosessnavn': prosessnavn,
        'prosesseier': prosesseier,
        'avdeling': avdeling,
        'prosessbeskrivelse': prosessbeskrivelse,
        'trigger': trigger,
        'frekvens': frekvens,
        'antall_prosesser': to_int(antall_prosesser),
        'behandlingstid': to_int(behandlingstid),
        'personer_involvert': to_int(personer_involvert),
        'feilrate': feilrate_int,
        'kostnad_per_time': to_int(kostnad_per_time),
        'arsvolum': to_int(arsvolum),
        'arslig_tidsbesparing': to_int(arslig_tidsbesparing),
        'kostnadsbesparelse': to_int(kostnadsbesparelse),
        'it_systemer': it_systemer,
        'datakilder': datakilder,
        'filformater': filformater,
        'api_tilgang': api_tilgang,
        'tidsbesparelse': to_int(tidsbesparelse),
        'volum': to_int(volum),
        'kvalitetsforbedring': to_int(kvalitetsforbedring),
        'teknisk_kompleksitet': to_int(teknisk_kompleksitet),
        'datakompleksitet': to_int(datakompleksitet),
        'regelstabilitet': to_int(regelstabilitet),
        'org_pavirkning': to_int(org_pavirkning),
        'brukerpavirkning': to_int(brukerpavirkning),
        'regelverksoverholdelse': to_int(regelverksoverholdelse),
        'gevinst_score': to_int(scoring['gevinst_score']),
        'gjennomforbarhet_score': to_int(scoring['gjennomforbarhet_score']),
        'strategisk_score': to_int(scoring['strategisk_score']),
        'total_score': to_int(scoring['total_score']),
        'justert_score': to_int(scoring['justert_score']),
        'volum_bonus': to_int(scoring['volum_bonus']),
        'prioritet': prioritet,
        'risiko_faktorer': risiko_faktorer,
        'bonus_faktorer': bonus_faktorer,
        'registrert_dato': datetime.now().isoformat(),

        # --- NYE FELTER (Alle int, der det gir mening) ---
        'estimert_implementeringstid': to_int(estimert_implementeringstid),
        'implementeringskostnad': to_int(implementeringskostnad),
        'vedlikeholdskostnad_aar': to_int(vedlikeholdskostnad_aar),
        'lisenskostnad_aarlig': to_int(lisenskostnad_aarlig),
        'forventet_levetid_aar': to_int(forventet_levetid_aar),
        'integrasjon_vanskelighet': integrasjon_vanskelighet,
        'endringsledelse_pavirkning': endringsledelse_pavirkning,
        'sesong_mönster': sesong_mönster,
        'forretningskritikalitet': forretningskritikalitet,
        'teknologi_anbefaling': teknologi_anbefaling,
        'automation_complexity_score': to_int(automation_complexity_score),
        'seasonal_boost': to_int(seasonal_boost),
        'forretningskritikalitet_score': to_int(forretningskritikalitet_score),

        # --- ROI metrics ---
        'roi_percentage': roi_dict.get('roi_percentage', 0),
        'payback_months': roi_dict.get('payback_months', 0),
        'npv': roi_dict.get('npv', 0),
        'total_besparelser': roi_dict.get('total_besparelser', 0),
        'total_kostnader': roi_dict.get('total_kostnader', 0),
    }

    # --- LAGRE ELLER OPPDATERE ---
    if rediger_mode:
        current_row = st.session_state.df.iloc[st.session_state.rediger_index]
        prosess_id = current_row['id']
        if oppdater_data_in_supabase(prosess_id, data_dict):
            st.success(f"Prosess '{prosessnavn}' er oppdatert!")
            st.session_state.rediger_index = None
            st.session_state.df = last_data()
        else:
            st.error("Kunne ikke oppdatere prosessen i databasen")
    else:
        if lagre_data_to_supabase(data_dict):
            st.success(f"Prosess '{prosessnavn}' er lagret!")
            st.session_state.df = last_data()
        else:
            st.error("Kunne ikke lagre prosessen i databasen")

    st.rerun()



def vis_oversikt():
    """Viser oversikt over prosesser"""
    st.subheader("📊 Prosessoversikt")
    
    df = st.session_state.df
    
    if df.empty:
        st.info("Ingen prosesser registrert ennå.")
        return

    # Filtrering (move this BEFORE the metrics)
    st.markdown("**Filtrer prosesser**")
    col1, col2, col3 = st.columns(3)
    with col1:
        avd_filter = st.selectbox("Avdeling", ["Alle"] + sorted(df['avdeling'].dropna().unique().tolist()))
    with col2:
        prioritet_filter = st.selectbox("Prioritet", ["Alle"] + sorted(df['prioritet'].dropna().unique().tolist()))
    with col3:
        min_score = st.slider("Minimum score", 0.0, 10.0, 0.0)

    # Apply filters to get filtered dataframe
    filtered_df = df.copy()
    if avd_filter != "Alle":
        filtered_df = filtered_df[filtered_df['avdeling'] == avd_filter]
    if prioritet_filter != "Alle":
        filtered_df = filtered_df[filtered_df['prioritet'] == prioritet_filter]
    filtered_df = filtered_df[pd.to_numeric(filtered_df['justert_score'], errors='coerce') >= min_score]

    # Dynamic metrics based on filters
    if not filtered_df.empty:
        # Calculate metrics for filtered data
        antall_prosesser = len(filtered_df)
        total_besparelse = filtered_df.apply(
            lambda row: beregn_realistisk_kostnadsbesparelse(
                row['arslig_tidsbesparing'],
                row['kostnad_per_time'],
                row.get('lisenskostnad_aarlig', 0),
                row.get('vedlikeholdskostnad_aar', 0)
            ),
            axis=1
        ).sum()

        total_tid = pd.to_numeric(filtered_df['arslig_tidsbesparing'], errors='coerce').sum()
        hoy_prioritet = filtered_df['prioritet'].str.contains("HØY", na=False).sum()
        
        # Create dynamic title based on filters
        title_parts = []
        if avd_filter != "Alle":
            title_parts.append(f"Avdeling: {avd_filter}")
        if prioritet_filter != "Alle":
            title_parts.append(f"Prioritet: {prioritet_filter}")
        if min_score > 0:
            title_parts.append(f"Min score: {min_score}")
        
        if title_parts:
            filter_title = " | ".join(title_parts)
            st.subheader(f"📊 Prosessoversikt - {filter_title}")
        else:
            st.subheader("📊 Prosessoversikt - Alle prosesser")
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Antall prosesser", antall_prosesser)
        with col2:
            st.metric("Årlig besparelse",
                f"{total_besparelse:,.0f} kr",
                help="Dette tallet inkluderer arbeidsgiveravgift og fratrekk for årlige lisenskostnader og driftskostnader."
            )

        with col3:
            st.metric("Tidsbesparing", f"{total_tid:,.0f} timer/år")
        with col4:
            st.metric("Høy prioritet", hoy_prioritet)
        
        # Additional breakdown if showing all data
        if avd_filter == "Alle" and prioritet_filter == "Alle" and min_score == 0:
            st.markdown("---")
            st.subheader("📈 Detaljert oversikt")
            
            
        
      # 1. Start med kopi av alle relevante rader
        display_df = filtered_df.copy()

        # 2. Realistisk besparelse-kolonne
        def beregn_realistisk_besparelse_rad(row):
            return beregn_realistisk_kostnadsbesparelse(
                row['arslig_tidsbesparing'],
                row['kostnad_per_time'],
                row.get('lisenskostnad_aarlig', 0),
                row.get('vedlikeholdskostnad_aar', 0)
            )

        display_df['Årlig besparelse (inkl. arb.g.avg., lisens, drift)'] = display_df.apply(beregn_realistisk_besparelse_rad, axis=1)
        display_df['Årlig besparelse (inkl. arb.g.avg., lisens, drift)'] = display_df['Årlig besparelse (inkl. arb.g.avg., lisens, drift)'].apply(lambda x: f"{x:,.0f} kr")
        display_df['arslig_tidsbesparing'] = pd.to_numeric(display_df['arslig_tidsbesparing'], errors='coerce').apply(lambda x: f"{x:,.0f} timer")
        display_df['justert_score'] = pd.to_numeric(display_df['justert_score'], errors='coerce').round(1)

        # 3. Velg kolonner til visning til slutt!
        display_cols = [
            'prosessnavn',
            'avdeling',
            'prioritet',
            'justert_score',
            'Årlig besparelse (inkl. arb.g.avg., lisens, drift)',
            'arslig_tidsbesparing'
        ]
        st.dataframe(display_df[display_cols], use_container_width=True)

        
        # Rediger og slett knapper
        st.markdown("**Rediger/Slett prosesser**")
        for idx, row in filtered_df.iterrows():
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                st.write(f"**{row['prosessnavn']}** - {row['avdeling']} - {row['prioritet']}")
            with col2:
                if st.button("✏️", key=f"edit_{idx}", help="Rediger"):
                    # Find the index in the original dataframe
                    original_idx = df[df['id'] == row['id']].index[0]
                    st.session_state.rediger_index = original_idx
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_{idx}", help="Slett"):
                    if slett_prosess_from_supabase(row['id']):
                        st.success(f"Prosess '{row['prosessnavn']}' er slettet!")
                        st.session_state.df = last_data()
                        st.rerun()
                    else:
                        st.error("Kunne ikke slette prosessen")

    else:
        st.info("Ingen prosesser matcher filterkriteriene.")

def vis_visualisering():
    """Viser visualiseringer og analyse"""
    st.subheader("📈 Visualisering og analyse")
    
    df = st.session_state.df
    
    if df.empty:
        st.info("Ingen prosesser registrert ennå. Gå til hovedsiden for å registrere prosesser.")
        return
    
    # Konverter numeriske kolonner
    numeric_cols = ['justert_score', 'kostnadsbesparelse', 'arslig_tidsbesparing', 'antall_prosesser', 'behandlingstid']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Create color palette for departments
    unique_departments = df['avdeling'].unique()
    # Din tilpassede palett uten gult:
    department_colors = [
        "#8dd3c7", "#fb8072", "#80b1d3", "#bc80bd", "#bebada",
        "#d9d9d9", "#fccde5", "#ccebc5", "#bcbd22", "#ff7f00",
        "#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#cab2d6",
        "#6a3d9a"
    ]  # Fjernet gule (#ffff99, #fdb462, #b3de69, #ffb3b3)

    dept_color_map = {dept: department_colors[i % len(department_colors)] for i, dept in enumerate(unique_departments)}

    
    # Visualiseringer
    col1, col2 = st.columns(2)  
    
    with col1:
        # Prioritetsfordeling
        st.subheader("Prioritetsfordeling")
        prioritet_counts = df['prioritet'].value_counts()
        priority_colors = ["#F52727", "#F2F52B", '#4ECDC4', '#E8E8E8']
        fig_pie = px.pie(
            values=prioritet_counts.values, 
            names=prioritet_counts.index,
            title="Fordeling av prioritetskategorier",
            color_discrete_sequence=priority_colors
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Avdelingsfordeling with department colors
        st.subheader("Avdelingsfordeling")
        avd_counts = df['avdeling'].value_counts()
        fig_bar = px.bar(
            x=avd_counts.index, 
            y=avd_counts.values,
            title="Antall prosesser per avdeling",
            labels={'x': 'Avdeling', 'y': 'Antall prosesser'},
            color=avd_counts.index,
            color_discrete_map=dept_color_map
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Score analyse
    st.subheader("Score-analyse")
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter plot: Gevinst vs Gjennomførbarhet colored by department
        fig_scatter = px.scatter(
            df, 
            x='gjennomforbarhet_score', 
            y='gevinst_score',
            size='justert_score',
            color='avdeling',  # Changed from 'prioritet' to 'avdeling'
            hover_data=['prosessnavn', 'prioritet'],
            title="Gevinst vs Gjennomførbarhet (farget etter avdeling)",
            labels={'gjennomforbarhet_score': 'Gjennomførbarhet', 'gevinst_score': 'Gevinst'},
            color_discrete_map=dept_color_map
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # Top 10 prosesser etter score colored by department
        st.subheader("Top 10 prosesser")
        top_prosesser = df.nlargest(10, 'justert_score')[['prosessnavn', 'justert_score', 'prioritet', 'avdeling']]
        fig_top = px.bar(
            top_prosesser,
            x='justert_score',
            y='prosessnavn',
            orientation='h',
            color='avdeling',  # Changed from 'prioritet' to 'avdeling'
            title="Topp 10 prosesser etter score (farget etter avdeling)",
            color_discrete_map=dept_color_map
        )
        st.plotly_chart(fig_top, use_container_width=True)
    
    # Økonomisk analyse
    st.subheader("Økonomisk analyse")
    col1, col2 = st.columns(2)
    
    with col1:
        # Kostnadsbesparelse per avdeling with consistent colors
        kostnader_avd = df.groupby('avdeling')['kostnadsbesparelse'].sum().sort_values(ascending=False)
        fig_kostnad = px.bar(
            x=kostnader_avd.index,
            y=kostnader_avd.values,
            title="Potensiell årlig kostnadsbesparelse per avdeling",
            labels={'x': 'Avdeling', 'y': 'Kostnadsbesparelse (kr)'},
            color=kostnader_avd.index,
            color_discrete_map=dept_color_map
        )
        st.plotly_chart(fig_kostnad, use_container_width=True)
    
    with col2:
        # Tidsbesparing vs Kostnadsbesparelse colored by department
        fig_tid_kostnad = px.scatter(
            df,
            x='arslig_tidsbesparing',
            y='kostnadsbesparelse',
            size='justert_score',
            color='avdeling',  # Changed from 'prioritet' to 'avdeling'
            hover_data=['prosessnavn', 'prioritet'],
            title="Tidsbesparing vs Kostnadsbesparelse (farget etter avdeling)",
            labels={'arslig_tidsbesparing': 'Årlig tidsbesparing (timer)', 'kostnadsbesparelse': 'Kostnadsbesparelse (kr)'},
            color_discrete_map=dept_color_map
        )
        st.plotly_chart(fig_tid_kostnad, use_container_width=True)
    
    # Detaljert analyse
    st.subheader("Detaljert analyse")
    
    # Korrelasjonsanalyse
    correlation_cols = ['justert_score', 'gevinst_score', 'gjennomforbarhet_score', 'strategisk_score', 
                       'antall_prosesser', 'behandlingstid', 'kostnadsbesparelse', 'arslig_tidsbesparing']
    
    corr_df = df[correlation_cols].corr()
    
    fig_heatmap = px.imshow(
        corr_df,
        text_auto=True,
        aspect="auto",
        title="Korrelasjonsmatrise",
        color_continuous_scale='RdBu'
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Sammendrag statistikk
    st.subheader("Sammendrag statistikk")
    
    summary_stats = df[['justert_score', 'kostnadsbesparelse', 'arslig_tidsbesparing', 'antall_prosesser', 'behandlingstid']].describe()
    st.dataframe(summary_stats)
    
    # Eksport funksjonalitet
    st.subheader("Eksport data")
    col1 = st.columns(1)[0]
    
    with col1:
        if st.button("📥 Last ned CSV"):
            csv = df.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="Last ned prosessdata som CSV",
                data=csv,
                file_name=f"rpa_prosesser_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

# Kjør app
if __name__ == "__main__":
    main()




