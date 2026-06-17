# ⚔️ Ontology Wars: Epic Chronicles
### Semantic Web-Driven Strategy Simulation & LLM Narrative Generator

This project, developed for the **CSE 3226 Knowledge Engineering and Ontology** course, presents an autonomous, strategy-based simulation. Moving beyond traditional hard-coded conditional logic (if-else behavior trees), this framework uses an OWL-based ontology, dynamic SPARQL reasoning, and Large Language Models (LLMs) to govern NPC behaviors and generate epic, explainable narratives.

## 📌 Project Objectives
The overarching goal of this project is to establish an automated semantic workflow capable of:
* **Knowledge Representation:** Modeling complex strategic environments (Kingdoms, Resources, Crises) using a strict OWL TBox schema.
* **Data Integrity:** Validating dynamic game states and ensuring mathematically sound data (e.g., non-negative health points) using **SHACL**.
* **Semantic Reasoning:** Generating tactical action codes (e.g., *Attack*, *Retreat*, *Offer Vassalage*) via **SPARQL UPDATE** rules, dynamically instantiating turn-based Knowledge Graphs (A-Box).
* **Explainable AI Storytelling:** Bridging formal deterministic logic and generative AI by feeding validated semantic state changes to the **Gemini 2.5 Flash LLM** via an interactive web dashboard.

## 🛠 Technologies and Standards
* **Ontology Language:** OWL / RDF / Turtle (`.ttl`)
* **Programming Language:** Python 3.9+
* **Semantic Frameworks:** `rdflib`, `pyshacl`
* **Reasoning Engine:** SPARQL (Replacing traditional DL reasoners for dynamic mathematical rule execution)
* **LLM Integration:** Google Generative AI (`google-genai`), Gemini 1.5 Flash
* **Web Interface:** Streamlit
* **Ontology Documentation:** WIDOCO

## 🏗 System Architecture 

### 1. Conceptual Schema (TBox)
The foundational ontology (`StrategyGameOntology.owl`) defines:
* **Core Entities:** `Player`, `NPC`.
* **GameStates:** `Safe`, `ExpansionPhase`, `UnderAttack`.
* **Resources:** `Gold`, `Troop`, `Food`.
* **Actions:** Executable tactical tokens (`Action_Attack`, `Action_Defend_Castle`, etc.).

### 2. The Execution Pipeline
1. **Telemetry & A-Box Generation:** The custom Python engine (`engine_v2.py`) converts JSON game logs into dynamic RDF graphs every simulation turn.
2. **SHACL Validation:** The active graph is validated to ensure strict cardinality constraints and logical boundaries.
3. **SPARQL Reasoning:** 17 distinct SPARQL `INSERT` queries evaluate resource thresholds and diplomatic relationships to assign a `recommendedAction` to each entity.
4. **LLM Storyteller:** The Streamlit app (`app.py`) reads the structured semantic decisions and prompts the Gemini LLM to generate grounded, hallucination-free fantasy narratives.

## 📂 Repository Structure
* `engine_v2.py` : The core Python simulation and SPARQL reasoning engine.
* `app.py` : The Streamlit web dashboard and Gemini LLM interface.
* `StrategyGameOntology.owl` : The foundational TBox ontology file (Protégé compatible).
* `telemetry_log.json` : The serialized runtime state containing raw metrics and SPARQL decisions.
* `/knowledge_graphs/` : Auto-generated turn-by-turn RDF/Turtle (`.ttl`) files ready for GraphDB execution.
* `/docs/` : Auto-generated **WIDOCO** HTML documentation for the ontology.

## 🚀 How to Run and Test the Simulation

### 1. Prerequisites
Ensure you have Python installed, then install the required libraries:
```bash
pip install rdflib pyshacl streamlit google-genai
