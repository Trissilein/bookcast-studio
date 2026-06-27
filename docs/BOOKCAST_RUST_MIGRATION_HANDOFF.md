# BookCast Rust Migration - Handoff

Stand: 2026-06-26

## Ziel

BookCast wird im selben Repo als Rust-first Desktop-Client neu aufgebaut.
Die neue Hauptoberfläche soll mit Slint laufen und zuerst den Bedienfluss
verbessern:

- Queue
- Progress
- Cancel
- Engine-Auswahl
- Import-Wizard
- `audio.cpp`-Monitoring mit `Update Available`

Die bestehende Python-App bleibt als Bridge und Migrationshilfe erhalten.
`audio.cpp` wird nicht per FFI eingebunden, sondern als externer Prozess oder
lokaler Dienst.

## Harte Leitplanken

- Kein Big-Bang-Rewrite.
- Python nicht löschen, nicht umbauen, nur als Bridge weiterverwenden.
- `audio.cpp` nur über Prozessgrenze anbinden.
- Rust UI ist der neue Primärpfad.
- Update-Verhalten ist `Check + Flag`, kein Auto-Sync.
- Erstes MVP ist `TTS Studio`, nicht der komplette Audiobook-Import.

## Aktueller Stand

- Im Repo liegt bereits ein Rust-Workspace-Root `Cargo.toml`.
- Das vorhandene Python-Backend ist funktional und darf als Fallback dienen.
- `ffmpeg` ist im PATH.
- Der `audio.cpp`-Upstream-HEAD ist aktuell auf:

```text
99a95d7e10407c5bdcd133b149d23e7a5ac1880d
```

## Umsetzungsreihenfolge

### 1. Rust-App scaffolden

- Workspace-Mitglied `rust/bookcast-rust` anlegen.
- `Cargo.toml`, `build.rs`, `src/main.rs`, UI-Datei für Slint anlegen.
- UI zuerst simpel, aber brauchbar:
  - Queue-Ansicht
  - Job-Status
  - Fortschritt
  - Engine-Auswahl
  - Import-Wizard-Bereich
  - `audio.cpp`-Statuszeile

### 2. Python-Bridge einhängen

- Einen kleinen Rust-Bridge-Layer bauen, der die vorhandenen Python-Commands
  aufruft.
- Ziel: vorhandene Import-/Renderlogik bleibt weiter nutzbar.
- Fallback für die ersten Render-Schritte bleibt Python.

### 3. `audio.cpp` als externe Engine integrieren

- `audio.cpp` als auswählbaren Engine-Adapter behandeln.
- Kein FFI.
- Ausführung über Subprozess oder lokalen Server-Wrapper.
- Die konkrete CLI kann erstmal konfigurierbar sein.

### 4. `audio.cpp`-Update-Monitor

- Beim App-Start prüfen.
- Per Refresh prüfen.
- Vergleich:
  - lokaler gepinnter Stand
  - Remote-HEAD von `https://github.com/0xShug0/audio.cpp`
- Wenn ungleich: `Update Available` anzeigen.

### 5. Queue + Cancel

- Queue in Rust verwalten.
- Aktiven Job anzeigen.
- Cancel soll laufende Prozesse abbrechen können oder mindestens den Job
  sauber markieren und die Queue stoppen.

### 6. Import-Wizard

- Geführter Import für lokale Quellen.
- Erst die robuste Variante:
  - Pfad wählen
  - Quelle prüfen
  - Fehler erklären
  - Preview anzeigen
- Calibre-Import als eigener Wizard-Schritt.

## Konkrete Arbeitspakete

### Paket A - UI-Skelett

- Slint UI anlegen.
- Tabs oder klare Bereiche für:
  - `TTS Studio`
  - `Import`
  - `Queue`
  - `Settings`
- Minimal brauchbares Layout.

### Paket B - Bridge

- Python-Interpreter finden.
- Bridge-Command definieren.
- Output und Fehler sauber ins UI loggen.

### Paket C - Engine-Registry

- `audio.cpp`
- Python bridge
- Fallback-Engine

### Paket D - Update-Check

- Pinned Revision-Datei anlegen.
- Git-Remote-Check durchführen.
- Status im UI anzeigen.

### Paket E - Import-Wizard

- Calibre-Ordner finden
- Bibliothek scannen
- Fehlerbilder erklären
- Import-Vorschlag erzeugen

## Was Claude als Nächstes tun soll

1. Das Rust-Workspace im Repo fertig scaffolden.
2. Slint-UI als erstes lauffähiges Fenster bauen.
3. Python-Bridge ankoppeln, ohne die bestehende App zu zerstören.
4. `audio.cpp`-Adapter als Subprozess/Server-Integration anlegen.
5. Update-Monitor für `audio.cpp` einbauen.
6. Danach Queue, Cancel und Import-Wizard ausarbeiten.

## Akzeptanzkriterien für den ersten Rust-Slice

- App startet mit nativer Rust-UI.
- Queue ist sichtbar.
- Engine kann umgeschaltet werden.
- Import-Wizard ist sichtbar.
- `audio.cpp`-Status kann `Update Available` zeigen.
- Python-Workflows bleiben weiterhin erreichbar.

## Wichtige Dateien

- `Cargo.toml`
- `rust/bookcast-rust/Cargo.toml`
- `rust/bookcast-rust/build.rs`
- `rust/bookcast-rust/src/main.rs`
- `rust/bookcast-rust/ui/bookcast.slint`
- `README.md`
- `docs/MILESTONES.md`

## Copy-Paste Brief für Claude

> Arbeite im Repo `bookcast-studio`.
> Ziel: Rust-first Desktop-Client mit Slint.
> Halte Python nur als Bridge und Fallback.
> Integriere `audio.cpp` als externen Prozess oder lokalen Dienst.
> Baue zuerst ein lauffähiges UI mit Queue, Progress, Cancel, Engine-Auswahl und Import-Wizard.
> Implementiere dazu einen `audio.cpp`-Update-Check gegen den Remote-HEAD.
> Kein Big-Bang-Rewrite, kein FFI, kein Entfernen der Python-App.
> Erstes Ziel ist ein brauchbares `TTS Studio`-MVP.

