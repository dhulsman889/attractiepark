document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const gegevensContainer = document.getElementById('personeelsgegevens');
    const weergegevensContainer = document.getElementById('weergegevens');
    const onderhoudstakenContainer = document.getElementById('onderhoudstaken');
    const taakduurContainer = document.getElementById('taakduur');


    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) {
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            
            gegevensContainer.innerHTML = "";
            weergegevensContainer.innerHTML = "";
            onderhoudstakenContainer.innerHTML = "";
            taakduurContainer.innerHTML= "";

            const data = JSON.parse(e.target.result);

            console.log(data);

            // Voorkeuren weergeven
            const personeelsgegevensDiv = document.createElement('div');
            personeelsgegevensDiv.classList.add('voorkeur');
            let personeelsgegevensHTML = ``;

            if (data.personeelsgegevens) {
                const nameHeader = document.createElement('h1');
                nameHeader.textContent = `${data.personeelsgegevens["naam"]}s dagtakenlijst 🚧🛠️`;
                gegevensContainer.appendChild(nameHeader);
    
                Object.keys(data.personeelsgegevens).forEach(key => {
                    personeelsgegevensHTML += `<div class="voorkeur-info">${key.charAt(0).toUpperCase() + key.slice(1)}: ${data.personeelsgegevens[key]}</div>`;
                });
            } else {
                // Voorkeuren niet volgens format in JSON aanwezig.
                personeelsgegevensHTML += `<div class="voorkeur-info">Hier moeten de personeelsgegevens komen. </div>`;
            }

            personeelsgegevensDiv.innerHTML = personeelsgegevensHTML;
            gegevensContainer.appendChild(personeelsgegevensDiv);

          
            // Weergegevens weergeven
            const weergegevensDiv = document.createElement('div');
            weergegevensDiv.classList.add('voorkeur');
            let weergegevensHTML = ``;
            if (data.weergegevens) {
                weergegevensHTML += '<div class="voorkeur-info">Weergegevens 🌞</div>'
                Object.keys(data.weergegevens).forEach(key => {
                    weergegevensHTML += `<div class="voorkeur-info">${key.charAt(0).toUpperCase() + key.slice(1)}: ${data.weergegevens[key]}</div>`;
                });
            } else {
                // Weergegevens niet volgens format in JSON aanwezig.
                weergegevensHTML += `<div class="voorkeur-info">Hier moeten weergegevens komen. </div>`;
            }
       
            weergegevensDiv.innerHTML = weergegevensHTML;
            weergegevensContainer.appendChild(weergegevensDiv);

            // Onderhoudstaken weergeven
            aantalTaken = 0;
            if (data.dagtaken && data.dagtaken.length > 0) {
                data.dagtaken.forEach((taak) => {
                    const li = document.createElement('li');
                    if (taak.omschrijving && taak.omschrijving.toLowerCase() == "pauze") {
                        li.classList.add('pauze')
                        li.innerHTML = `<div class="time"><b>PAUZE</b></div>
                                        <p> Duur: ${taak.duur} minuten <br></p>`;
                    } else if (taak.type) {
                        const div = document.createElement('div')
                        div.classList.add('spoedreparatie')
                        div.innerHTML = `<b>- Tijdsblok spoedreparaties -</b>`;
                        taak.alternatieve_onderhoudstaken.forEach((alternatieve_taak) => {
                            aantalTaken++
                            div.innerHTML += `
                            <p>
                                #${aantalTaken} - ${alternatieve_taak.omschrijving} (Prio ${alternatieve_taak.prioriteit}) <br>
                                Duur: ${alternatieve_taak.duur} minuten <br>
                                Beroepstype: ${alternatieve_taak.beroepstype} <br>
                                Bevoegdheid: ${alternatieve_taak.bevoegdheid} <br>
                                Attractie: ${alternatieve_taak.attractie || '-'} <br>
                                Buitenwerk: ${alternatieve_taak.is_buitenwerk} <br>
                                Fysieke belasting: ${alternatieve_taak.fysieke_belasting || "-"} 

                            </p>`
                        })
                        div.innerHTML += `</div>`
                        li.appendChild(div)
                    } else if (taak.omschrijving && taak.omschrijving.toLowerCase() == "administratietijd") {
                        li.innerHTML = `<div class="time"><b>Administratietijd</b></div>
                                        <p>
                                            Aantal taken: ${taak.aantal_taken} <br>
                                            Duur: ${taak.duur} minuten <br>
                                        </p>`;
                    } else {
                        aantalTaken++
                        li.innerHTML = `
                        <div class="time"><b>#${aantalTaken} - ${taak.omschrijving} (Prio ${taak.prioriteit})</b></div>
                           <p>
                               Duur: ${taak.duur} minuten <br>
                               Beroepstype: ${taak.beroepstype} <br>
                               Bevoegdheid: ${taak.bevoegdheid} <br>
                               Attractie: ${taak.attractie || '-'} <br>
                               Buitenwerk:  ${taak.is_buitenwerk === 1 ? "ja" : "nee"} <br>
                               Fysieke belasting: ${taak.fysieke_belasting|| "-"} 
                           </p>`;
    
                    }
               
                    onderhoudstakenContainer.appendChild(li);
                });
            } else {
                const onderhoudstakenDiv = document.createElement('li');
                onderhoudstakenDiv.innerHTML = "<div>Hier moeten dagtaken komen. <\div>"
                onderhoudstakenContainer.appendChild(onderhoudstakenDiv)
            }
            

            // Totale taakduur weergeven
            const taakduurGegevensDiv = document.createElement('div');
            taakduurGegevensDiv.classList.add('voorkeur');
            taakduurGegevensDiv.innerHTML = `<div class="voorkeur-info"> Totaal geplande tijd: ${data.totale_duur} minuten<\div>`
            taakduurContainer.appendChild(taakduurGegevensDiv)
        };
        reader.readAsText(file);
    });
});
