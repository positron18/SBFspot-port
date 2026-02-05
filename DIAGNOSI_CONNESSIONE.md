# Diagnosi Problemi di Connessione Inverter

## Sintesi del Problema
Il monitor basato sulla versione Python (`monitor.py`) non riesce ad individuare l'inverter sulla rete locale tramite il processo di auto-discovery, nonostante l'inverter sia raggiungibile e operativo.

## Prove Effettuate e Risultati
1.  **Ping Test**: `ping 192.168.192.100` → **SUCCESSO**. L'inverter risponde a basso livello.
2.  **Original SBFspot (C++)**: Funziona correttamente poiché utilizza l'IP statico configurato in `SBFspot.cfg`.
3.  **Python Direct Test (`test_direct.py`)**: **SUCCESSO**. Utilizzando l'IP diretto, la libreria Python comunica perfettamente con l'inverter.
4.  **Python Auto-Discovery (`monitor.py`)**: **FALLITO**. Lo script non riceve risposte dai pacchetti di ricerca.

## Causa Radice (Root Cause)
Il problema risiede nel **Protocollo di Discovery Speedwire** (UDP multicast/broadcast sulla porta 9522). 

L'auto-discovery funziona inviando pacchetti a tutta la rete ("chi c'è?"). Per motivi legati alla configurazione di rete o del router (spesso dopo un riavvio o cambio di firmware):
-   I pacchetti multicast/broadcast vengono bloccati dal router.
-   Oppure l'inverter, pur essendo acceso, non risponde correttamente alle richieste di discovery ma accetta solo connessioni dirette (unicast).

### Gestione Indirizzi IP Dinamici
L'inverter potrebbe cambiare indirizzo IP nel tempo se non è configurato con un IP statico. Questo causerebbe il fallimento del discovery.
**Soluzione:** È consigliato impostare una "DHCP Reservation" sul router per l'indirizzo MAC dell'inverter (es. `192.168.192.100`).

### Analisi Tecnica: Storico Dati e Flag `-finq`
Dall'analisi del codice C++ (SBFspot) è emerso quanto segue:

1.  **Recupero Storico (`ArchiveDayData`)**:
    *   SBFspot richiede esplicitamente lo storico usando il comando `0x70000200`.
    *   Usa un byte di controllo speciale (`0xE0`) invece di quello standard per i dati istantanei (`0xA0`).
    *   Riceve record da 12 byte (Timestamp + Energia Totale accumulata).
    *   Calcola la potenza media (W) tra due intervalli confrontando l'incremento di energia nel tempo.
2.  **Flag `-finq` (Force Inquiry)**:
    *   SBFspot calcola l'ora di alba e tramonto in base alle coordinate geografiche nel file `.cfg`.
    *   Se è buio, il programma normalmente termina subito per evitare timeout (molti inverter SMA "dormono" di notte).
    *   Il flag `-finq` forza il programma a provare la connessione anche se è buio. Fondamentale per sistemi con batterie (come il tuo) che restano attivi H24.

### Stato del Porting Python
Abbiamo aggiornato la libreria Python per supportare:
*   [x] Connessione diretta via IP (già testata con successo).
*   [x] Byte di controllo `0xE0` per le richieste di archivio.
*   [x] Struttura dati per lo storico giornaliero (`DayData`).
*   [ ] Debug dell'errore `0x17` (Invalid Arguments) restituito dall'inverter sulle richieste storiche.

## Il Rischio dell'IP Dinamico
Hai perfettamente ragione: se l'inverter è in DHCP, il suo indirizzo IP potrebbe cambiare al prossimo riavvio del router o alla scadenza del "lease" DHCP. Questo romperebbe la connessione fissa a `192.168.192.100`.

### Perché l'Auto-Discovery è fondamentale?
L'auto-discovery serve proprio a risolvere questo: lo script chiede "Dove sei?" e l'inverter risponde col suo nuovo IP. Se il discovery non funziona, siamo "ciechi" di fronte a un cambio di indirizzo.

## Strategie per la Stabilità Permanente

### 1. Prenotazione DHCP (Consigliato)
La soluzione più robusta è configurare il router per assegnare **sempre lo stesso IP** al MAC address dell'inverter. 
- Entra nel pannello del router.
- Cerca "DHCP Reservation" o "Static Leases".
- Associa l'IP `192.168.192.100` al dispositivo SMA.
In questo modo, anche se il discovery fallisce, l'indirizzo non cambierà mai.

### 2. IP Statico sull'Inverter
È possibile impostare un IP statico direttamente nelle impostazioni dell'inverter (tramite Sunny Explorer o interfaccia web, se disponibile). Questo è il metodo più "ferreo" ma richiede l'accesso alle impostazioni protette dell'inverter.

### 3. Fallback "Subnet Scan" (Soluzione Software)
Se non puoi agire sul router, possiamo rendere il software più intelligente:
- Se l'auto-discovery (multicast) fallisce, lo script può provare a fare un "giro di telefonate" (unicast) a tutti gli IP della sottorete `192.168.192.1` -> `192.168.192.254`.
- È un po' più lento (circa 10-20 secondi), ma troverebbe l'inverter anche se il multicast è bloccato e l'IP è cambiato.

**Stato Finale**: Al momento siamo collegati via IP diretto. Per il lungo termine, la **Prenotazione DHCP** sul router è la mossa migliore per dormire sonni tranquilli.

