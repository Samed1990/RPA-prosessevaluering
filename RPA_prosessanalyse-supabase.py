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
    page_icon=" ",
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
    datastruktur INTEGER,
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
            'datastruktur', 'regelstabilitet', 'org_pavirkning', 'brukerpavirkning', 'regelverksoverholdelse',
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
            'datastruktur', 'regelstabilitet', 'org_pavirkning', 'brukerpavirkning', 'regelverksoverholdelse',
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
def beregn_prioritering(data):
    """Beregner prioriteringsscore basert på inputdata med maks 10 poeng"""
    # Hovedscores (1-5 hver)
    gevinst = (data['tidsbesparelse'] * 0.4 + data['volum'] * 0.4 + data['kvalitetsforbedring'] * 0.2) * 2  # Maks 10
    gjennomforbarhet = (data['teknisk_kompleksitet'] * 0.3 + data['datastruktur'] * 0.4 + data['regelstabilitet'] * 0.3) * 2  # Maks 10
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

def beregn_kvantitative_scores(behandlingstid, antall_prosesser, feilrate, personer_involvert, kostnad_per_time, filformater):
    """Beregner automatiske scores basert på kvantitative data - høyere verdier gir høyere score"""
    
    # Tidsbesparelse score basert på behandlingstid (høyere tid = høyere score)
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
    
    # Volum score basert på antall prosesser per måned (høyere volum = høyere score)
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
    
    # Kvalitetsforbedring score basert på feilrate (høyere feilrate = høyere score)
    if feilrate >= 20:
        kvalitet_score = 5
    elif feilrate >= 15:
        kvalitet_score = 4
    elif feilrate >= 10:
        kvalitet_score = 3
    elif feilrate >= 5:
        kvalitet_score = 2
    else:
        kvalitet_score = 1
    
    # Teknisk kompleksitet basert på filformater og antall personer (høyere kompleksitet = lavere score)
    teknisk_score = 3  # Default medium
    if filformater:
        f = filformater.lower()
        if "pdf" in f or "word" in f or "docx" in f:
            teknisk_score = 5  # Strukturerte dokumenter er lettere å automatisere
        elif "excel" in f or "xlsx" in f or "csv" in f:
            teknisk_score = 4  # Strukturerte data er relativt enkle
        elif "xml" in f or "json" in f:
            teknisk_score = 3  # Strukturerte data men mer komplekse
        elif "api" in f:
            teknisk_score = 2  # API krever mer teknisk arbeid
        else:
            teknisk_score = 3  # Default for ukjente formater
    
    # Juster basert på personer involvert (flere personer = lavere score pga kompleksitet)
    if personer_involvert >= 10:
        teknisk_score = max(1, teknisk_score - 2)
    elif personer_involvert >= 5:
        teknisk_score = max(1, teknisk_score - 1)
    
    # Datastruktur score basert på kostnad per time (høyere kostnad = høyere potensial)
    if kostnad_per_time >= 1200:
        datastruktur_score = 5  # Høy kostnad = høy besparelsespotensial
    elif kostnad_per_time >= 900:
        datastruktur_score = 4
    elif kostnad_per_time >= 600:
        datastruktur_score = 3
    elif kostnad_per_time >= 400:
        datastruktur_score = 2
    else:
        datastruktur_score = 1
    
    # Regelstabilitet basert på frekvens og behandlingstid (mer stabile prosesser = høyere score)
    if behandlingstid >= 60 and antall_prosesser >= 100:
        regelstabilitet_score = 5  # Lange, hyppige prosesser er vanligvis stabile
    elif behandlingstid >= 30 and antall_prosesser >= 50:
        regelstabilitet_score = 4
    elif behandlingstid >= 15 or antall_prosesser >= 20:
        regelstabilitet_score = 3
    else:
        regelstabilitet_score = 2
    
    return tidsbesparelse_score, volum_score, kvalitet_score, teknisk_score, datastruktur_score, regelstabilitet_score

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

# --- STREAMLIT APP ---
def main():
    st.title("🤖 RPA Prosessevaluering (Database hostes på Supabase)")
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
            if rediger_mode:
                val = st.session_state.df.iloc[st.session_state.rediger_index][col]
                return default if pd.isna(val) else val
            return default
        
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
                                  index=["Daglig", "Ukentlig", "Månedlig", "Ved behov", "Sesongbasert"].index(get_val('frekvens', "Daglig")))
        
        # Kvantitative data
        st.markdown("**Kvantitative data**")
        col2a, col2b = st.columns(2)
        with col2a:
            antall_prosesser = st.number_input("Antall per måned*", min_value=0, value=int(get_val('antall_prosesser', 0)))
            personer_involvert = st.number_input("Personer involvert", min_value=1, value=int(get_val('personer_involvert', 1)))
        with col2b:
            behandlingstid = st.number_input("Behandlingstid (min)*", min_value=0, value=int(get_val('behandlingstid', 0)))
            feilrate = st.number_input("Feilrate (%)", min_value=0.0, max_value=100.0, value=float(get_val('feilrate', 0.0)), step=0.1)
        
        kostnad_per_time = st.number_input("Kostnad per time (kr)", min_value=0, value=int(get_val('kostnad_per_time', 600)))
        
        # Teknisk informasjon
        st.markdown("**Teknisk informasjon**")
        it_systemer = st.text_area("IT-systemer", value=get_val('it_systemer', ""))
        datakilder = st.text_area("Datakilder", value=get_val('datakilder', ""))
        filformater = st.text_area("Filformater", value=get_val('filformater', ""))
        api_tilgang = st.selectbox("API-tilgang", ["Ja", "Nei", "Ukjent"], 
                                 index=["Ja", "Nei", "Ukjent"].index(get_val('api_tilgang', "Ja")))
        
        # Prioriteringsmatrise (automatically calculated from quantitative data)
        st.markdown("**Prioriteringsmatrise (1-5) - Automatisk beregnet fra kvantitative data**")

        # Calculate automatic values based on quantitative data
        auto_tid, auto_vol, auto_kval, auto_tek, auto_data, auto_regel = beregn_kvantitative_scores(
            behandlingstid, antall_prosesser, feilrate, personer_involvert, kostnad_per_time, filformater
        )

        # Use automatic values directly (no manual sliders)
        tidsbesparelse = auto_tid
        volum = auto_vol
        kvalitetsforbedring = auto_kval
        teknisk_kompleksitet = auto_tek
        datastruktur = auto_data
        regelstabilitet = auto_regel

        # Display the calculated values in a nice format
        col3a, col3b = st.columns(2)
        with col3a:
            st.markdown("**Gevinst-relaterte faktorer:**")
            st.info(f"🕒 **Tidsbesparelse:** {tidsbesparelse}/5\n(Basert på {behandlingstid} min behandlingstid)")
            st.info(f"📊 **Volum:** {volum}/5\n(Basert på {antall_prosesser} prosesser/måned)")
            st.info(f"✅ **Kvalitetsforbedring:** {kvalitetsforbedring}/5\n(Basert på {feilrate}% feilrate)")

        with col3b:
            st.markdown("**Gjennomførbarhet-relaterte faktorer:**")
            st.info(f"🔧 **Teknisk kompleksitet:** {teknisk_kompleksitet}/5\n(Basert på filformater og {personer_involvert} personer)")
            st.info(f"💾 **Datastruktur:** {datastruktur}/5\n(Basert på {kostnad_per_time} kr/time)")
            st.info(f"📋 **Regelstabilitet:** {regelstabilitet}/5\n(Basert på prosessvolum og behandlingstid)")

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

        # Get current values and clean them up
        current_risiko_str = get_val('risiko_faktorer', "")
        current_bonus_str = get_val('bonus_faktorer', "")

        # Split and clean the strings, filter out invalid options
        current_risiko = []
        if current_risiko_str:
            current_risiko = [item.strip() for item in current_risiko_str.split(",") if item.strip() in risiko_liste]

        current_bonus = []
        if current_bonus_str:
            current_bonus = [item.strip() for item in current_bonus_str.split(",") if item.strip() in bonus_liste]

        risiko_faktorer = st.multiselect("Risikofaktorer (-1 poeng hver)", risiko_liste, default=current_risiko)
        bonus_faktorer = st.multiselect("Bonusfaktorer (+1 poeng hver)", bonus_liste, default=current_bonus)
        
        # Score preview
        temp_data = {
            'tidsbesparelse': tidsbesparelse, 'volum': volum, 'kvalitetsforbedring': kvalitetsforbedring,
            'teknisk_kompleksitet': teknisk_kompleksitet, 'datastruktur': datastruktur, 'regelstabilitet': regelstabilitet,
            'org_pavirkning': org_pavirkning, 'brukerpavirkning': brukerpavirkning, 'regelverksoverholdelse': regelverksoverholdelse,
            'risiko_faktorer': risiko_faktorer, 'bonus_faktorer': bonus_faktorer,
            'antall_prosesser': antall_prosesser, 'behandlingstid': behandlingstid, 'feilrate': feilrate
        }
        
        scoring = beregn_prioritering(temp_data)
        prioritet = get_prioritet_kategori(scoring['justert_score'])
        
        st.info(f"**Prioritet:** {prioritet}  \n**Score:** {scoring['justert_score']}/10  \n**Gevinst:** {scoring['gevinst_score']}/10 | **Gjennomførbarhet:** {scoring['gjennomforbarhet_score']}/10 | **Strategisk:** {scoring['strategisk_score']}/10")
        
        # Lagre knapp
        if st.button("💾 Lagre prosess", type="primary"):
            lagre_prosess(prosessnavn, prosesseier, avdeling, prosessbeskrivelse, trigger, frekvens,
                         antall_prosesser, behandlingstid, personer_involvert, feilrate, kostnad_per_time,
                         it_systemer, datakilder, filformater, api_tilgang, tidsbesparelse, volum,
                         kvalitetsforbedring, teknisk_kompleksitet, datastruktur, regelstabilitet,
                         org_pavirkning, brukerpavirkning, regelverksoverholdelse, risiko_faktorer,
                         bonus_faktorer, scoring, prioritet, rediger_mode)
    
    # --- HØYRE KOLONNE: Oversikt ---
    with col2:
        vis_oversikt()

def lagre_prosess(prosessnavn, prosesseier, avdeling, prosessbeskrivelse, trigger, frekvens,
                 antall_prosesser, behandlingstid, personer_involvert, feilrate, kostnad_per_time,
                 it_systemer, datakilder, filformater, api_tilgang, tidsbesparelse, volum,
                 kvalitetsforbedring, teknisk_kompleksitet, datastruktur, regelstabilitet,
                 org_pavirkning, brukerpavirkning, regelverksoverholdelse, risiko_faktorer,
                 bonus_faktorer, scoring, prioritet, rediger_mode):
    """Lagrer prosessdata til Supabase"""
    
    # Validering
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
    
    # Beregn utledede verdier
    arsvolum = int(antall_prosesser * 12)  # Convert to integer
    arslig_tidsbesparing = float((arsvolum * behandlingstid) / 60)  # Keep as float
    kostnadsbesparelse = float(arslig_tidsbesparing * kostnad_per_time)  # Keep as float
    
    # Opprett datadict
    data_dict = {
        'prosessnavn': prosessnavn, 'prosesseier': prosesseier, 'avdeling': avdeling,
        'prosessbeskrivelse': prosessbeskrivelse, 'trigger': trigger, 'frekvens': frekvens,
        'antall_prosesser': antall_prosesser, 'behandlingstid': behandlingstid,
        'personer_involvert': personer_involvert, 'feilrate': feilrate, 'kostnad_per_time': kostnad_per_time,
        'arsvolum': arsvolum, 'arslig_tidsbesparing': arslig_tidsbesparing, 'kostnadsbesparelse': kostnadsbesparelse,
        'it_systemer': it_systemer, 'datakilder': datakilder, 'filformater': filformater, 'api_tilgang': api_tilgang,
        'tidsbesparelse': tidsbesparelse, 'volum': volum, 'kvalitetsforbedring': kvalitetsforbedring,
        'teknisk_kompleksitet': teknisk_kompleksitet, 'datastruktur': datastruktur, 'regelstabilitet': regelstabilitet,
        'org_pavirkning': org_pavirkning, 'brukerpavirkning': brukerpavirkning, 'regelverksoverholdelse': regelverksoverholdelse,
        'gevinst_score': scoring['gevinst_score'], 'gjennomforbarhet_score': scoring['gjennomforbarhet_score'],
        'strategisk_score': scoring['strategisk_score'], 'total_score': scoring['total_score'],
        'justert_score': scoring['justert_score'], 'volum_bonus': scoring['volum_bonus'],
        'prioritet': prioritet, 'risiko_faktorer': risiko_faktorer, 'bonus_faktorer': bonus_faktorer,
        'registrert_dato': datetime.now().isoformat()
    }
    
    if rediger_mode:
        # Oppdater eksisterende rad i Supabase
        current_row = st.session_state.df.iloc[st.session_state.rediger_index]
        prosess_id = current_row['id']
        
        if oppdater_data_in_supabase(prosess_id, data_dict):
            st.success(f"Prosess '{prosessnavn}' er oppdatert!")
            st.session_state.rediger_index = None
            # Refresh data
            st.session_state.df = last_data()
        else:
            st.error("Kunne ikke oppdatere prosessen i databasen")
    else:
        # Legg til ny rad i Supabase
        if lagre_data_to_supabase(data_dict):
            st.success(f"Prosess '{prosessnavn}' er lagret!")
            # Refresh data
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
        total_besparelse = pd.to_numeric(filtered_df['kostnadsbesparelse'], errors='coerce').sum()
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
            st.metric("Årlig besparelse", f"{total_besparelse:,.0f} kr")
        with col3:
            st.metric("Tidsbesparing", f"{total_tid:,.0f} timer/år")
        with col4:
            st.metric("Høy prioritet", hoy_prioritet)
        
        # Additional breakdown if showing all data
        if avd_filter == "Alle" and prioritet_filter == "Alle" and min_score == 0:
            st.markdown("---")
            st.subheader("📈 Detaljert oversikt")
            
            # Breakdown by department
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Per avdeling:**")
                avd_breakdown = df.groupby('avdeling').agg({
                    'prosessnavn': 'count',
                    'kostnadsbesparelse': lambda x: pd.to_numeric(x, errors='coerce').sum(),
                    'arslig_tidsbesparing': lambda x: pd.to_numeric(x, errors='coerce').sum(),
                    'prioritet': lambda x: x.str.contains("HØY", na=False).sum()
                }).round(0)
                avd_breakdown.columns = ['Antall', 'Årlig besparelse (kr)', 'Tidsbesparing (timer)', 'Høy prioritet']
                avd_breakdown['Årlig besparelse (kr)'] = avd_breakdown['Årlig besparelse (kr)'].apply(lambda x: f"{x:,.0f}")
                avd_breakdown['Tidsbesparing (timer)'] = avd_breakdown['Tidsbesparing (timer)'].apply(lambda x: f"{x:,.0f}")
                st.dataframe(avd_breakdown)
            
            with col2:
                st.markdown("**Per prioritet:**")
                prioritet_breakdown = df.groupby('prioritet').agg({
                    'prosessnavn': 'count',
                    'kostnadsbesparelse': lambda x: pd.to_numeric(x, errors='coerce').sum(),
                    'arslig_tidsbesparing': lambda x: pd.to_numeric(x, errors='coerce').sum()
                }).round(0)
                prioritet_breakdown.columns = ['Antall', 'Årlig besparelse (kr)', 'Tidsbesparing (timer)']
                prioritet_breakdown['Årlig besparelse (kr)'] = prioritet_breakdown['Årlig besparelse (kr)'].apply(lambda x: f"{x:,.0f}")
                prioritet_breakdown['Tidsbesparing (timer)'] = prioritet_breakdown['Tidsbesparing (timer)'].apply(lambda x: f"{x:,.0f}")
                st.dataframe(prioritet_breakdown)
        
        # Vis tabell
        display_cols = ['prosessnavn', 'avdeling', 'prioritet', 'justert_score', 'kostnadsbesparelse', 'arslig_tidsbesparing']
        display_df = filtered_df[display_cols].copy()
        display_df['kostnadsbesparelse'] = pd.to_numeric(display_df['kostnadsbesparelse'], errors='coerce').apply(lambda x: f"{x:,.0f} kr")
        display_df['arslig_tidsbesparing'] = pd.to_numeric(display_df['arslig_tidsbesparing'], errors='coerce').apply(lambda x: f"{x:,.0f} timer")
        display_df['justert_score'] = pd.to_numeric(display_df['justert_score'], errors='coerce').round(1)
        
        st.dataframe(display_df, use_container_width=True)
        
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
    
    # Visualiseringer
    col1, col2 = st.columns(2)
    
    with col1:
        # Prioritetsfordeling
        st.subheader("Prioritetsfordeling")
        prioritet_counts = df['prioritet'].value_counts()
        colors = ['#FF6B6B', '#FFE66D', '#4ECDC4', '#E8E8E8']
        fig_pie = px.pie(
            values=prioritet_counts.values, 
            names=prioritet_counts.index,
            title="Fordeling av prioritetskategorier",
            color_discrete_sequence=colors
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Avdelingsfordeling
        st.subheader("Avdelingsfordeling")
        avd_counts = df['avdeling'].value_counts()
        fig_bar = px.bar(
            x=avd_counts.index, 
            y=avd_counts.values,
            title="Antall prosesser per avdeling",
            labels={'x': 'Avdeling', 'y': 'Antall prosesser'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Score analyse
    st.subheader("Score-analyse")
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter plot: Gevinst vs Gjennomførbarhet
        fig_scatter = px.scatter(
            df, 
            x='gjennomforbarhet_score', 
            y='gevinst_score',
            size='justert_score',
            color='prioritet',
            hover_data=['prosessnavn', 'avdeling'],
            title="Gevinst vs Gjennomførbarhet",
            labels={'gjennomforbarhet_score': 'Gjennomførbarhet', 'gevinst_score': 'Gevinst'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # Top 10 prosesser etter score
        st.subheader("Top 10 prosesser")
        top_prosesser = df.nlargest(10, 'justert_score')[['prosessnavn', 'justert_score', 'prioritet']]
        fig_top = px.bar(
            top_prosesser,
            x='justert_score',
            y='prosessnavn',
            orientation='h',
            color='prioritet',
            title="Topp 10 prosesser etter score"
        )
        st.plotly_chart(fig_top, use_container_width=True)
    
    # Økonomisk analyse
    st.subheader("Økonomisk analyse")
    col1, col2 = st.columns(2)
    
    with col1:
        # Kostnadsbesparelse per avdeling
        kostnader_avd = df.groupby('avdeling')['kostnadsbesparelse'].sum().sort_values(ascending=False)
        fig_kostnad = px.bar(
            x=kostnader_avd.index,
            y=kostnader_avd.values,
            title="Potensiell årlig kostnadsbesparelse per avdeling",
            labels={'x': 'Avdeling', 'y': 'Kostnadsbesparelse (kr)'}
        )
        st.plotly_chart(fig_kostnad, use_container_width=True)
    
    with col2:
        # Tidsbesparing vs Kostnadsbesparelse
        fig_tid_kostnad = px.scatter(
            df,
            x='arslig_tidsbesparing',
            y='kostnadsbesparelse',
            size='justert_score',
            color='prioritet',
            hover_data=['prosessnavn'],
            title="Tidsbesparing vs Kostnadsbesparelse",
            labels={'arslig_tidsbesparing': 'Årlig tidsbesparing (timer)', 'kostnadsbesparelse': 'Kostnadsbesparelse (kr)'}
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
