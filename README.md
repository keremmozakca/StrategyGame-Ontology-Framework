# Ontology-Driven Tactical Recommendation System for Strategy Games .

This project, developed for the **CSE 3226 Knowledge Engineering and Ontology** course, presents a dynamic semantic reasoning framework designed to govern NPC behaviors and strategic decision-making in real-time strategy games. 

Moving beyond traditional hard-coded conditional logic (if-else behavior trees), this ontology serves as a machine-readable knowledge base that processes live game telemetry, evaluates kingdom states, and generates context-aware tactical recommendations.

## 📌 Project Objectives
The overarching goal of this ontology is to establish an automated semantic workflow capable of:
* Modeling complex strategic environments (Kingdoms, Resources, Crises).
* Evaluating dynamic game states using Description Logic rules.
* Generating tactical action codes (e.g., Defend, Gather Resource) based on live resource thresholds.
* Serving as the reasoning backbone for a future plug-and-play Unity NPC Framework integrated with LLMs for dynamic narrative generation.

## 🛠 Technologies and Standards
* **Ontology Language:** OWL (Web Ontology Language) / RDF/XML
* **Development Environment:** Protégé 5.5.0
* **Reasoning Engine:** HermiT
* **Documentation:** Widoco (HTML Generation)

## 🏗 Ontology Architecture (TBox)
The knowledge graph is structured around four foundational pillars:

### 1. Core Entities
* **Entity:** The primary actors, specialized into **Player** (human-controlled) and **NPC** (autonomous kingdoms/factions).
* **GameState:** Dynamic situational contexts such as **UnderAttack**, **ResourceCritical**, and **ExpansionPhase**.
* **Resource:** Economic and military assets like **Gold**, **Troop**, and **Food**.
* **Action:** Executable functional tokens like **Defend**, **Attack**, and **BuildTroop**.

### 2. Semantic Relationships (Object Properties)
* `hasState`: Binds an Entity to its current situational GameState.
* `hasResource`: Maps economic assets to specific Entities.
* `recommendedAction`: The critical output property derived by the reasoner, suggesting the optimal tactical move.
* `isAlliedWith`: A symmetric property defining diplomatic relationships.

### 3. Quantitative Metrics (Data Properties)
* `resourceAmount`: Integer tracking of economic strength.
* `threatLevel`: Integer (1-10) defining the severity of a GameState.
* `healthPoints`: Core vitality of an Entity.

## 📂 Repository Structure
* `/src`: Contains the primary ontology file (`StrategyGameOntology.owl`).
* `/docs`: Contains architectural design decisions (`design_decisions.md`) and auto-generated Widoco documentation.

## 🚀 How to Run and Test Reasoning
1. Download and install [Protégé](https://protege.stanford.edu/).
2. Open the `StrategyGameOntology.owl` file located in the `/src` directory.
3. Navigate to the **Individuals** tab to view the sample scenario (e.g., *Kingdom_Avalon* facing a *State_Under_Siege*).
4. Start the **HermiT Reasoner** (Reasoner > Start reasoner) to observe automated class and property inferences based on defined mathematical thresholds.
