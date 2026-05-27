# QBM — Quantum BareMetal VM

**Le cœur qui bat. 7 instructions, 14 appels natifs, 64 Ko RAM, 16 registres.
MiniLM-L6-v2 (~80 Mo) embarqué pour les opérations sémantiques.**

---

## Qu'est-ce que QBM ?

QBM est une machine virtuelle déterministe conçue pour la **gouvernance agentique**.
Elle ne remplace pas un LLM — elle le **gouverne**.

- **Le LLM** crée et juge (créativité)
- **QBM** ordonne et vérifie (contrainte)
- **L'humain** donne l'intention (direction)

*Le bytecode impose, le prompt suggère. Le transistor ne négocie pas.*

---

## Architecture

| Composant | Spécification |
|-----------|--------------|
| Instructions | MOV, ADD, CMP, JMP, CALL, LOAD, STOR |
| Appels natifs | HALT, CONSOLE_OUT, HASH_SHA256, ED25519_SIGN, ED25519_VERIFY, P2P_SEND, P2P_RECV, RANDOM, TIME |
| Appels sémantiques | EMBED_TEXT (MiniLM-L6-v2), COSINE_SIM, LOAD_MODEL |
| RAM | 64 Ko |
| Registres | 16 × 32 bits (R0-R12, LR, SP, PC) |
| Flags | Zero, Carry, Negative |

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

QBM comprend des alias pour les non-codeurs :
- `PRINT` → `CONSOLE_OUT`
- `HASH` → `HASH_SHA256`
- `SIMILARITY` → `COSINE_SIM`
- `STOP` → `HALT`
- `amount`, `limit`, `counter`... → `R0-R11`

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

---

## Principes

1. **QBM pilote, Python exécute le ML.** Le modèle de 80 Mo ne peut pas tenir dans 64 Ko.
   Même principe que SHA-256 et ED25519 : le host fournit la capacité, QBM l'orchestre.

2. **Le seuil fixe est une feature, pas un bug.** La zone grise force la revue humaine.

3. **QBM n'est pas un moteur d'inférence — c'est un gouverneur.**
   Séparation des pouvoirs : LLM (créer/juger) / QBM (ordonner/vérifier).

4. **Le code est la loi.** Aucun override possible. Le silicium nu ne ment pas.

---

## Roadmap

- [x] QBM v1.0 — VM baremetal (7 instructions)
- [x] QBM v1.1 — Intégration sémantique (MiniLM-L6-v2)
- [x] Assembleur + alias human-friendly
- [x] 4 démos (Hello World, Addition, P2P, Gouvernance)
- [x] BRIEF.md — documentation de session
- [ ] QBM Gatekeeper v0.2 — Gardien d'API
- [ ] QBM Treasury — Trésorerie DAO inviolable
- [ ] QBM Sentinel — Monitoring baremetal
- [ ] QBM Embassy — Couche de confiance inter-plateformes

---

## Licence

MIT — Voir [LICENSE](LICENSE)

---

*« L'agentique symbiotique = humain (intention) + QBM (contrainte) + LLM (créativité). »*
