# Dubblettjägaren för Windows

Ett grafiskt Python-program för att hitta filer med identiskt innehåll även om filnamnen skiljer sig.

## Starta

1. Installera Python 3.10+ för Windows från python.org (med Tkinter).
2. Ladda ner filen duplicate_finder.py.
3. Öppna PowerShell i den nedladdade mappen och kör: python duplicate_finder.py
4. Välj en mapp och klicka på Sök dubbletter.

Ingen ytterligare Python-modul behöver installeras.

## Funktioner

- Söker rekursivt och grupperar filer efter storlek och SHA-256.
- Visar identiska filer, låter dig öppna mappen och exportera fullständigt CSV-resultat.
- Alla analyser körs lokalt. Inga filer flyttas, ändras eller raderas.
- Hoppar över symboliska länkar och rapporterar oåtkomliga eller förändrade filer.
- Visar högst 5000 rader, men exporterar alla.

## Viktigt

Beräknad platsbesparing är en uppskattning, inte en garanti. Hardlinks kan peka på samma lagrade data. Undersök alltid dubbletter manuellt före eventuell radering. Detta är källkod, inte en signerad .exe-fil; programmet har inte testats på din dator.

Detta projekt ligger i en egen mapp i en separat branch för att inte ändra den befintliga iOS-appen.
