import json
import os
import random
import copy
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD
try:
    from pyshacl import validate
    SHACL_AVAILABLE = True
except ImportError:
    SHACL_AVAILABLE = False
    print("WARNING: pyshacl not installed. Run 'pip install pyshacl' for validation.")

# Logging & Directories
LOG_FILE = "telemetry_log.json"
KG_DIR = "knowledge_graphs"
os.makedirs(KG_DIR, exist_ok=True)

# Namespace
GAME = Namespace("http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#")

# ==============================================================================
# SHACL VALIDATION SCHEMA
# ==============================================================================
SHACL_SHAPES = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

game:EntityShape a sh:NodeShape ;
    sh:targetClass game:Entity ;
    sh:property [
        sh:path game:healthPoints ;
        sh:datatype xsd:integer ;
        sh:minInclusive 0 ;
        sh:message "Health Points cannot drop below 0!" ;
    ] ;
    sh:property [
        sh:path game:hasState ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Each kingdom must have exactly 1 GameState!" ;
    ] .
"""

def create_initial_world():
    print("--- CREATING NEW WORLD (TURN 1) ---")
    entities = [
        {"id": "Player_Kingdom", "type": "Player", "healthPoints": 100, "gold": 50, "food": 50, "troop": 30, "threatLevel": 2, "allies": [], "vassalOf": "", "target": "", "isEliminated": False},
        {"id": "Kingdom_Avalon", "type": "NPC", "healthPoints": 100, "gold": 45, "food": 60, "troop": 25, "threatLevel": 3, "allies": [], "vassalOf": "", "target": "", "isEliminated": False},
        {"id": "Kingdom_OrcHorde", "type": "NPC", "healthPoints": 100, "gold": 20, "food": 30, "troop": 50, "threatLevel": 5, "allies": [], "vassalOf": "", "target": "", "isEliminated": False},
        {"id": "Kingdom_ElvenForest", "type": "NPC", "healthPoints": 100, "gold": 60, "food": 40, "troop": 20, "threatLevel": 2, "allies": [], "vassalOf": "", "target": "", "isEliminated": False}
    ]
    return {"turn": 1, "entities": entities}

def initialize_game_state():
    if not os.path.exists(LOG_FILE):
        initial_state = [create_initial_world()]
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_state, f, indent=4, ensure_ascii=False)
        return initial_state, initial_state[0]
    else:
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                all_turns = json.load(f)
                return all_turns, all_turns[-1]
        except:
            initial_state = [create_initial_world()]
            return initial_state, initial_state[0]

def build_knowledge_graph(alive_entities):
    """ Builds the Knowledge Graph by combining T-Box (OWL) and A-Box (JSON data). """
    g = Graph()
    
    # 1. Load T-Box (Ontology Schema)
    try:
        g.parse("StrategyGameOntology.owl", format="xml")
        print("-> T-Box (Ontology Schema) loaded successfully from OWL file.")
    except Exception as e:
        print(f"-> WARNING: Could not load OWL file. Proceeding with empty schema. Error: {e}")

    g.bind("game", GAME)
    
    # 2. Construct A-Box from dynamic JSON data
    for e in alive_entities:
        e_uri = GAME[e["id"]]
        
        # Basic Classification
        g.add((e_uri, RDF.type, GAME.Entity))
        g.add((e_uri, RDF.type, GAME.Player if e["type"] == "Player" else GAME.NPC))
        
        # Data Properties (Forced XSD Integer)
        g.add((e_uri, GAME.healthPoints, Literal(int(e["healthPoints"]), datatype=XSD.integer)))
        
        # State Assignment
        state_uri = GAME[f"State_{e['id']}"]
        g.add((e_uri, GAME.hasState, state_uri))
        
        threat = int(e["threatLevel"])
        g.add((state_uri, GAME.threatLevel, Literal(threat, datatype=XSD.integer)))
        
        if threat <= 3:
            g.add((state_uri, RDF.type, GAME.Safe))
        elif 4 <= threat <= 7:
            g.add((state_uri, RDF.type, GAME.ExpansionPhase))
        else:
            g.add((state_uri, RDF.type, GAME.UnderAttack))
            
        # Resource Objects
        gold_uri = GAME[f"Gold_{e['id']}"]
        g.add((gold_uri, RDF.type, GAME.Gold))
        g.add((gold_uri, GAME.resourceAmount, Literal(int(e["gold"]), datatype=XSD.integer)))
        g.add((e_uri, GAME.hasResource, gold_uri))
        
        food_uri = GAME[f"Food_{e['id']}"]
        g.add((food_uri, RDF.type, GAME.Food))
        g.add((food_uri, GAME.resourceAmount, Literal(int(e["food"]), datatype=XSD.integer)))
        g.add((e_uri, GAME.hasResource, food_uri))
        
        troop_uri = GAME[f"Troop_{e['id']}"]
        g.add((troop_uri, RDF.type, GAME.Troop))
        g.add((troop_uri, GAME.resourceAmount, Literal(int(e["troop"]), datatype=XSD.integer)))
        g.add((e_uri, GAME.hasResource, troop_uri))

        # Object Properties (Relationships)
        for ally in e["allies"]:
            g.add((e_uri, GAME.isAlliedWith, GAME[ally]))
            
        if e["vassalOf"]:
            g.add((e_uri, GAME.isVassalOf, GAME[e["vassalOf"]]))

    return g

def execute_sparql_rules(g):
    """ Executes SPARQL UPDATE queries equivalent to the original SWRL rules. """
    
    sparql_queries = [
        # S1: Defensive Instinct
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e game:recommendedAction game:Action_Defend_Castle }
            WHERE { ?e a game:Entity ; game:hasState ?s . ?s a game:UnderAttack . } """,
            
        # S2: Counter-Attack Opportunity (Troop >= 40)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e game:recommendedAction game:Action_Attack }
            WHERE { ?e game:hasState ?s . ?s a game:UnderAttack . ?e game:hasResource ?r . ?r a game:Troop ; game:resourceAmount ?amt . FILTER(?amt >= 40) } """,
            
        # S3: Economic Crisis & Retreat (Food <= 20)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e game:recommendedAction game:Action_Retreat }
            WHERE { ?e game:hasState ?s . ?s a game:UnderAttack . ?e game:hasResource ?r . ?r a game:Food ; game:resourceAmount ?amt . FILTER(?amt <= 20) } """,
            
        # S4: Peacetime Investment (Gold >= 40)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e game:recommendedAction game:Action_BuildTroop }
            WHERE { ?e game:hasState ?s . ?s a game:Safe . ?e game:hasResource ?r . ?r a game:Gold ; game:resourceAmount ?amt . FILTER(?amt >= 40) } """,
            
        # S5: Poverty & Recovery (Gold <= 15)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e game:recommendedAction game:Action_GatherResource }
            WHERE { ?e game:hasResource ?r . ?r a game:Gold ; game:resourceAmount ?amt . FILTER(?amt <= 15) } """,
            
        # S6: Expansion Phase Strategy (Food >= 20)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e game:recommendedAction game:Action_Attack }
            WHERE { ?e game:hasState ?s . ?s a game:ExpansionPhase . ?e game:hasResource ?r . ?r a game:Food ; game:resourceAmount ?amt . FILTER(?amt >= 20) } """,
            
        # S7: Request Urgent Aid
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_RequestAid . ?e1 game:requestsAidFrom ?e2 }
            WHERE { ?e1 game:hasState ?s . ?s a game:UnderAttack . ?e1 game:isAlliedWith ?e2 . } """,
            
        # S8: Accept Aid (Abundance) (Gold >= 40)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_AcceptAid }
            WHERE { ?e2 game:requestsAidFrom ?e1 . ?e1 game:hasState ?s . ?s a game:Safe . ?e1 game:hasResource ?r . ?r a game:Gold ; game:resourceAmount ?amt . FILTER(?amt >= 40) } """,
            
        # S9: Reject Aid (Self-Preservation) (Gold <= 20)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_RejectAid }
            WHERE { ?e2 game:requestsAidFrom ?e1 . ?e1 game:hasResource ?r . ?r a game:Gold ; game:resourceAmount ?amt . FILTER(?amt <= 20) } """,
            
        # S10: Submit Before Collapse (HP <= 15)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_OfferVassalage . ?e1 game:offersVassalageTo ?e2 }
            WHERE { ?e1 game:hasState ?s1 . ?s1 a game:UnderAttack . ?e1 game:healthPoints ?hp . FILTER(?hp <= 15) . ?e2 a game:Entity ; game:hasState ?s2 . ?s2 a game:Safe . } """,

        # S11: Opportunistic Betrayal (Troop >= 60)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_BreakAlliance . ?e1 game:hasTarget ?e2 }
            WHERE { ?e1 game:hasState ?s1 . ?s1 a game:ExpansionPhase . ?e1 game:hasResource ?r . ?r a game:Troop ; game:resourceAmount ?amt . FILTER(?amt >= 60) . ?e1 game:isAlliedWith ?e2 . ?e2 game:hasState ?s2 . ?s2 a game:UnderAttack . } """,

        # S12: Pact of the Strong
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_OfferAlliance . ?e1 game:offersAllianceTo ?e2 }
            WHERE { ?e1 game:hasState ?s1 . ?s1 a game:Safe . ?e2 game:hasState ?s2 . ?s2 a game:Safe . FILTER(?e1 != ?e2) } """,

        # S13: Accept Vassalage Offer
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_AcceptVassalage }
            WHERE { ?e2 game:offersVassalageTo ?e1 . ?e1 game:hasState ?s . ?s a game:Safe . } """,

        # S14: Exploit Vassal Resources (Gold >= 50)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_BuildTroop }
            WHERE { ?e1 game:hasState ?s1 . ?s1 a game:Safe . ?e2 game:isVassalOf ?e1 . ?e2 game:hasResource ?r . ?r a game:Gold ; game:resourceAmount ?amt . FILTER(?amt >= 50) } """,

        # S15: Reject Vassalage Offer (HP >= 50)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_RejectVassalage }
            WHERE { ?e2 game:offersVassalageTo ?e1 . ?e1 game:hasState ?s . ?s a game:Safe . ?e1 game:healthPoints ?hp . FILTER(?hp >= 50) } """,

        # S16: Accept Alliance (Troop >= 40)
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_AcceptAlliance }
            WHERE { ?e2 game:offersAllianceTo ?e1 . ?e2 game:hasResource ?r . ?r a game:Troop ; game:resourceAmount ?amt . FILTER(?amt >= 40) } """,

        # S17: Reject Alliance
        """ PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
            INSERT { ?e1 game:recommendedAction game:Action_RejectAlliance }
            WHERE { ?e2 game:offersAllianceTo ?e1 . ?e1 game:hasState ?s . ?s a game:ExpansionPhase . } """
    ]

    for q in sparql_queries:
        g.update(q)
    return g

def consult_ontology(alive_entities, turn_num):
    print("\n--- STEP 2: RDFLIB & SPARQL REASONING ---")
    
    # 1. Build Graph
    g = build_knowledge_graph(alive_entities)
    
    # 2. SHACL Validation
    if SHACL_AVAILABLE:
        print("-> Running SHACL Validation...")
        shacl_g = Graph().parse(data=SHACL_SHAPES, format="turtle")
        conforms, results_graph, results_text = validate(g, shacl_graph=shacl_g, inference='rdfs')
        if not conforms:
            print("!!! SHACL VALIDATION FAILED !!!")
            print(results_text)
        else:
            print("-> SHACL Validation Passed. Knowledge Graph is consistent.")

    # 3. Execute SPARQL Rules
    print("-> Executing SPARQL Rules (SWRL Equivalent)...")
    g = execute_sparql_rules(g)
    
    # 4. Export Turtle File
    ttl_file = os.path.join(KG_DIR, f"turn_{turn_num}.ttl")
    g.serialize(destination=ttl_file, format="turtle")
    print(f"-> Turn KG exported to {ttl_file}")

    # 5. Extract Decisions
    query_results = g.query("""
        PREFIX game: <http://www.semanticweb.org/cse3226/strategy-game-ontology/v2#>
        SELECT ?entity ?action
        WHERE { ?entity game:recommendedAction ?action }
    """)

    action_pool = {}
    for row in query_results:
        e_id = str(row.entity).split("#")[-1]
        action = str(row.action).split("#")[-1] 
        if e_id not in action_pool:
            action_pool[e_id] = []
        action_pool[e_id].append(action)

    print("\n--- COMMANDER DECISIONS ---")
    chosen_actions = {}
    for e in alive_entities:
        e_id = e["id"]
        if e_id in action_pool and action_pool[e_id]:
            
            # DIPLOMACY PRIORITIZATION (If there are Alliance or Vassalage, choose 100%)
            diplomacy_actions = [a for a in action_pool[e_id] if "Alliance" in a or "Vassalage" in a]
            
            if diplomacy_actions:
                chosen = random.choice(diplomacy_actions) # Offer or Accept
            else:
                chosen = random.choice(action_pool[e_id]) # Otherwise

            chosen_actions[e_id] = chosen
            print(f"[{e_id}] -> SPARQL FIRED: {chosen}")
        else:
            chosen_actions[e_id] = "Action_GatherResource"
            print(f"[{e_id}] -> No Rules Matched. Default: Action_GatherResource")

    return chosen_actions

def resolve_actions(alive_entities, decisions):
    print("\n--- STEP 3: ACTION RESOLUTION (GAME PHYSICS & DIPLOMACY) ---")
    
    def get_entity_by_id(target_id):
        for entity in alive_entities:
            if entity["id"] == target_id: return entity
        return None

    entities_by_power = sorted(alive_entities, key=lambda x: x["troop"])

    for e_id, action in decisions.items():
        entity = get_entity_by_id(e_id)
        if not entity or entity["isEliminated"]: continue
            
        print(f"\n[{e_id}] is executing: {action}")

        if action == "Action_GatherResource":
            gathered_gold = random.randint(10, 25)
            gathered_food = random.randint(15, 40)
            entity["gold"] += gathered_gold
            entity["food"] += gathered_food
            print(f"  -> Harvested {gathered_gold} Gold and {gathered_food} Food.")

        elif action == "Action_BuildTroop":
            # GÜNCELLEME 1: S14 Kuralı - Overlord her zaman önce Vassal'ını sömürür!
            for potential_vassal in alive_entities:
                if potential_vassal["vassalOf"] == e_id and potential_vassal["gold"] >= 30:
                    stolen_gold = 25
                    potential_vassal["gold"] -= stolen_gold
                    entity["gold"] += stolen_gold
                    print(f"  -> OVERLORD EXPLOITATION: Extorted {stolen_gold} Gold from vassal {potential_vassal['id']} to fund the army!")
                    break # Her tur sadece 1 vassal sömürülür
                    
            max_troops_affordable = min(entity["gold"] // 2, entity["food"])
            if max_troops_affordable > 0:
                troops_to_build = random.randint(1, max_troops_affordable)
                entity["gold"] -= (troops_to_build * 2)
                entity["food"] -= (troops_to_build * 1)
                entity["troop"] += troops_to_build
                print(f"  -> Trained {troops_to_build} troops.")
            else:
                print("  -> Insufficient funds to build troops.")

        elif action == "Action_Attack":
            if entity["troop"] <= 0:
                print("  -> Army is completely depleted! Cannot launch an attack.")
                continue

            valid_targets = [e for e in entities_by_power if e["id"] != e_id and e["id"] not in entity["allies"] and entity["vassalOf"] != e["id"]]
            if not valid_targets:
                print("  -> No valid targets available for attack. Standing down.")
                continue
                
            target_entity = valid_targets[0]
            target_id = target_entity["id"]
            print(f"  -> WAR DECLARED! Selected weakest target: {target_id}")
            
            entity["threatLevel"] = min(10, entity["threatLevel"] + 2)
            target_entity["threatLevel"] = max(8, min(10, target_entity["threatLevel"] + 3))
            
            # GÜNCELLEME 2: Hedef "Retreat" kararı aldıysa, saldıran taraf yağma yapar
            if decisions.get(target_id) == "Action_Retreat":
                loot = int(target_entity["gold"] * 0.25) # Hedefin altınının %25'i çalınır
                entity["gold"] += loot
                target_entity["gold"] -= loot
                print(f"  -> ENEMY RETREATED! Pillaged {loot} Gold from {target_id}'s abandoned lands.")
                continue

            total_troops = entity["troop"] + target_entity["troop"]
            if total_troops == 0: continue
                
            win_chance = (entity["troop"] / total_troops) * 100
            if random.uniform(0, 100) <= win_chance:
                print(f"  -> BATTLE WON! Plundered {target_id}.")
                entity["troop"] = max(0, int(entity["troop"] * 0.8)) 
                loot = int(target_entity["gold"] * 0.4) 
                entity["gold"] += loot
                target_entity["gold"] -= loot
                target_entity["troop"] = max(0, int(target_entity["troop"] * 0.5)) 
                target_entity["healthPoints"] -= random.randint(15, 30)
            else:
                print(f"  -> BATTLE LOST! Heavy casualties.")
                entity["troop"] = max(0, int(entity["troop"] * 0.5)) 
                target_entity["troop"] = max(0, int(target_entity["troop"] * 0.8)) 

        elif action == "Action_Defend_Castle":
            militia = int(entity["troop"] * 0.15)
            if militia == 0: 
                militia = 5 # Eğer ordu sıfırsa çaresizce 5 köylü silahlandırılır.
            entity["troop"] += militia
            entity["threatLevel"] = max(0, entity["threatLevel"] - 1)
            print(f"  -> Fortified walls! Raised {militia} militia troops.")

        elif action == "Action_Retreat":
            lost_troops = int(entity["troop"] * 0.1)
            entity["troop"] -= lost_troops
            entity["threatLevel"] = max(2, entity["threatLevel"] - 2) 
            print(f"  -> Retreated to save the core army. Lost {lost_troops} troops in the chaos.")

        elif action == "Action_OfferAlliance":
            print("  -> Sent diplomatic envoys to propose an alliance. Waiting for response...")

        elif action == "Action_AcceptAlliance":
            offerors = [o_id for o_id, act in decisions.items() if act == "Action_OfferAlliance" and o_id != e_id]
            if offerors:
                target_id = offerors[0] 
                target_entity = get_entity_by_id(target_id)
                if target_id not in entity["allies"]:
                    entity["allies"].append(target_id)
                    target_entity["allies"].append(e_id)
                    print(f"  -> ALLIANCE ACCEPTED! Officially formed a pact with {target_id}.")
            else:
                print("  -> Wanted to accept an alliance, but no valid offers were found.")

        elif action == "Action_RejectAlliance":
            print("  -> ALLIANCE REJECTED! We stand alone.")
            
        elif action == "Action_BreakAlliance":
            if entity["allies"]:
                ally_entities = [e for e in alive_entities if e["id"] in entity["allies"]]
                weakest_ally = sorted(ally_entities, key=lambda x: x["troop"])[0]
                entity["allies"].remove(weakest_ally["id"])
                weakest_ally["allies"].remove(e_id)
                entity["threatLevel"] = min(10, entity["threatLevel"] + 2)
                weakest_ally["threatLevel"] = min(10, weakest_ally["threatLevel"] + 2)
                print(f"  -> ALLIANCE BROKEN! Betrayed {weakest_ally['id']}.")
            else:
                print("  -> No alliances to break.")

        elif action == "Action_OfferVassalage":
            print("  -> Desperate times. Sent envoys begging for protection (Vassalage).")

        elif action == "Action_AcceptVassalage":
            beggars = [o_id for o_id, act in decisions.items() if act == "Action_OfferVassalage" and o_id != e_id]
            if beggars:
                target_id = beggars[0]
                target_entity = get_entity_by_id(target_id)
                target_entity["vassalOf"] = e_id
                target_entity["threatLevel"] = max(1, target_entity["threatLevel"] - 3) 
                print(f"  -> VASSALAGE ACCEPTED! {target_id} is now under our protection.")
            else:
                print("  -> Ready to accept vassals, but no one offered submission.")

        elif action == "Action_RejectVassalage":
            print("  -> VASSALAGE REJECTED! We don't protect the weak.")

        elif action == "Action_RequestAid":
            print("  -> Sent ravens to allies requesting urgent financial aid.")

        elif action == "Action_AcceptAid":
            requesters = [o_id for o_id, act in decisions.items() if act == "Action_RequestAid" and o_id in entity["allies"]]
            if requesters:
                target_id = requesters[0]
                target_entity = get_entity_by_id(target_id)
                if entity["gold"] >= 20:
                    entity["gold"] -= 20
                    target_entity["gold"] += 20
                    print(f"  -> AID SENT! Transferred 20 Gold to our ally {target_id}.")
                else:
                    print(f"  -> Tried to send aid to {target_id}, but we lack funds.")
            else:
                print("  -> Ready to send aid, but no ally requested it.")

        elif action == "Action_RejectAid":
            print("  -> AID REJECTED! We must prioritize our own survival.")

def perform_upkeep(alive_entities):
    print("\n--- STEP 4: END OF TURN MAINTENANCE (UPKEEP) ---")
    collapsed_ids = []

    for entity in alive_entities:
        e_id = entity["id"]
        
        # Original Geopolitical Decay Logic
        if entity["troop"] >= 40:
            entity["threatLevel"] = min(7, entity["threatLevel"] + 1)
        else:
            entity["threatLevel"] = max(0, entity["threatLevel"] - 1)
        
        if entity["troop"] > entity["food"]:
            starved_troops = entity["troop"] - entity["food"]
            entity["troop"] = entity["food"]  
            entity["food"] = 0
            entity["threatLevel"] = min(10, entity["threatLevel"] + 2) 
            entity["healthPoints"] = max(0, entity["healthPoints"] - 10)
            print(f"  -> [{e_id}] CRISIS: Famine! {starved_troops} troops starved. Health dropped due to riots.")
        else:
            entity["food"] -= entity["troop"]
            
        if entity["healthPoints"] <= 0:
            entity["healthPoints"] = 0
            entity["isEliminated"] = True
            collapsed_ids.append(e_id)
            print(f"  -> [{e_id}] COLLAPSED! The kingdom has fallen into ruins.")

    if collapsed_ids:
        print("\n  -> PROCESSING POST-COLLAPSE DIPLOMACY...")
        for entity in alive_entities:
            if entity["isEliminated"]:
                continue
            if entity["vassalOf"] in collapsed_ids:
                print(f"     * [{entity['id']}] is now FREE! Their overlord has fallen.")
                entity["vassalOf"] = ""
            original_ally_count = len(entity["allies"])
            entity["allies"] = [ally for ally in entity["allies"] if ally not in collapsed_ids]
            if len(entity["allies"]) < original_ally_count:
                print(f"     * [{entity['id']}] lost an ally due to collapse.")

def save_game_state(all_turns, new_turn):
    print("\n--- STEP 5: SAVING GAME STATE ---")
    all_turns.append(new_turn)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(all_turns, f, indent=4, ensure_ascii=False)
    turn_num = new_turn["turn"]
    print(f"  -> Turn {turn_num} successfully saved to {LOG_FILE}.")

def main(turns_to_play=1):
    for i in range(turns_to_play):
        print(f"\n{'='*40}")
        print(f"=== STARTING TURN EXECUTION ===")
        print(f"{'='*40}")
        
        all_turns, latest_turn = initialize_game_state()
        new_turn = copy.deepcopy(latest_turn)
        new_turn["turn"] += 1
        
        alive_entities = [entity for entity in new_turn["entities"] if not entity["isEliminated"]]
        if len(alive_entities) <= 1:
            print("\n=== GAME OVER! CONQUEST COMPLETE! ===")
            break

        decisions = consult_ontology(alive_entities, new_turn["turn"])
        resolve_actions(alive_entities, decisions)
        perform_upkeep(alive_entities)

        # ADDITION
        new_turn["sparql_decisions"] = decisions
        
        save_game_state(all_turns, new_turn)

if __name__ == "__main__":
    main(30)