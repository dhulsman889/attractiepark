# import modulen
from pathlib import Path
import json
import pprint
import mysql.connector
import mysql

# from database_wrapper import Database


# initialisatie

# parameters voor connectie met de database


mydb = mysql.connector.connect(
  host="localhost",
  user="admin",
  password="root",
  database="attractiepark"
)

db = mydb.cursor()
# main

# Haal de eigenschappen op van een personeelslid
# altijd verbinding openen om query's uit te voeren

personeelslid_id = input("Voer het ID van het personeelslid in: ")

# pas deze query aan om het juiste personeelslid te selecteren
personeelslid_query = f"SELECT * FROM personeelslid WHERE id = {personeelslid_id}"
personeelslid = db.execute(personeelslid_query)

personeelslid_data = db.fetchone()

if personeelslid_data:
    pprint.pp(personeelslid_data)
else:
    print("Geen personeelslid gevonden met het opgegeven ID.")

def fetch_onderhoudstaken(max_fysieke_belasting):
    if (personeelslid_data[4] == 'Senior'):
        print("Senior")
        select_onderhoudstaken = f"SELECT * FROM onderhoudstaak WHERE afgerond = 0 AND fysieke_belasting <= {max_fysieke_belasting}"
    elif (personeelslid_data[4] == 'Medior'):
        print("Medior")
        select_onderhoudstaken = f"SELECT * FROM onderhoudstaak WHERE afgerond = 0 AND bevoegdheid IN ('Medior', 'Junior', 'Stagiair') AND fysieke_belasting <= {max_fysieke_belasting}"
    elif (personeelslid_data[4] == 'Junior'):
        print("Junior")
        select_onderhoudstaken = f"SELECT * FROM onderhoudstaak WHERE afgerond = 0 AND bevoegdheid IN ('Junior', 'Stagiair') AND fysieke_belasting <= {max_fysieke_belasting}"
    else:
        print("Stagiair")
        select_onderhoudstaken = f"SELECT * FROM onderhoudstaak WHERE afgerond = 0 AND bevoegdheid = 'Stagiair' AND fysieke_belasting <= {max_fysieke_belasting}"

    onderhoudstaken = db.execute(select_onderhoudstaken)

    onderhoudstaken_data = db.fetchall(onderhoudstaken)

    print(onderhoudstaken_data[0][1], onderhoudstaken_data[0][2], onderhoudstaken_data[0][3], onderhoudstaken_data[0][4], onderhoudstaken_data[0][5])
    return(onderhoudstaken_data)

# Haal alle onderhoudstaken op die nog niet afgerond zijn en die het personeelslid mag uitvoeren
if(personeelslid_data[8] > 0):
    if(personeelslid_data[7] <= 24):
        max_fysieke_belasting = 25 - personeelslid_data[8]
        taken = fetch_onderhoudstaken(max_fysieke_belasting)
        print(taken)
    elif(personeelslid_data[7] > 24 and personeelslid_data[7] <= 50):
        max_fysieke_belasting = 40 - personeelslid_data[8]
        taken = fetch_onderhoudstaken(max_fysieke_belasting)
        print(taken)
    else:
        max_fysieke_belasting = 20 - personeelslid_data[8]
        taken = fetch_onderhoudstaken(max_fysieke_belasting)
        print(taken)

# altijd verbinding sluiten met de database als je klaar bent
db.close()

# pprint.pp(onderhoudstaken_data) # print de resultaten van de query op een overzichtelijke manier



# verzamel alle benodigde gegevens in een dictionary
# dagtakenlijst = {
#     "personeelsgegevens" : {
#         "naam": personeelslid[0]['naam'] # voorbeeld van hoe je bij een eigenschap komt
#         # STAP 1: vul aan met andere benodigde eigenschappen
#     },
#     "weergegevens" : {
#         # STAP 4: vul aan met weergegevens
#     }, 
#     "dagtaken": [] # STAP 2: hier komt een lijst met alle dagtaken
#     ,
#     "totale_duur": 0 # STAP 3: aanpassen naar daadwerkelijke totale duur
# }

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
# with open('dagtakenlijst_personeelslid_x.json', 'w') as json_bestand_uitvoer:
#     json.dump(dagtakenlijst, json_bestand_uitvoer, indent=4)