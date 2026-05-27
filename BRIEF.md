# QBM — Brief de session
## 16-17 Mai 2026

---

## Etat du projet

**QBM (Quantum BareMetal VM)** — VM deterministe de gouvernance agentique.
7 instructions, 14 appels natifs, 64 Ko RAM, 16 registres.
MiniLM-L6-v2 (~80 Mo) embarque pour les operations semantiques.

## Ce qui a ete livre cette session

### QBM v1.1 — Integration semantique
- 3 nouveaux appels natifs :
  - `EMBED_TEXT` (0x0A) — Embedding via MiniLM-L6-v2 (384 float32)
  - `COSINE_SIM` (0x0B) — Similarite cosinus, score 0-10000
  - `LOAD_MODEL` (0x0C) — Prechargement lazy-load du modele
- Bugs corriges : indentation du fichier, syntaxe assembleur
- Skill qbm-constitution mis a jour avec spec complete v1.1
- 4 demos : Hello World, Addition, P2P, Gouvernance semantique

## Decisions architecturales cles

1. **QBM pilote, Python execute le ML.** Le modele de 80 Mo ne peut pas tenir dans 64 Ko.
   Meme principe que SHA-256 et ED25519 : le host fournit la capacite, QBM l'orchestre.

2. **Le seuil fixe est une feature, pas un bug.** Zone grise (6000-8000) → revue humaine.
   Multi-references pour eviter les faux positifs.

3. **QBM n'est pas un moteur d'inference ML — c'est un gouverneur.**
   Le LLM cree/juge, QBM ordonne/verifie. Separation des pouvoirs.

4. **Le code est la loi.** Aucun override possible.

## Concepts fondateurs

- Le bytecode impose, le prompt suggere. Le transistor ne negocie pas.
- La bienveillance est mesurable via similarite cosinus → seuil binaire.
- Le silicium nu ne ment pas : pas de couches d'abstraction entre CMP et le flag.
- L'agentique symbiotique = humain (intention) + QBM (contrainte) + LLM (creativite).

## 7 projets pour v0.2+
1. QBM Treasury — Tresorerie DAO inviolable
2. QBM Notary — Analyse de contrats par similarite semantique
3. QBM Gatekeeper — Gardien d'API (rate limiting, contenu, auth)
4. QBM Sentinel — Monitoring avec seuils dans le silicium
5. QBM Publisher — Chaine editoriale autonome
6. QBM Mediator — Arbitre entre agents IA concurrents
7. QBM Embassy — Couche de confiance inter-plateformes

**Priorite :** Gatekeeper → Sentinel → Embassy

## Prochaine session
- [ ] pip install sentence-transformers numpy
- [ ] python qbm.py --demo (execution complete avec MiniLM)
- [ ] Creation repo GitHub qbmcreator/qbm
- [ ] Push initial + tests unitaires
- [ ] Debut Gatekeeper v0.2
- [ ] Migration Linux (Ubuntu 24.04 LTS)
