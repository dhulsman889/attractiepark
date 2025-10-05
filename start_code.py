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

# pas deze query aan om het juiste personeelslid te selecteren
select_query = "SELECT * FROM personeelslid WHERE id = 1"
personeelslid = db.execute(select_query)

myresult = db.fetchone()

if myresult:
    pprint.pp(myresult)
else:
    print("Geen personeelslid gevonden met het opgegeven ID.")
# altijd verbinding sluiten met de database als je klaar bent
# db.close()

# pprint.pp(personeelslid) # print de resultaten van de query op een overzichtelijke manier
# print(personeelslid[0]['naam'])



# Haal alle onderhoudstaken op
# altijd verbinding openen om query's uit te voeren
# db.connect()

# pas deze query aan en voeg queries toe om de juiste onderhoudstaken op te halen
# select_query = "SELECT * FROM onderhoudstaak"
# onderhoudstaken = db.execute(select_query)

# altijd verbinding sluiten met de database als je klaar bent
# db.close()

# pprint.pp(onderhoudstaken) # print de resultaten van de query op een overzichtelijke manier



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