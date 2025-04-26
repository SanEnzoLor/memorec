import streamlit as st
import pandas as pd
import time
import random
import numpy as np
import requests
import json
import base64
import speech_recognition as sr

from st_audiorec import st_audiorec
from pydub import AudioSegment
from io import StringIO
from io import BytesIO




import secrets
import string

# Funzione per generare il token di accesso
def generate_unique_token(length=32):
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    if load_from_github(token).empty:
        return token
    else:
        return generate_unique_token()




# Funzione per trascrivere l'audio
def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="it-IT")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            return f"Errore nel servizio di riconoscimento vocale: {e}"


# Funzione per caricare i dati dalla sessione precedente
def load_from_github(id_value):
    # Parametri di accesso al repository
    repo_name = "SanEnzoLor/memo_data"
    file_name = "dati.csv"
    branch_name = "main"
    token = st.secrets["token"]

    # URL per ottenere il contenuto del file
    url = f"https://api.github.com/repos/{repo_name}/contents/{file_name}?ref={branch_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()["content"]
        decoded_content = base64.b64decode(content).decode("utf-8")
        df = pd.read_csv(StringIO(decoded_content))
        
        filtered_df = df[df["ID"] == id_value]
        
        return filtered_df

    elif response.status_code == 404:
        st.warning("Il file non è stato trovato nel repository.")
        return pd.DataFrame()
    else:
        st.error(f"Errore durante il caricamento del file da GitHub: {response.status_code}")
        return pd.DataFrame()


def save_and_upload_to_github(data):
    # Input per i dati da salvare
    columns = ["ID", "Eta", "Gender", "Nazionalita", "Educazione", "Occupazione", "Caregiver", "Limitazione",  "BDI2", "RRS", "PCL-5-reexperiencing", "PCL-5-avoidance", "PCL-5-altereted_cognition", "PCL-5-hyperarousal", "PCL-5-tot", "Cue-Word", "Text", "Time", "Time_recording"]
    new_df = pd.DataFrame(data, columns=columns)
    file_name = "dati.csv"

    # Input per GitHub
    repo_name = "SanEnzoLor/memo_data"
    branch_name = "main"
    token = st.secrets["token"]
        
    # Verifica se il file esiste nella repository
    url = f"https://api.github.com/repos/{repo_name}/contents/{file_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:  # Il file esiste già
        sha = response.json()["sha"]
        content = response.json()
        # Decodifica e carica i dati esistenti
        existing_data = base64.b64decode(content["content"]).decode("utf-8")
        existing_df = pd.read_csv(StringIO(existing_data))
    else:
        sha = None  # Il file non esiste ancora
        existing_df = pd.DataFrame()  # DataFrame vuoto

    # Combina i dati esistenti con i nuovi dati
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Salva il nuovo DataFrame in CSV
    combined_csv = combined_df.to_csv(index=False)

    # Codifica il contenuto aggiornato in Base64
    content = base64.b64encode(combined_csv.encode("utf-8")).decode("utf-8")
    
    # Creazione del payload per l'API di GitHub
    payload = {
        "message": "Aggiunta file CSV tramite Streamlit",
        "content": content,
        "branch": branch_name,
    }
    if sha:  # Se il file esiste, aggiungi "sha" al payload
        payload["sha"] = sha
    
    # Richiesta POST a GitHub
    response = requests.put(url, headers=headers, data=json.dumps(payload))
            
    if response.status_code == 200:  # 200 = aggiornato
        st.success("File aggiornato con successo su GitHub!")
        if st.session_state.df_ses_p is not None:
            new_df = pd.concat([st.session_state.df_ses_p, new_df], ignore_index=True)
        st.write(new_df)
    elif response.status_code == 201:  # 201 = creato
        st.success("File creato con successo su GitHub!")
        st.write(new_df)
    else:
        st.error(f"Errore durante l'upload; attendere qualche secondo...")
        # Attendi un tempo casuale tra 0 e 5 secondi prima di riprovare
        wait_time = random.uniform(0, 5)
        time.sleep(wait_time)
        save_and_upload_to_github(data)      
        
    #st.download_button(label="**CLICCA QUI** per **scaricare i dati** della sessione.", data = new_df.to_csv(index=False), icon = "💾", type = "primary", file_name="dati_sessione.csv", mime="text/csv")
    

# Funzione per somministrare il BDI2
def BDI2():
    if st.session_state.results_d == 0:
        st.write("L'Inventario per la Depressione di Beck (BDI -II) è un questionario autovalutativo utilizzato per quantificare i sintomi del disturbo depressivo maggiore in adolescenti e adulti.")
        st.write("Il presente questionario consiste di 21 gruppi di affermazioni.  Per ogni gruppo scelga quella che meglio descrive come si è sentito nelle ultime due settimane (incluso oggi). Se più di una affermazione dello stesso gruppo descrive ugualmente bene come si sente, faccia una crocetta sul numero più elevato per quel gruppo. Non si soffermi troppo su ogni affermazione: la prima risposta è spesso la più accurata.")
    
        options = ["0. Non mi sento triste.", "1. Mi sento triste per la maggior parte del tempo.", "2. Mi sento sempre triste.", "3. Mi sento così triste o infelice da non poterlo sopportare."]
        items= options.index(st.selectbox("Tristezza", options))#, on_change = BDI2_on_change()
        
        options = ["0. Non sono scoraggiato riguardo al mio futuro.", "1. Mi sento più scoraggiato riguardo al mio futuro rispetto al solito.", "2. Non mi aspetto nulla di buono per me.", "3. Sento che il mio futuro è senza speranza e che continuerà a peggiorare."]
        items = items + options.index(st.selectbox("Pessimismo", options))
            
        options = ["0. Non mi sento un fallito.", "1. Ho fallito più di quanto avrei dovuto.", "2. Se ripenso alla mia vita riesco a vedere solo una serie di fallimenti.", "3. Ho la sensazione di essere un fallimento totale come persona."]
        items = items + options.index(st.selectbox("Fallimento", options))
        
        options = ["0. Traggo lo stesso piacere di sempre dalle cose che faccio.", "1. Non traggo più piacere dalle cose come un tempo.", "2. Traggo molto poco piacere dalle cose che di solito mi divertivano.", "3. Non riesco a trarre alcun piacere dalle cose che una volta mi piacevano."]
        items = items + options.index(st.selectbox("Perdita di piacere", options))
        
        options = ["0. Non mi sento particolarmente in colpa.", "1. Mi sento in colpa per molte cose che ho fatto o che avrei dovuto fare.", "2. Mi sento molto spesso in colpa.", "3. Mi sento sempre in colpa."]
        items = items + options.index(st.selectbox("Senso di colpa", options))
        
        options = ["0. Non mi sento come se stessi subendo una punizione. ","1. Sento che potrei essere punito. ","2. Mi aspetto di essere punito. ","3. Mi sento come se stessi subendo una punizione."]
        items = items + options.index(st.selectbox("Sentimenti di punizione", options))
        
        options = ["0. Considero me stesso come ho sempre fatto.","1. Credo meno in me stesso.","2. Sono deluso di me stesso. ","3. Mi detesto."]
        items = items + options.index(st.selectbox("Autostima", options))
        
        options = ["0. Non mi critico né mi biasimo più del solito.","1. Mi critico più spesso del solito.", "2. Mi critico per tutte le mie colpe.", "3. Mi biasimo per ogni cosa brutta che mi accade."]
        items = items + options.index(st.selectbox("Autocritica", options))
        
        options = ["0. Non ho alcun pensiero suicida.","1. Ho pensieri suicidi ma non li realizzerei.","2. Sento che starei meglio se morissi. ","3. Se mi si presentasse l’occasione, non esiterei ad uccidermi."]
        items = items + options.index(st.selectbox("Suicidio", options))
        
        options = ["0. Non piango più del solito.","1. Piango più del solito. ","2. Piango per ogni minima cosa. ","3. Ho spesso voglia di piangere ma non ci riesco."]
        items = items + options.index(st.selectbox("Pianto", options))
        
        options = ["0. Non mi sento più agitato o teso del solito.","1. Mi sento più agitato o teso del solito. ","2. Sono così nervoso o agitato al punto che mi è difficile rimanere fermo. ","3. Sono così nervoso o agitato che devo continuare a muovermi o fare qualcosa."]
        items = items + options.index(st.selectbox("Agitazione", options))
        
        options = ["0. Non ho perso interesse verso le altre persone o verso le attività.", "1. Sono meno interessato agli altri o alle cose rispetto a prima. ","2. Ho perso la maggior parte dell’interesse verso le altre persone o cose. ","3. Mi risulta difficile interessarmi a qualsiasi cosa."]
        items = items + options.index(st.selectbox("Perdita di interessi", options))
        
        options = ["0. Prendo decisioni come sempre. ","1. Trovo più difficoltà del solito nel prendere decisioni. ","2. Ho molte più difficoltà nel prendere decisioni rispetto al solito. ","3. Non riesco a prendere nessuna decisione."]
        items = items + options.index(st.selectbox("Indecisione", options))
        
        options = ["0. Non mi sento inutile. ","1. Non mi sento valido e utile come un tempo. ","2. Mi sento più inutile delle altre persone. ","3. Mi sento completamente inutile su qualsiasi cosa."]
        items = items + options.index(st.selectbox("Senso di inutilità", options))
        
        options = ["0. Ho la stessa energia di sempre. ","1. Ho meno energia del solito. ","2. Non ho energia sufficiente per fare la maggior parte delle cose.","3. Ho così poca energia che non riesco a fare nulla."]
        items = items + options.index(st.selectbox("Perdita di energia ", options))
        
        options = ["0. Non ho notato alcun cambiamento nel mio modo di dormire. ", "1a. Dormo un po’ più del solito. ","1b. Dormo un po’ meno del solito. ","2a. Dormo molto più del solito. ","2b. Dormo molto meno del solito. ","3a. Dormo quasi tutto il giorno. ","3b. Mi sveglio 1-2 ore prima e non riesco a riaddormentarmi."]
        items = items + np.round(options.index(st.selectbox("Sonno", options))/2 + 0.01)
        
        options = ["0. Non sono più irritabile del solito. ","1. Sono più irritabile del solito. ","2. Sono molto più irritabile del solito.","3. Sono sempre irritabile."]
        items = items + options.index(st.selectbox("Irritabilità", options))
        
        options = ["0. Non ho notato alcun cambiamento nel mio appetito.", "1a. Il mio appetito è un po’ diminuito rispetto al solito. ","1b. Il mio appetito è un po’ aumentato rispetto al solito. ","2a. Il mi appetito è molto diminuito rispetto al solito. ","2b. Il mio appetito è molto aumentato rispetto al solito. ","3a. Non ho per niente appetito. ","3b. Mangerei in qualsiasi momento"]
        items = items + np.round(options.index(st.selectbox("Appetito", options))/2 + 0.01)
        
        options = ["0. Riesco a concentrarmi come sempre.","1. Non riesco a concentrarmi come al solito.","2. Trovo difficile concentrarmi per molto tempo.","3. Non riesco a concentrarmi su nulla."]
        items = items + options.index(st.selectbox("Concentrazione", options))
        
        options = ["0. Non sono più stanco o affaticato del solito. ","1. Mi stanco e mi affatico più facilmente del solito. ","2. Sono così stanco e affaticato che non riesco a fare molte delle cose che facevo prima. ","3. Sono talmente stanco e affaticato che non riesco più a fare nessuna delle cose che facevo prima."]
        items = items + options.index(st.selectbox("Fatica", options))
        
        options = ["0. Non ho notato alcun cambiamento recente nel mio interesse verso il sesso.", "1. Sono meno interessato al sesso rispetto a prima.","2. Ora sono molto meno interessato al sesso. ","3. Ho completamente perso l’interesse verso il sesso."]
        items = items + options.index(st.selectbox("Sesso", options))

        return items

    else:
        choice_d = st.selectbox("Si vuole **rieseguire** l' **Inventario per la Depressione di Beck (BDI -II)** ?", ["SI", "NO"], index = 1)
        if choice_d == "SI":
            st.session_state.results_d = 0
            BDI2()
        else:
            return st.session_state.results_d

# Funzione per somministrare il RRS
def RRS():
    if st.session_state.results_r == 22:
        st.write("La Scala delle Risposte Ruminative (RRS) è una misura autovalutata progettata per valutare la frequenza con cui gli individui si impegnano in diversi tipi di pensieri e comportamenti ruminativi.")
        st.write("Gli individui pensano e agiscono in molti modi diversi quando si sentono depressi. Per favore, legga ciascuno dei seguenti item e indichi se, quando si sente giù, triste o depresso, lo pensa o lo fa 'mai', 'a volte', 'spesso' o 'sempre'. Indichi cortesemente cosa fa di solito, non cosa pensa di dover fare, selezionando il numero per indicare quanto ogni problema la affligge:")
    
        # Crea quattro colonne per le informazioni
        cl1, cl2, cl3, cl4 = st.columns([0.26, 0.32, 0.29, 0.13])
        # Mostra le scritte nelle colonne
        with cl1:
            st.write("Mai = 1") 
        with cl2:
            st.write("A volte = 2")
        with cl3:
            st.write("Spesso = 3")
        with cl4:
            st.write("Sempre = 4")
                
        items = st.slider("Pensare a quanto ti senti solo", min_value=1, max_value=4, step=1)        
        items = items + st.slider("Pensare “Non sarò in grado di svolgere il mio lavoro se non mi libero di questo”", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare alle tue sensazioni di stanchezza e malessere", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare a quanto sia difficile concentrarti", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare “Cosa ho fatto per meritarmi questo?”", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare a quanto ti senti passivo e demotivato", min_value=1, max_value=4, step=1)
        items = items + st.slider("Analizzare eventi recenti per cercare di capire perché sei depresso", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare al fatto che ti sembra di non sentire più niente", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare “Perché non riesco a mettermi in moto?”", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare “Perché reagisco sempre in questo modo?”", min_value=1, max_value=4, step=1)
        items = items + st.slider("Andare via da solo e pensare al perché ti senti in questo modo", min_value=1, max_value=4, step=1)
        items = items + st.slider("Scrivere cosa stai pensando e analizzarlo", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare a una situazione recente, desiderando che fosse andata meglio", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare “Non riuscirò a concentrarmi se continuo a sentirmi in questo modo”", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare “Perché ho problemi che gli altri non hanno?”", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare “Perché non tratto meglio le cose?”", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare a quanto ti senti triste", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare a tutte le tue mancanze, difetti, colpe, errori", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare al fatto che non te la senti di far nulla", min_value=1, max_value=4, step=1)
        items = items + st.slider("Analizzare la tua personalità per cercare di capire perché sei depresso", min_value=1, max_value=4, step=1)
        items = items + st.slider("Andare da solo in un qualche posto per pensare alle tue emozioni", min_value=1, max_value=4, step=1)
        items = items + st.slider("Pensare a quanto ti senti arrabbiato con te stesso", min_value=1, max_value=4, step=1)
    
        return items

    else:
        choice_r = st.selectbox("Si vuole **rieseguire** la **Scala delle Risposte Ruminative (RRS)** ?", ["SI", "NO"], index = 1)
        if choice_r == "SI":
            st.session_state.results_r = 22
            RRS()
        else:
            return st.session_state.results_r


# Funzione per il PTSD checklist 5
def PCL5():
    if st.session_state.results_p[4] == 0:
        st.write("Ha mai vissuto uno dei seguenti eventi: rischio di morte, minaccia concreta di lesioni gravi o atti di violenza? In una o più delle seguenti modalità?")
        st.write("1. Sperimentando in prima persona l'evento o gli eventi.")
        st.write("2. Assistendo a un evento o gli eventi verificati ad altri.")
        st.write("3. Apprendendo che l'evento è accaduto a un parente o a un amico stretto.")
        st.write("4. Sperimentando un'esposizione ripetuta a dettagli estremi di eventi non noti verificati ad altri (e.g., i primi soccorritori che raccolgono parti di corpi; gli agenti di polizia ripetutamente esposti a dettagli di abusi su minori).")
        trauma_event = st.selectbox("risposta", ["SI","NO"], index=1, label_visibility = "collapsed") # NO predefinito
    
        if trauma_event == "SI":
            st.write("Qui sotto viene riportata una lista di problemi che talvolta le persone presentano in risposta a esperienze molto stressanti. Leggere ogni problema attentamente e selezionare il numero per indicare quanto ogni problema l'ha afflitta nell'ultima settimana:")
            
            # Crea cinque colonne per le informazioni
            cl1, cl2, cl3, cl4, cl5 = st.columns([0.2, 0.16, 0.32, 0.16, 0.16])
            # Mostra le scritte nelle colonne
            with cl1:
                st.write("Per niente = 0") 
            with cl2:
                st.write("Poco = 1")
            with cl3:
                st.write("Moderatamente = 2")
            with cl4:
                st.write("Molto = 3")
            with cl5:
                st.write("Moltissimo = 4")
            
            items_reexperiencing = st.slider("Ricordi ripetuti, disturbanti e indesiderati dell'esperienza stressante che ha subito?", min_value=0, max_value=4, step=1)
            items_reexperiencing = items_reexperiencing + st.slider("Sogni ricorrenti e disturbanti dell'esperienza stressante?", min_value=0, max_value=4, step=1)
            items_reexperiencing = items_reexperiencing + st.slider("Avere la sensazione o comportarsi improvvisamente come se l'esperienza stressante  si stesse verificando nuovamente (come se si rivivesse la stessa esperienza)?", min_value=0, max_value=4, step=1)
            items_reexperiencing = items_reexperiencing + st.slider("Sentirsi molto turbato/a quando qualcosa le ricorda l'esperienza stressante?", min_value=0, max_value=4, step=1)
            items_reexperiencing = items_reexperiencing + st.slider("Avere forti reazioni fisiche quando qualcosa Le ricorda l'esperienza stressante (per esempio battito del cuore accelerato, respiro affannoso, sudorazione)?", min_value=0, max_value=4, step=1)
    
            items_avoidance = st.slider("Evitare ricordi, pensieri o sensazioni legati all'esperienza stressante?", min_value=0, max_value=4, step=1)
            items_avoidance = items_avoidance + st.slider("Evitare qualunque cosa Le ricordi l'esperienza stressante (per esempio, persone, luoghi, conversazioni, attività, oggetti o situazioni)?", min_value=0, max_value=4, step=1)
    
            items_altereted_cognition = st.slider("Problemi a ricordare elementi importanti dell'esperienza stressante?", min_value=0, max_value=4, step=1)
            items_altereted_cognition = items_altereted_cognition + st.slider("Avere opinioni fortemente negative di sé, di altre persone o del mondo (per esempio, avere pensieri del tipo: Io sono una cattiva persona, c'è realmente qualcosa che non va in me, non ci si può fidare di nessuno, il mondo intero è pericoloso)?", min_value=0, max_value=4, step=1)
            items_altereted_cognition = items_altereted_cognition + st.slider("Incolpare se stesso/a o altre persone dell'esperienza stressante o di ciò che è accaduto in seguito?", min_value=0, max_value=4, step=1)
            items_altereted_cognition = items_altereted_cognition + st.slider("Avere sentimenti fortemente negativi come paura, terrore, rabbia, senso di colpa o vergogna?", min_value=0, max_value=4, step=1)
            items_altereted_cognition = items_altereted_cognition + st.slider("Perdita di interesse alle attività che solitamente Le piacevano?", min_value=0, max_value=4, step=1)
            items_altereted_cognition = items_altereted_cognition + st.slider("Sentirsi distante o isolato/a dal prossimo?", min_value=0, max_value=4, step=1)
            items_altereted_cognition = items_altereted_cognition + st.slider("Avere difficoltà a provare sentimenti positivi (per esempio, sentirsi incapace di provare felicità o sentimenti di affetto nei confronti di persone a Lei care)?", min_value=0, max_value=4, step=1)
            
            items_hyperarousal = st.slider("Avere un comportamento irritabile, accessi di rabbia, o reazioni aggressive?", min_value=0, max_value=4, step=1)
            items_hyperarousal = items_hyperarousal + st.slider("Correre troppi rischi o fare cose che potrebbero causarLe danno?", min_value=0, max_value=4, step=1)
            items_hyperarousal = items_hyperarousal + st.slider("Essere ipervigile, guardingo/a o sempre all'erta?", min_value=0, max_value=4, step=1)
            items_hyperarousal = items_hyperarousal + st.slider("Sentirsi in tensione o spaventarsi facilmente?", min_value=0, max_value=4, step=1)
            items_hyperarousal = items_hyperarousal + st.slider("Avere difficoltà di concentrazione?", min_value=0, max_value=4, step=1)
            items_hyperarousal = items_hyperarousal + st.slider("Avere difficoltà ad addormentarsi o a dormire?", min_value=0, max_value=4, step=1)
    
            tot = items_reexperiencing + items_avoidance + items_altereted_cognition + items_hyperarousal
        
        else:
            items_reexperiencing = 0
            items_avoidance = 0
            items_altereted_cognition = 0
            items_hyperarousal = 0
            tot = 0
    
        return items_reexperiencing, items_avoidance, items_altereted_cognition, items_hyperarousal, tot

    else:
        choice_p = st.selectbox("Si vuole **rieseguire** la **Checklist per il Disturbo da Stress Posttraumatico - 5 (PCL-5)** ?", ["SI", "NO"], index = 1)
        if choice_p == "SI":
            st.session_state.results_p = [0, 0, 0, 0, 0]
            PCL5()
        else:
            return st.session_state.results_p


# Interfaccia Streamlit
def main():   
    # Crea due colonne per le immagini
    col1, col2 = st.columns([0.81, 1])
    # Mostra le immagini nelle colonne
    with col1:
        st.image("image/logo_unige.png", use_container_width=True)
    with col2:
        st.image("image/logo_nextage.png", use_container_width=True)

    st.title("**Indagine volta alla costruzione di una banca dati di memorie in italiano**")
    st.write("Questo studio fa parte del progetto di dottorato intitolato:")
    st.write("**Modeling dialogue between human and digital agents for the personalized stimulation of mnemonic abilities and the support for the evaluation of the progress and assistance of neurocognitive problems**")
    st.write("Lo scopo di questo studio è quello di raccogliere memorie autobiografiche eventualmente correlabili a indici noti in letteratura come stimatori dello stato di salute individuale.")
    st.markdown("I dati raccolti in questo studio, in formato testuale e anonimo (se si registra un file audio, esso sarà cancellato una volta completata la trascrizione automatica), saranno caricati su una banca dati privata di GitHub https://github.com/SanEnzoLor/memo_data.")
    st.markdown("I dati raccolti da Streamlit Cloud sono anch'essi anonimi e hanno lo scopo di analizzare e gestire l'utilizzo dell'app. In nessun modo sarà possibile risalire all'identità di chi ha completato il test. Per ulteriori informazioni, consulta https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-analytics e https://streamlit.io/privacy-policy.")
    st.markdown("Essendo i dati anonimizzati, la raccolta è conforme al Regolamento Generale sulla Protezione dei Dati o GDPR.")
    
    st.header("**Indici Demografici**")

    # Gestione dello stato per i dati della sessione
    if "change" not in st.session_state:
        st.session_state.change = False
    def gend_sel():
        st.session_state.change = True

    
    # Lista di parole spunto
    cue_words_f = ['ECCITATA', 'ANNOIATA', 'FELICE', 'FALLITA', 'FORTUNATA', 'DISPERATA', 'RILASSATA', 'SOLITARIA', 'SERENA', 'TRISTE']
    cue_words = ['ECCITATO', 'ANNOIATO', 'FELICE', 'FALLITO', 'FORTUNATO', 'DISPERATO', 'RILASSATO', 'SOLITARIO', 'SERENO', 'TRISTE']
    # Gestione dello stato per i dati della sessione
    if "remaining_words" not in st.session_state:
        st.session_state.remaining_words = cue_words.copy()  # Parole rimanenti

    
    if "eta" not in st.session_state:
        st.session_state.eta = 18
    if "gender" not in st.session_state:
        st.session_state.gender = "Nessuno"
    if "nazione" not in st.session_state:
        st.session_state.nazione = " "
    if "educazione" not in st.session_state:
        st.session_state.educazione = "Scuola primaria"
    if "occupazione" not in st.session_state:
        st.session_state.occupazione = "SI"
    if "caregiver" not in st.session_state:
        st.session_state.caregiver = "NO"
    if "autonomia" not in st.session_state:
        st.session_state.autonomia = "NO."
    if "desc" not in st.session_state:
        st.session_state.desc = ""
    if "results_d" not in st.session_state:
        st.session_state.results_d = 0
    if "results_r" not in st.session_state:
        st.session_state.results_r = 22
    if "results_p" not in st.session_state:
        st.session_state.results_p = [0, 0, 0, 0, 0]

    
    if "df_ses_p" not in st.session_state:
        st.session_state.df_ses_p = None
    
    
    # blocca l'aggiornamento dell'applicativo dopo aver letto il file caricato
    if "file_update" not in st.session_state:
        st.session_state.file_update = True




    # genera il nuovo token di accesso
    if "new_token" not in st.session_state:
        st.session_state.new_token = generate_unique_token()



    
    # Creazione di input per acquisire dati dall'utente
    user_id = st.text_input("**Se NON è la PRIMA VOLTA che partecipi**: Inserisci il **codice di accesso** che ti è stato fornito al termine della sessione precedente:")

    if user_id != "" and st.session_state.file_update == True:
        file = load_from_github(user_id)
        if not file.empty:
            st.write(file)
        else:
            st.info("Nessun dato trovato per l'ID inserito.")
    
    #file = st.file_uploader("Carica il **file scaricato** (avente il formato: **dati_sessione.csv**) se si è interrotta la **sessione precedente** senza completare l'attività:", type=["csv"])
    
    #if file and st.session_state.file_update == True:
        #columns = ["Eta", "Gender", "Nazionalita", "Educazione", "Occupazione", "Caregiver", "Limitazione",  "BDI2", "RRS", "PCL-5-reexperiencing", "PCL-5-avoidance", "PCL-5-altereted_cognition", "PCL-5-hyperarousal", "PCL-5-tot", "Cue-Word"]
        st.session_state.df_ses_p = file #pd.read_csv(file)
        #if not all(col in st.session_state.df_ses_p.columns for col in columns):
        #    st.error("Il file caricato non è corretto.")
        #else:
        st.session_state.new_token = st.session_state.df_ses_p["ID"].iloc[-1]
        st.session_state.eta = st.session_state.df_ses_p["Eta"].iloc[-1]
        st.session_state.gender = st.session_state.df_ses_p["Gender"].iloc[-1]
        st.session_state.nazione = st.session_state.df_ses_p["Nazionalita"].iloc[-1]
        st.session_state.educazione = st.session_state.df_ses_p["Educazione"].iloc[-1]
        st.session_state.occupazione = st.session_state.df_ses_p["Occupazione"].iloc[-1]
        st.session_state.caregiver = st.session_state.df_ses_p["Caregiver"].iloc[-1]
        st.session_state.autonomia = st.session_state.df_ses_p["Limitazione"].iloc[-1].split('.', 1)[0] + "."
        if st.session_state.autonomia != "NO.":
            st.session_state.desc = st.session_state.df_ses_p["Limitazione"].iloc[-1].split('. ', 1)[1]
        st.session_state.results_d = st.session_state.df_ses_p["BDI2"].iloc[-1]
        st.session_state.results_r = st.session_state.df_ses_p["RRS"].iloc[-1]
        st.session_state.results_p = [st.session_state.df_ses_p["PCL-5-reexperiencing"].iloc[-1], st.session_state.df_ses_p["PCL-5-avoidance"].iloc[-1], st.session_state.df_ses_p["PCL-5-altereted_cognition"].iloc[-1], st.session_state.df_ses_p["PCL-5-hyperarousal"].iloc[-1], st.session_state.df_ses_p["PCL-5-tot"].iloc[-1]]
        cue_words_p = [c_w[:-1] for c_w in st.session_state.df_ses_p["Cue-Word"]]
        if st.session_state.gender == "Femminile":
            cue_words_ref = cue_words_f
        else:
            cue_words_ref = cue_words
        cue_words_p_r = [p for p in cue_words_ref if p[:-1] not in cue_words_p]
        st.session_state.remaining_words = cue_words_p_r.copy()
        # blocca l'aggiornamento dell'applicativo
        st.session_state.file_update = False
    
    
    dispositivo = st.selectbox("**NECESSARIA:** In questo momento quale strumento stai utilizzando per completare l'attività:", ["Computer","Smartphone"], index = 0)
    st.session_state.eta = st.number_input("Inserisci l'età:", min_value=18, max_value=80, step=1, value = st.session_state.eta)
    gender_ind = ["Maschile", "Femminile", "Non-binario", "Nessuno"].index(st.session_state.gender)
    st.session_state.gender = st.selectbox("Seleziona il genere in cui ti identifichi:", ["Maschile", "Femminile", "Non-binario", "Nessuno"], index = gender_ind, on_change = gend_sel)
    st.session_state.nazione = st.text_input("Scrivi la tua nazionalità:", value = st.session_state.nazione)
    if dispositivo == "Smartphone":
        st.warning("Per salvare correttamente le risposte date per iscritto nel campo testuale premere sulla tastiera virtuale **INVIO**.")
    educazione_ind = ["Scuola primaria", "Scuola secondaria di primo grado", "Scuola secondaria di secondo grado", "Istituto tecnico superiore", "Università triennale", "Università magistrale", "Dottorato"].index(st.session_state.educazione)
    st.session_state.educazione = st.selectbox("Seleziona il grado di istruzione più elevato conseguito:", ["Scuola primaria", "Scuola secondaria di primo grado", "Scuola secondaria di secondo grado", "Istituto tecnico superiore", "Università triennale", "Università magistrale", "Dottorato"], index = educazione_ind)
    occupazione_ind = ["SI","NO"].index(st.session_state.occupazione)
    st.session_state.occupazione = st.selectbox("In questo momento hai un impiego:", ["SI","NO"], index = occupazione_ind)

    caregiver_ind = ["SI","NO"].index(st.session_state.caregiver)
    st.session_state.caregiver = st.selectbox("In questo momento stai fornendo assistenza a un familiare non autosufficiente:", ["SI","NO"], index = caregiver_ind)
    
    autonomia_ind = ["NO.", "SI, motoria.", "SI, sensoriale.", "SI, cognitiva."].index(st.session_state.autonomia)
    st.session_state.autonomia = st.selectbox("Indica se durante le attività quotidiane hai una delle seguenti limitazioni all'autonomia:", ["NO.", "SI, motoria.", "SI, sensoriale.", "SI, cognitiva."], index=autonomia_ind)
    if st.session_state.autonomia != "NO.":
        st.session_state.desc = st.text_input(f"Se si vuole aggiungere una descrizione della propria limitazione {st.session_state.autonomia.split('.', 1)[0].split(', ', 1)[1]}:", value = st.session_state.desc)
    else:
        st.session_state.desc = ""
    

    st.header("**Beck Depression Inventory - II**")
    results_d = BDI2()
    st.write(f"BDI2: {results_d}")

    st.header("**Ruminative Response Scale**")
    results_r = RRS()
    st.write(f"RRS: {results_r}")
    
    st.header("**Posttraumatic Stress Disorder Checklist - 5**")
    results_p = PCL5()
    if results_p is not None:
        st.write(f"PCL5: Re-experiencing = {results_p[0]}, Avoidance = {results_p[1]}, Negative alterations in cognition and mood = {results_p[2]}, Hyper-arousal = {results_p[3]}, Totale = {results_p[4]}")


    st.header("**Cue-Word Autobiographic Memory Retrievial**")
    st.write("L'attività consiste nel **raccontare** un **evento personale** richiamato dalla **parola** che verrà mostrata una volta selezionato **Inizia**. Si descrivano quanti più **dettagli** possibili associati alla memoria autobiografica recuperarta. L'evento descritto **NON** deve essere accaduto durante la **scorsa settimana**. **È OBBLIGATORIO EVITARE** di menzionare **indirizzi specifici** e/o **nome e cognome di persone**, **È OBBLIGATORIO UTILIZZARE** indirizzi generici (e.g. città), nomi comuni di persona (e.g. amico/compagno) o nomi di fantasia (e.g. soprannomi).")
    st.write("Terminata la narrazione sarà possibile salvare la memoria appena descritta (selezionando **Salva memoria**), l'esercizio **dovrà** essere rieseguito per 10 volte con parole differenti (selezionando **Prosegui** e poi **Salva memoria**). Se si desidera ci si può fermare prima (selezionando **Salva Dati e Termina**).")
    st.write("Vi sarà la possibilità:")
    st.write("- Sia di **registrare un audio**, che verrà poi **trascritto automaticamente** nel campo di testuale per eventuali modifiche,")
    st.write("- Sia di **scrivere direttamente** nel campo testuale.") 

    # Gestione dello stato per i dati della sessione
    if "session_data" not in st.session_state:
        st.session_state.session_data = []  # Dati temporanei della sessione
    if st.session_state.change == True and st.session_state.gender == "Femminile":
        corrispondenti = []
        for parola1 in cue_words_f:
            # Rimuovi l'ultima lettera di parola1
            base_parola1 = parola1[:-1]
            # Controlla se esiste una parola che combacia con base_parola1
            match_trovato = any(base_parola1 == parola2[:-1] for parola2 in st.session_state.remaining_words)
            if match_trovato:
                corrispondenti.append(parola1)
        st.session_state.remaining_words = corrispondenti.copy()  # Parole rimanenti
        st.session_state.change = False
    if st.session_state.change == True and st.session_state.gender != "Femminile":
        corrispondenti = []
        for parola1 in cue_words:
            # Rimuovi l'ultima lettera di parola1
            base_parola1 = parola1[:-1]
            # Controlla se esiste una parola in list2 che combacia con base_parola1
            match_trovato = any(base_parola1 == parola2[:-1] for parola2 in st.session_state.remaining_words)
            if match_trovato:
                corrispondenti.append(parola1)
        st.session_state.remaining_words = corrispondenti.copy()  # Parole rimanenti
        st.session_state.change = False
    if "selected_word" not in st.session_state:
        st.session_state.selected_word = ""
    if "start_time" not in st.session_state:
        st.session_state.start_time = 0
    if "start" not in st.session_state:
        st.session_state.start = False
    if "show" not in st.session_state:
        st.session_state.show = False
    if "wav_audio_data" not in st.session_state:
        st.session_state.wav_audio_data = None
    if "transcription" not in st.session_state:
        st.session_state.transcription = ""
    if "time_rec" not in st.session_state:
        st.session_state.time_rec = 0
    if "testo" not in st.session_state:
        st.session_state.testo = ""
    if "ind" not in st.session_state:
        st.session_state.ind = "Inizia"

    ten_w = False
    
    def on_button_i_click():
        st.session_state.start = True
        st.session_state.show = True
    
    # Bottone per avviare la registrazione
    if st.button(st.session_state.ind, disabled = st.session_state.start, on_click = on_button_i_click):
        if len(st.session_state.remaining_words) != 0:
            if dispositivo == "Computer":
                st.warning("Per il salvataggio della memoria fornita selezionare **Salva memoria**.")
            else:
                st.warning("Per il salvataggio della memoria fornita premere prima sulla tastiera virtuale **INVIO** poi selezionare **Salva memoria**.")
            # Timer e il campo di input
            st.session_state.start_time = time.time()
            # Seleziona una parola casuale dalla lista di parole rimanenti
            st.session_state.selected_word = random.choice(st.session_state.remaining_words)
        else:
            # Se non ci sono parole da suggerire, disabilita il pulsante di registrazione
            st.warning("Hai già usato tutte le 10 parole, non è più possibile fare altre registrazioni. Selezionare **Salva Dati e Termina**")
            ten_w = True
    
    if st.session_state.show == True and ten_w == False:
        # Mostra la parola spunto
        st.write("**Racconta una memoria** che recuperi prendendo spunto dalla parola:")
        st.header(f"**{st.session_state.selected_word}**")
        # Mostra il modulo di registrazione 
        st.warning("Se si volesse utilizzare la trascrizione automatica premere **Start Recording**, quando ci si vuole fermare premere **Stop** e **ATTENDERE qualche secondo** per il caricamento del file audio temporaneo. Nel caso in cui **NON** ci sia feedback visivo della registrazione in corso o l'audio finale abbia durata di 0 secondi, fare ripartire la registrazione premendo prima **Stop** (se non si è già premuto) e poi **Start Recording**.")
        st.session_state.wav_audio_data = st_audiorec()

    # Trascrizione automatica tramite modulo speech to text
    if st.session_state.wav_audio_data is not None:
        # Converti l'audio registrato in formato WAV
        if st.session_state.show == True:
            st.warning("**Attendere**, sto generando la trascrizione. Vi è la possibilità di correggerla prima di salvarla.")
        audio_file = BytesIO(st.session_state.wav_audio_data)
        audio_segment = AudioSegment.from_file(audio_file)
        st.session_state.time_rec = len(audio_segment)/1000 # da [ms] a [s]
        
        # Salva temporaneamente il file WAV per la trascrizione
        temp_file = "temp_audio.wav"
        audio_segment.export(temp_file, format="wav")
        st.session_state.transcription = transcribe_audio(temp_file)

    visible = lambda x: "visible" if x else "collapsed"
    able = lambda x, y: False if x and not y else True
    if dispositivo == "Computer":
        st.session_state.testo = st.text_area("**Scrivi** qui il tuo testo una volta vista la **parola** da cui recuperare la memoria, oppure **modifica** qui la **trascrizione** dell'audio:",
                                              value = st.session_state.transcription,
                                              height = 300,
                                              key = len(st.session_state.remaining_words),
                                              disabled = able(st.session_state.show, ten_w),
                                              label_visibility = visible(st.session_state.show))
    else:
        if st.session_state.transcription != "":
            st.write("**Trascrizione audio:**")
            st.write(st.session_state.transcription)
            st.warning("La **modifica** della trascrizione da smartphone potrebbe essere più difficoltosa che da computer, per potervi muovere lungo il testo utilizzare il **cursore mobile** nel campo testuale (tenendo premuto e spostando la lineaa verticale lampeggiante).")
        st.session_state.testo = st.text_input("**Scrivi** qui il tuo testo una volta vista la **parola** da cui recuperare la memoria, oppure **modifica** qui la **trascrizione** dell'audio:",
                                                value = st.session_state.transcription,
                                                key = len(st.session_state.remaining_words),
                                                disabled = able(st.session_state.show, ten_w),
                                                label_visibility = visible(st.session_state.show))
        if dispositivo == "Smartphone":
            st.warning("Per salvare correttamente le risposte date per iscritto nel campo testuale premere sulla tastiera virtuale **INVIO**.")
    
    def on_button_s_click():
        st.session_state.show = False
        st.session_state.start = False
        st.session_state.ind = "Prosegui"
    
    if len(st.session_state.remaining_words) != 0:
        if st.button("Salva memoria", disabled = not st.session_state.show, on_click = on_button_s_click):
            duration = time.time() - st.session_state.start_time
            # Aggiungi i dati di questa registrazione alla sessione
            st.session_state.session_data.append({
                "ID": st.session_state.new_token,
                "Eta": st.session_state.eta,
                "Gender": st.session_state.gender,
                "Nazionalita": st.session_state.nazione,
                "Educazione": st.session_state.educazione,
                "Occupazione": st.session_state.occupazione,
                "Caregiver": st.session_state.caregiver,
                "Limitazione": st.session_state.autonomia + " " + st.session_state.desc,
                "BDI2": results_d,
                "RRS" : results_r,
                "PCL-5-reexperiencing": results_p[0], 
                "PCL-5-avoidance": results_p[1],
                "PCL-5-altereted_cognition": results_p[2],
                "PCL-5-hyperarousal": results_p[3],
                "PCL-5-tot": results_p[4],
                "Cue-Word": st.session_state.selected_word,
                "Text": st.session_state.testo,
                "Time": duration,
                "Time_recording": st.session_state.time_rec
            })
            
            # Rimuovi la parola utilizzata dalla lista
            if st.session_state.selected_word in st.session_state.remaining_words:
                st.session_state.remaining_words.remove(st.session_state.selected_word)
            st.success(f"Registrazione completata. Dati salvati temporaneamente.")
            # Reset testo precedente
            st.session_state.transcription = ""
            st.session_state.testo = ""
            # Reset file audio
            st.session_state.wav_audio_data = None
            st.session_state.time_rec = 0
            st.write("")
            st.write("")
            st.write(f"Sono state fornite **{10 - len(st.session_state.remaining_words)}** memorie.")
            

    # Bottone per salvare i dati
    if st.session_state.session_data:
        st.write("")
        st.write("")
        st.write("Se si sono completate le **10 memorie** o se si desidera **interrompere**, premere:")
        if st.button(label = "Salva Dati e Termina"):
            save_and_upload_to_github(st.session_state.session_data)
            st.success("Grazie per aver partecipato alla raccolta dati!")
            st.success("Il tuo codice di accesso:", icon = "🔑")
            st.code(st.session_state.new_token, language='text')
            st.warning("Copia e conserva questo codice. Non potrai più visualizzarlo dopo aver chiuso la pagina.", icon = "💾")
            st.session_state.session_data.clear()
        st.write("Selezionando **Salva Dati e Termina** acconsenti al trattamento delle informazioni fornite per fini di ricerca, secondo quanto descritto in testa alla pagina.")

    st.header("BIBLIOGRAFIA")
    st.warning("**Leggere dopo** aver svolto il **test**.")
    st.write("")
    st.write("- **Beck Depression Inventory - II:**")
    st.write("Versione italiana del Beck Depression Inventory - II:")
    st.markdown("https://www.endowiki.it/images/stories/pdf/Beck-II-Italiano.pdf")
    #st.markdown("https://psicologiaecomunicazione.it/wp-content/uploads/2018/07/Inventario-per-la-Depressione-Di-Beck-Beck-Depression-Inventory.pdf")
    st.write("Descrizione, somministrazione e valutazione del Beck Depression Inventory - II:")
    st.markdown("https://www.itsalute.com/Condizioni-Trattamenti/depressione/Come-interpretare-il-Beck-Depression-Inventory-.html")
    st.write("")
    #st.markdown("https://academy.formazionecontinuainpsicologia.it/wp-content/uploads/2023/07/ruminative.pdf")
    st.write("- **Ruminative Response Scale:**")
    st.write("Versione italiana del Ruminative Response Scale:")
    st.markdown("http://siba-ese.unisalento.it/index.php/psychofenia/article/view/i17201632vXn17p15")
    st.write("Studio riguardante la correlazione tra depressione e ruminazione:")
    st.markdown("https://doi.org/10.1016/j.jbtep.2006.03.002")
    st.write("Descrizione, somministrazione e valutazione del Ruminative Response Scale:")
    st.markdown("https://psychologyroots.com/ruminative-responses-scale/")
    st.write("")
    st.write("- **Posttraumatic Stress Disorder Checklist - 5:**")
    st.write("Studio riguardante la definizioni dei criteri, secondo il Manuale Diagnostico e Statistico dei Disturbi Mentali (DSM):")
    st.markdown("https://www.ptsd.va.gov/professional/articles/article-pdf/id1628840.pdf")
    st.write("Descrizione, somministrazione e valutazione del Posttraumatic Stress Disorder Checklist - 5:")
    st.markdown("https://www.ptsd.va.gov/professional/assessment/adult-sr/ptsd-checklist.asp")
    st.write("Versione italiana del Posttraumatic Stress Disorder Checklist - 5:")
    st.markdown("https://www.center-tbi.eu/files/approved-translations/Italian/ITALIAN_PCL_PW.pdf")
    st.write("Esempio di suddivisione dei punteggi del Posttraumatic Stress Disorder Checklist - 5:")
    st.markdown("https://novopsych.com.au/wp-content/uploads/2024/08/PTSD-assessment-pcl-5-results-report-scoring.pdf")    
    st.write("")
    st.write("- **Cue-Word Autobiographic Memory Retrievial:**")
    st.write("Studio che ha raccolto memorie fornite da partecipanti online, per poi valutarle tramite schemi di codifica della narrazione autobiografica ed, infine, addestrarci un classificatore in grado di emulare la codifica umana:")
    st.markdown("https://doi.org/10.1080/09658211.2018.1507042")
    st.write("Studio che indica quali indici di benessere mentale solo correlati alla fenomenologia della memoria autobiografica:")
    st.markdown("https://pubmed.ncbi.nlm.nih.gov/15081887/")    

if __name__ == "__main__":
    main()
