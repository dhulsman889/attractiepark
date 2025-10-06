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
        select_onderhoudstaken = f"SELECT * FROM onderhoudstaak WHERE afgerond = 0 AND fysieke_belasting <= {max_fysieke_belasting} AND beroepstype = '{personeelslid_data[3]}'"
    elif (personeelslid_data[4] == 'Medior'):
        select_onderhoudstaken = f"SELECT * FROM onderhoudstaak WHERE afgerond = 0 AND bevoegdheid IN ('Medior', 'Junior', 'Stagiair') AND fysieke_belasting <= {max_fysieke_belasting} AND beroepstype = '{personeelslid_data[3]}'"
    elif (personeelslid_data[4] == 'Junior'):
        select_onderhoudstaken = f"SELECT * FROM onderhoudstaak WHERE afgerond = 0 AND bevoegdheid IN ('Junior', 'Stagiair') AND fysieke_belasting <= {max_fysieke_belasting} AND beroepstype = '{personeelslid_data[3]}'"
    else:
        select_onderhoudstaken = f"SELECT * FROM onderhoudstaak WHERE afgerond = 0 AND bevoegdheid = 'Stagiair' AND fysieke_belasting <= {max_fysieke_belasting} AND beroepstype = '{personeelslid_data[3]}'"

    db.execute(select_onderhoudstaken)

    onderhoudstaken_data = db.fetchall()

    print(f"\nTaak 1: {onderhoudstaken_data[0][1]}\nTijd: {onderhoudstaken_data[0][2]}\nPrioriteit: {onderhoudstaken_data[0][3]}\nFysieke belasting: {onderhoudstaken_data[0][6]}\nBeroepstype: {onderhoudstaken_data[0][5]}\n")
    return onderhoudstaken_data

# Haal alle onderhoudstaken op die nog niet afgerond zijn en die het personeelslid mag uitvoeren
if(personeelslid_data[7] <= 24):
    max_fysieke_belasting = 25 - personeelslid_data[8]
    taken = fetch_onderhoudstaken(max_fysieke_belasting)
elif(personeelslid_data[7] > 24 and personeelslid_data[7] <= 50):
    max_fysieke_belasting = 40 - personeelslid_data[8]
    taken = fetch_onderhoudstaken(max_fysieke_belasting)
else:
    max_fysieke_belasting = 20 - personeelslid_data[8]
    taken = fetch_onderhoudstaken(max_fysieke_belasting)
pprint.pp(taken)

for taak in taken:
    print(f"Taak: {taak[1]}\nTijd: {taak[2]}\nPrioriteit: {taak[3]}\nFysieke belasting: {taak[6]}\nBeroepstype: {taak[5]}")

# altijd verbinding sluiten met de database als je klaar bent
mydb.close()

def generate_schedule(taken, werktijd, pauze_opsplitsen):
    # defensive inputs
    try:
        werktijd = int(werktijd)
    except Exception:
        werktijd = 0
    pauze_opsplitsen = bool(pauze_opsplitsen)

    # Normalize DB rows (tuples) into mutable dicts with integer durations
    norm_taken = []
    for row in taken:
        naam = row[1] if len(row) > 1 else '<onbekend>'
        try:
            duur = int(row[2]) if row[2] is not None else 0
        except Exception:
            try:
                duur = int(str(row[2]))
            except Exception:
                duur = 0
        norm_taken.append({'id': row[0] if len(row) > 0 else None, 'naam': naam, 'duur': duur})

    taken = norm_taken

    rooster = []
    tijd = 0
    taken_idx = 0

    # Pauze-instellingen: (start_minute, duur_minuten, label)
    if pauze_opsplitsen:
        pauzes = [(werktijd // 3, 15, "Pauze 1 (15 min)"), (2 * werktijd // 3, 15, "Pauze 2 (15 min)")]
    else:
        pauzes = [(werktijd // 2, 30, "Pauze (30 min)")]
    volgende_pauze = 0

    while tijd < werktijd and taken_idx < len(taken):
        taak = taken[taken_idx]
        duur = taak['duur']

        # Check of de volgende pauze midden in deze taak valt en of de pauze volledig past
        if volgende_pauze < len(pauzes):
            bp, bd, bl = pauzes[volgende_pauze]
            if tijd <= bp < tijd + duur and bp + bd <= werktijd:
                # Plan deel van taak tot pauze
                until = bp - tijd
                if until > 0:
                    rooster.append((tijd, tijd + until, f"Taak: {taak['naam']} (deels)"))
                    taak['duur'] -= until
                    tijd += until
                # Plan pauze
                rooster.append((tijd, tijd + bd, bl))
                tijd += bd
                volgende_pauze += 1
                continue

        # Plan (resterende) taak volledig als er ruimte is, anders plan gedeeltelijk en stop
        if tijd + duur <= werktijd:
            rooster.append((tijd, tijd + duur, f"Taak: {taak['naam']}"))
            tijd += duur
            taken_idx += 1
        else:
            resterend = werktijd - tijd
            if resterend > 0:
                rooster.append((tijd, tijd + resterend, f"Taak: {taak['naam']} (deels)"))
            tijd = werktijd
            break

    # Plan eventuele nog niet ingeplande pauzes die volledig binnen werktijd passen
    while volgende_pauze < len(pauzes):
        bp, bd, bl = pauzes[volgende_pauze]
        if bp + bd <= werktijd and all(not (s == bp and e == bp + bd and lbl == bl) for s, e, lbl in rooster):
            # Voeg alleen toe als de pauze nog niet overlapt met bestaande items
            rooster.append((bp, bp + bd, bl))
        volgende_pauze += 1

    # Sorteer op starttijd en return
    rooster.sort(key=lambda x: x[0])
    return rooster

# verzamel alle benodigde gegevens in een dictionary
dagtakenlijst = {
    "personeelsgegevens" : {
        "naam": personeelslid_data[1],
        "werktijden": personeelslid_data[2],
        "bevoegdheid": personeelslid_data[4],
        "verlaagde_fysieke_belasting": personeelslid_data[8],
        "max_fysieke_belasting": max_fysieke_belasting
    },
    "weergegevens" : {
        # STAP 4: vul aan met weergegevens
    }, 
    "dagtaken": generate_schedule(taken, personeelslid_data[2], personeelslid_data[6])
    ,
    "totale_duur": sum(taak[2] for taak in taken) # STAP 3: aanpassen naar daadwerkelijke totale duur
}

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open('dagtakenlijst_personeelslid_x.json', 'w') as json_bestand_uitvoer:
    json.dump(dagtakenlijst, json_bestand_uitvoer, indent=4)