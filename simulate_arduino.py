import requests
import json
import time
from datetime import datetime

# ==========================================
# CONFIGURATION DU SIMULATEUR
# ==========================================
SERVER_URL = "http://192.168.43.146:8000/api/iot"
PATIENT_ID = 7  # Remplacez par un ID patient valide de votre base
CHECK_INTERVAL_SECONDS = 10  # Intervalle de vérification (boucle loop)

# En-têtes HTTP
HEADERS = {
    'Content-Type': 'application/json'
}

# Mémoire locale du simulateur (reproduit la RAM de l'Arduino)
local_schedules = []
triggered_today = set()  # Retient les prises déjà déclenchées aujourd'hui


def fetch_schedule():
    """
    Simule la fonction GET /api/iot/schedule/<patient_id>/
    """
    global local_schedules
    url = f"{SERVER_URL}/schedule/{PATIENT_ID}/"
    print(f"\n[GET] Interrogation du serveur : {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            local_schedules = data.get('schedules', [])
            print(f"--> Succès ! Planning reçu pour le Patient #{data.get('patient_id')}:")
            for item in local_schedules:
                meds = ", ".join([m['name'] for m in item.get('medications', [])])
                print(f"    📦 Compartiment {item['compartment']} à {item['time']} -> ({meds})")
        else:
            print(f"--> Erreur Serveur ({response.status_code}) : {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"--> Impossible de contacter le serveur Django : {e}")


def send_take_dose_log(compartment_number, status="TAKEN"):
    """
    Simule la fonction POST /api/iot/log/ (Appui sur le bouton de validation)
    """
    url = f"{SERVER_URL}/log/"
    payload = {
        "patient_id": PATIENT_ID,
        "compartment": compartment_number,
        "status": status
    }
    print(f"\n[POST] Envoi de la confirmation de prise : {url}")
    print(f"       Données envoyées : {json.dumps(payload)}")
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=HEADERS, timeout=5)
        if response.status_code in [200, 201]:
            res_data = response.json()
            print(f"--> Réponse Django : {res_data.get('message')} (Log ID: {res_data.get('log_id')})")
        else:
            print(f"--> Erreur POST ({response.status_code}) : {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"--> Échec de l'envoi du log : {e}")


def run_simulator():
    """
    Boucle principale simulant le void loop() de l'Arduino
    """
    print("=" * 60)
    print("      SIMULATEUR PILULIER IOT ARDUINO / ESP32      ")
    print("=" * 60)
    
    # 1. Démarrage : téléchargement initial de la prescription
    fetch_schedule()
    
    print("\n[LOOP] Simulation en cours... (Ctrl+C pour arrêter)")
    
    try:
        while True:
            now_str = datetime.now().strftime("%H:%M")
            current_time_full = datetime.now().strftime("%H:%M:%S")
            print(f"[{current_time_full}] Vérification des horaires...", end="\r")

            # Parcours du planning en mémoire
            for item in local_schedules:
                comp = item['compartment']
                target_time = item['time']
                trigger_key = f"{comp}_{target_time}"

                # Déclenchement à l'heure exacte
                if now_str == target_time and trigger_key not in triggered_today:
                    print(f"\n\n🔔 [ALERTE IOT] Il est {now_str} !")
                    print(f"💡 LED Compartiment {comp} ALLUMÉE ! Buzzer en marche !")
                    
                    # Simulation de l'action du patient
                    input(f"👉 Appuyez sur [ENTRÉE] pour simuler l'ouverture et la prise du Compartiment {comp}...")
                    
                    # Envoi de la confirmation à Django
                    send_take_dose_log(comp)
                    triggered_today.add(trigger_key)
                    print("💡 LED ÉTEINTE.")

            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\n[STOP] Arpêt du simulateur.")

if __name__ == "__main__":
    run_simulator()