# QBM — Quantum BareMetal VM

> **QBM fait une chose, une seule : rendre la confiance vérifiable.**

---

## Deux intelligences

| Intelligence de génération | Intelligence de fiabilité |
|---|---|
| Produire, créer, répondre | Tenir, vérifier, ne jamais dévier |
| GPT, Claude, Gemini, DeepSeek | **QBM** |
| Le poète improvise | **Le gardien ne dort jamais** |

L'industrie conçoit l'IA comme un monolithe. NUMEN la conçoit comme un **système** :
un composant propose (LLM, humain, capteur), un autre vérifie et juge (QBM).
**La séparation fait la confiance.**

---

## Qu'est-ce que QBM ?

Machine virtuelle déterministe de **gouvernance agentique**.
7 instructions, 14 appels natifs, 64 Ko RAM, 16 registres.
MiniLM-L6-v2 (~80 Mo) embarqué — pas un LLM, juste 384 nombres pour comparer du sens sans jamais comprendre.

- **L'humain** apporte l'intention
- **Le LLM** propose
- **Le silicium** (QBM) vérifie et juge

*Le bytecode impose, le prompt suggère. Le transistor ne négocie pas.*

---

## Architecture technique

| Composant | Spécification |
|-----------|--------------|
| Instructions | MOV, ADD, CMP, JMP, CALL, LOAD, STOR |
| Appels natifs | HALT, CONSOLE_OUT, HASH_SHA256, ED25519_SIGN, ED25519_VERIFY, P2P_SEND, P2P_RECV, RANDOM, TIME |
| Appels sémantiques | EMBED_TEXT (MiniLM-L6-v2, 384 float32), COSINE_SIM (score 0-10000), LOAD_MODEL |
| RAM | 64 Ko |
| Registres | 16 × 32 bits (R0-R12, LR, SP, PC) |
| Flags | Zero, Carry, Negative |

---

## Trajectoire naturelle

```
┌──────────────────────────────────────────────────────────┐
│  ÉTAPE 1 — VM logicielle (aujourd'hui)                   │
│  qbm.py → Python → OS → CPU                              │
│  476 lignes, dépend de Python, portable                  │
│  Usage : développement, démo, prototypage                │
├──────────────────────────────────────────────────────────┤
│  ÉTAPE 2 — VM compilée (proche)                          │
│  qbm.rs → ELF binaire → OS → CPU                         │
│  Mêmes 7 instructions, plus rapide, pas de Python        │
│  Usage : production, embarqué sur serveur                │
├──────────────────────────────────────────────────────────┤
│  ÉTAPE 3 — VM bare-metal (moyen terme)                   │
│  qbm.bin → CPU (pas d'OS)                                │
│  La VM EST le firmware. Boot direct.                     │
│  Usage : Raspberry Pi, microcontrôleurs, satellites      │
├──────────────────────────────────────────────────────────┤
│  ÉTAPE 4 — VM en silicium (long terme)                   │
│  FPGA / ASIC → transistors → pas de CPU hôte             │
│  7 instructions câblées en hardware                      │
│  Consommation : milliwatts                               │
│  Usage : pacemakers, capteurs autonomes, nœuds P2P       │
└──────────────────────────────────────────────────────────┘
```

**Étape 1 : atteinte.** Démo passée le 20 Mai 2026.

---

## QBM dans l'écosystème NUMEN

QBM est la **couche 5** de l'architecture agentique symbiotique :

```
HUMAIN → SUI → SP → AGENT → Chaîne d'Agents → QBM → SILICIUM
(parle)  (capte)(encode)(traduit)  (vérifie)   (contraint)(exécute)
                              ↓
                         EMBASSY (registre)
```

| # | Couche | Rôle |
|---|---|---|
| 1 | SUI | Symbiotic User Interface — capte l'intention |
| 2 | SP | Symphony Protocol — standard humain→agent |
| 3 | Agent | Traduction intention → actions |
| 4 | Chaîne d'Agents | Vérification en cascade, conformité |
| **5** | **QBM** | **Contrainte déterministe. Le gardien.** |
| 6 | Embassy | Registre immuable, signatures, preuves |
| 7 | Silicium | Exécution physique |

---

## Installation

```bash
pip install sentence-transformers numpy
```

## Utilisation

```bash
# Exécuter les 4 démos
python qbm.py --demo

# Assembler et exécuter un fichier .qbm
python qbm.py programme.qbm
```

## Tests

```bash
python -m unittest test_qbm -v
```

---

## Les 4 démos — 4 mythes cassés

| # | Démo | Mythe industriel cassé |
|---|---|---|
| 1 | Hello, Silicium ! | *Pas d'OS. Pas de runtime. Le silicium écoute directement.* |
| 2 | Addition baremetal | *42 + 58 = 100. Calculé dans 64 Ko. Pas besoin d'un datacenter.* |
| 3 | Transfert P2P | *Transaction effectuée. Sans banque. Sans API. Sans intermédiaire.* |
| 4 | Gouvernance sémantique | *Contenu filtré sans humain, sans LLM juge. 384 nombres. Un seuil. Fait.* |

📺 **[Voir la démo](demo/QBM.mp4)** (13 Mo)

---

## Langage d'assemblage QBM

```asm
; Hello World baremetal
MOV R0, @msg
MOV R1, #16
CALL CONSOLE_OUT
CALL HALT

msg:
    .ascii "Hello, Silicium!"
```

### Alias Human-Friendly

QBM comprend les alias pour les non-codeurs :
- `PRINT` → `CONSOLE_OUT`
- `HASH` → `HASH_SHA256`
- `SIMILARITY` → `COSINE_SIM`
- `STOP` → `HALT`
- `amount`, `limit`, `budget`, `score`… → `R0-R12`

---

## Gouvernance sémantique

```asm
CALL LOAD_MODEL           ; Charge MiniLM (80 Mo)
MOV R0, @candidate
CALL EMBED_TEXT           ; Embed le message candidat
MOV R0, @reference
CALL EMBED_TEXT           ; Embed la référence
CALL COSINE_SIM           ; Score 0-10000
CMP R0, #7000             ; Seuil de bienveillance
JMP 3, rejeter            ; < 7000 → rejeté
```

**Zone grise** : 6000-8000 → revue humaine obligatoire.
**Dérogation** : signée, publique, tracée dans l'Embassy Registry.

---

## Principes

1. **QBM fait une chose.** Rendre la confiance vérifiable. Pas tout faire — bien faire l'essentiel.

2. **QBM pilote, le host exécute.** Le modèle de 80 Mo ne peut pas tenir dans 64 Ko.
   Même principe que SHA-256 et ED25519 : le host fournit la capacité, QBM l'orchestre.

3. **Le seuil fixe est une feature, pas un bug.** Zone grise (6000-8000) → humain requis.
   Multi-références pour éviter les faux positifs.

4. **Séparation des pouvoirs.** Le LLM propose. Le silicium vérifie et juge.
   Aucun prompt ne contourne le bytecode.

5. **Au-delà des LLM.** QBM vérifie des actions, pas des tokens.
   Contrats, diagnostics, transactions, capteurs IoT, votes.
   Aucun LLM requis. Juste un contrat, du bytecode, et du courant.

---

## QBM V1 — Ce qui a été livré

- [x] VM v1.0 — 7 instructions baremetal
- [x] VM v1.1 — Intégration sémantique (MiniLM-L6-v2)
- [x] Assembleur QBM Human (alias français, registres nommés)
- [x] 4 démos intégrées (Hello World, Addition, P2P, Gouvernance)
- [x] Tests unitaires (`test_qbm.py`)
- [x] Documentation (BRIEF.md, README.md)
- [x] Repo public GitHub (`qbmcreator/qbm`)
- [x] Vidéo de démonstration (`demo/QBM.mp4`)

---

## Licence

MIT — Voir [LICENSE](LICENSE)

---

*« L'agentique symbiotique = humain (intention) + LLM (proposition) + QBM (vérification, jugement). »*
