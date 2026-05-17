# Design Decisions & Ontology Axioms

This document outlines the logical constraints, modeling choices, and Description Logic axioms implemented within the Strategy Game Ontology to ensure semantic consistency and enable automated tactical reasoning.

## 1. Structural Axioms & Restrictions

### Decision: Strict Domain and Range Binding
- **Constraint:** `hasState` Domain: `Entity`, Range: `GameState`
- **Rationale:** Prevents semantic pollution. An `Action` or a `Resource` cannot possess a "State". Only an active actor (`Entity`) can experience game phases like `UnderAttack` or `ResourceCritical`.

### Decision: Symmetric Diplomatic Relations
- **Constraint:** `isAlliedWith` defined as a **Symmetric Property**.
- **Rationale:** If Kingdom A is allied with Kingdom B, the reasoning engine must automatically infer that Kingdom B is allied with Kingdom A. This eliminates the need for bidirectional data entry in the game loop.

## 2. Data Integrity Constraints

### Decision: Integer Typing for Dynamic Metrics
- **Constraint:** `resourceAmount`, `threatLevel`, and `healthPoints` strictly bound to `xsd:integer`.
- **Rationale:** Ensuring metrics are parsed as integers allows SPARQL queries and DL rules to perform mathematical evaluations (e.g., `< 20`, `>= 8`) critical for threshold-based crisis detection.

### Decision: Disjoint Categorization
- **Constraint:** `Action`, `GameState`, `Resource`, and `Entity` are defined as mutually **Disjoint Classes**.
- **Rationale:** A conceptual safeguard preventing the game engine's data binder from accidentally classifying a 'Defend' token as a 'Resource'.

## 3. Automated Reasoning Logic

### Decision: Dynamic State Classification
- **Description:** Implementation of threshold-based equivalent classes for automated crisis detection.
- **Example DL Axiom:** `CriticalThreatState ≡ GameState and (threatLevel some integer[>= 8])`
- **Rationale:** The system does not need a hard-coded script to flag a crisis. If an entity's state registers a threat level of 8 or higher, the HermiT reasoner instantly classifies it as a `CriticalThreatState`, which subsequently triggers emergency `recommendedAction` properties.
