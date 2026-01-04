try:
    import google.genai as genai
except ImportError:
    import google.generativeai as genai
    print("⚠️ Bitte installiere das neue Paket: pip install google-genai")

import PIL.Image
from instagrapi import Client
import time
import random
import os

# --- 1. KONFIGURATION ---
GEMINI_API_KEY = "AIzaSyDJOPjW_u14R7PbHYlQ7Cn4QZkVy0dj3Ng" 
INSTA_USER = "oldgreasyboy"
INSTA_PASS = "OLIVER221705!"

# Name der Datei, in der wir den Login speichern
SESSION_DATEI = "session.json"

# Gemini Setup
try:
    # Neue API
    client = genai.Client(api_key=GEMINI_API_KEY)
    model = client.models.generate_content
    USE_NEW_API = True
except:
    # Alte API (deprecated)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    USE_NEW_API = False

# Temp-Ordner erstellen falls nicht vorhanden
if not os.path.exists('temp'):
    os.makedirs('temp')
    print("📁 'temp' Ordner erstellt.")

# Speicher für erledigte Posts
bearbeitete_posts = []

def generiere_frechen_kommentar(bild_pfad):
    try:
        img = PIL.Image.open(bild_pfad)
        prompt = (
            "Du bist ein frecher Instagram-User. Analysiere das Bild. "
            "Schreibe einen kurzen Kommentar (max 10 Wörter). "
            "Witzig, leicht sarkastisch oder eine Frage. "
            "Nutze 1 Emoji. Keine Hashtags."
        )
        
        if USE_NEW_API:
            response = model(
                model='gemini-1.5-flash',
                contents=[prompt, img]
            )
            return response.text.strip()
        else:
            response = model.generate_content([prompt, img])
            return response.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini Fehler: {e}")
        return "Wild! 🔥"

def start_bot():
    print("🤖 Bot startet...")
    cl = Client()
    
    # --- NEU: LOGIN MIT SESSION ---
    # 1. Versuchen, alte Sitzung zu laden
    if os.path.exists(SESSION_DATEI):
        print("📂 Lade gespeicherte Sitzung...")
        try:
            cl.load_settings(SESSION_DATEI)
        except Exception as e:
            print(f"⚠️ Konnte Sitzung nicht laden, starte neu: {e}")

    # 2. Einloggen (nutzt die Sitzung, wenn vorhanden)
    try:
        cl.login(INSTA_USER, INSTA_PASS)
        print(f"✅ Erfolgreich eingeloggt als {INSTA_USER}")
    except Exception as e:
        print(f"❌ Login fehlgeschlagen: {e}")
        return

    # 3. Sitzung sofort speichern (für das nächste Mal)
    cl.dump_settings(SESSION_DATEI)
    print("💾 Sitzung gespeichert.")

    # --- ENDE LOGIN ---

    my_id = cl.user_id_from_username(INSTA_USER)
    
    while True:
        try:
            following = cl.user_following(my_id)
            print(f"🔍 Überprüfe {len(following)} Accounts...")

            for user_id in following:
                time.sleep(random.uniform(3, 8)) 

                try:
                    # Versuche zuerst die V1-API (robuster)
                    medias = cl.user_medias_v1(user_id, amount=1)
                except Exception as e:
                    # Bei Fehler: überspringen und weitermachen
                    if "data" in str(e) or "validation" in str(e).lower():
                        # Bekannter Instagram API Fehler - ignorieren
                        pass
                    continue
                
                if not medias:
                    continue

                latest_media = medias[0]

                if latest_media.id in bearbeitete_posts:
                    continue

                if latest_media.media_type != 1:
                    # Es ist ein Video/Reel -> Ignorieren
                    bearbeitete_posts.append(latest_media.id)
                    continue

                print(f"🔥 Neues FOTO gefunden bei User {user_id}!")

                path = None
                try:
                    # Bild herunterladen
                    path = cl.photo_download(latest_media.pk, folder="temp")
                    
                    if not path or not os.path.exists(path):
                        print("⚠️ Bild-Download fehlgeschlagen.")
                        bearbeitete_posts.append(latest_media.id)
                        continue
                    
                    # Kommentar generieren
                    kommentar = generiere_frechen_kommentar(path)
                    print(f"📝 Kommentar: {kommentar}")
                    
                    # Kommentar posten
                    cl.media_comment(latest_media.id, kommentar)
                    print("✅ Gepostet!")
                    
                    bearbeitete_posts.append(latest_media.id)
                    
                    print("⏳ Warte sicherheitshalber...")
                    time.sleep(random.uniform(40, 80))

                except Exception as e:
                    print(f"❌ Fehler beim Posten: {e}")
                    bearbeitete_posts.append(latest_media.id)
                finally:
                    if path and os.path.exists(path):
                        try:
                            os.remove(path)
                        except:
                            pass

            print("💤 Runde fertig. Schlafe 5 Minuten...")
            time.sleep(300)

        except KeyboardInterrupt:
            print("\n🛑 Bot gestoppt.")
            break
        except Exception as e:
            print(f"⚠️ Haupt-Loop Fehler: {e}")
            print("⏳ Warte 60 Sekunden...")
            time.sleep(60)

if __name__ == "__main__":
    start_bot()