import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ==========================================
# 1. MENAXHIMI I DATABAZËS DHE SIGURISË
# ==========================================
class DatabaseManager:
    def __init__(self, db_name='clinic_data.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        # Tabela e përdoruesve me fjalëkalime të enkriptuara
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
        # Tabela e takimeve e lidhur me përdoruesin
        c.execute('''CREATE TABLE IF NOT EXISTS appointments 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT, date TEXT, time TEXT)''')
        self.conn.commit()

    def make_hash(self, password):
        return hashlib.sha256(str.encode(password)).hexdigest()

    def add_user(self, username, password, role="patient"):
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                      (username, self.make_hash(password), role))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Përdoruesi ekziston

    def login_user(self, username, password):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                  (username, self.make_hash(password)))
        return c.fetchone()

    def book_appointment(self, username, date, time):
        c = self.conn.cursor()
        c.execute("INSERT INTO appointments (username, date, time) VALUES (?, ?, ?)", 
                  (username, date, time))
        self.conn.commit()

    def get_appointments(self, username):
        c = self.conn.cursor()
        c.execute("SELECT date, time FROM appointments WHERE username=?", (username,))
        return c.fetchall()

# ==========================================
# 2. LOGJIKA MJEKËSORE (AI MOCK)
# ==========================================
class MedicalLogic:
    def __init__(self):
        self.symptom_rules = {
            'ethe': ['Grip', 'Ftohje e zakonshme', 'Infeksion'],
            'kolle': ['Grip', 'Bronkit', 'Alergji'],
            'dhimbje koke': ['Migrenë', 'Tension', 'Mungesë gjumi'],
        }
        
    def check_symptoms(self, symptoms):
        possible_conditions = set()
        for symptom in symptoms:
            if symptom in self.symptom_rules:
                possible_conditions.update(self.symptom_rules[symptom])
        return possible_conditions

# ==========================================
# 3. NDËRFAQJA E PËRDORUESIT (UI)
# ==========================================
# Konfigurimi i faqes
st.set_page_config(page_title="MediCare AI Clinic", page_icon="🏥", layout="centered")

# Inicializimi i klasave
db = DatabaseManager()
medical_ai = MedicalLogic()

# Menaxhimi i Sesionit (Qëndrimi i loguar)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# --- SHIRITI ANËSOR: LOGIN / REGISTER ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=100) # Ikonë gjenerike mjekësore
    st.title("MediCare Portal")
    
    if not st.session_state['logged_in']:
        menu = st.selectbox("Menu", ["Hyr (Login)", "Krijo Llogari (Register)"])
        
        if menu == "Hyr (Login)":
            username = st.text_input("Emri i përdoruesit")
            password = st.text_input("Fjalëkalimi", type="password")
            if st.button("Hyr"):
                if db.login_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.success(f"Mirësevini, {username}!")
                    st.rerun()
                else:
                    st.error("Kredenciale të gabuara!")
                    
        elif menu == "Krijo Llogari (Register)":
            new_user = st.text_input("Emri i përdoruesit")
            new_password = st.text_input("Fjalëkalimi", type="password")
            if st.button("Regjistrohu"):
                if db.add_user(new_user, new_password):
                    st.success("Llogaria u krijua me sukses! Tani mund të hyni.")
                else:
                    st.warning("Ky emër përdoruesi ekziston tashmë.")
    else:
        st.write(f"I loguar si: **{st.session_state['username']}**")
        if st.button("Dil (Logout)"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ''
            st.rerun()

# --- FAQJA KRYESORE (VETËM PËR TË LOGUARIT) ---
if st.session_state['logged_in']:
    st.title("🏥 Portali i Pacientit")
    st.markdown("---")
    
    # Krijimi i seksioneve me Tabs (shumë më profesionale)
    tab1, tab2, tab3 = st.tabs(["🩺 Kontrolli i Simptomave", "📅 Rezervo Takim", "📋 Takimet e mia"])
    
    with tab1:
        st.header("Kontrolli i Simptomave")
        st.info("⚠️ **Kujdes:** Ky mjet ofron vetëm sugjerime fillestare dhe nuk zëvendëson diagnostikimin nga një mjek profesionist.")
        symptoms = st.text_input("Shkruaj simptomat (të ndara me presje, p.sh: ethe, kolle):")
        if st.button("Analizo"):
            if symptoms:
                symptoms_list = [sym.strip().lower() for sym in symptoms.split(',')]
                conditions = medical_ai.check_symptoms(symptoms_list)
                if conditions:
                    st.warning("Sëmundje të mundshme (Këshillohuni me mjekun):")
                    for cond in conditions:
                        st.write(f"- {cond}")
                else:
                    st.success("Nuk u gjetën të dhëna për këto simptoma në sistemin tonë.")
            else:
                st.error("Ju lutem shkruani një simptomë.")

    with tab2:
        st.header("Rezervo një Takim")
        date = st.date_input("Zgjidhni datën:", min_value=datetime.today())
        time = st.time_input("Zgjidhni orën:")
        if st.button("Konfirmo Takimin"):
            db.book_appointment(st.session_state['username'], str(date), str(time))
            st.success(f"Takimi u rezervua me sukses për datën {date} në orën {time}.")

    with tab3:
        st.header("Takimet e tua të ardhshme")
        appointments = db.get_appointments(st.session_state['username'])
        if appointments:
            for idx, appt in enumerate(appointments):
                st.write(f"**Takimi {idx+1}:** Data: `{appt[0]}` | Ora: `{appt[1]}`")
        else:
            st.write("Nuk keni asnjë takim të rezervuar.")
else:
    st.warning("👈 Ju lutem, identifikohuni ose krijoni një llogari në menunë anësore për të përdorur sistemin.")