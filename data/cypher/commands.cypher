// ================
// 1. Add a Pokémon
// ================
:param pokemon => {number:'9999', name:"Mariukachu", total:377, type:'Normal'};

// Test before
MATCH (p:Pokemon {id: $pokemon.id})
RETURN p;

// Command
CREATE (:Pokemon {
  number: $pokemon.number,
  name:   $pokemon.name,
  total:  toInteger($pokemon.total),
  type:   $pokemon.type
});

// test after
MATCH (p:Pokemon {number: $pokemon.number})
RETURN p;

// ==========================================
// 2. Move a Pokémon from one trainer to another
// ==========================================
:param pokemon_id => 119;
:param to_trainer_id => 408;

// Test before
MATCH (p:Pokemon {id: $pokemon_id})
OPTIONAL MATCH (a:Trainer)-[ow:OWNS]->(p)
RETURN p, a, ow;

// command
MATCH (p:Pokemon)
WHERE p.id = toInteger($pokemon_id) OR p.id = $pokemon_id
OPTIONAL MATCH (:Trainer)-[r:OWNS]->(p)
DELETE r
WITH p
MERGE (to:Trainer {trainerID: $to_trainer_id})
MERGE (to)-[:OWNS]->(p);

// Test after
MATCH (p:Pokemon {id: $pokemon_id})
OPTIONAL MATCH (a:Trainer)-[ow:OWNS]->(p)
RETURN p, a, ow;

// ================================================================
// 3. Remove a “middle” evolution and connect base ev. to final ev.
// ================================================================
:param mid_id => 2;

// test before
MATCH (base:Pokemon)-[r1:EVOLVES_TO]->(mid:Pokemon {id: $mid_id})-[r2:EVOLVES_TO]->(final:Pokemon)
RETURN base, r1, mid, r2, final;

// command
MATCH (base:Pokemon)-[r1:EVOLVES_TO]->(mid:Pokemon {id: $mid_id})-[r2:EVOLVES_TO]->(final:Pokemon)
MERGE (base)-[:EVOLVES_TO]->(final)
WITH DISTINCT mid
DETACH DELETE mid;

// test after
MATCH (a:Pokemon)-[r:EVOLVES_TO]->(b:Pokemon)
WHERE NOT EXISTS { MATCH (a)-[:EVOLVES_TO]->(:Pokemon {id: $mid_id}) }
AND   NOT EXISTS { MATCH (:Pokemon {id: $mid_id}) }
RETURN a, r, b;

// =========================================================================
// 4. Remove the gym leader with the lowest win ratio and delete the trainer
// =========================================================================

// test before
MATCH (t:Trainer)-[r:LEADS]->(g:Gym)
OPTIONAL MATCH (b:Battle)
WHERE (b.gym_id = g.gym_id)
WITH t, r, g,
     count(b) AS total,
     sum(CASE WHEN (b.trainer_winner_id = t.trainerID)
              THEN 1 ELSE 0 END) AS wins
WITH t, r, g, wins, total,
     CASE WHEN total = 0 THEN 0.0 ELSE 1.0 * wins / total END AS ratio
RETURN t, r, g, ratio, wins, total
ORDER BY ratio ASC, total ASC
LIMIT 5;

// command
// pick the worst leader
MATCH (t:Trainer)-[r:LEADS]->(g:Gym)
OPTIONAL MATCH (b:Battle)
WHERE (b.gym_id = g.gym_id)
WITH t, r, g,
     count(b) AS total,
     sum(CASE WHEN (b.trainer_winner_id = t.trainerID)
              THEN 1 ELSE 0 END) AS wins
WITH t, r, g, wins, total,
     CASE WHEN total = 0 THEN 0.0 ELSE 1.0 * wins / total END AS ratio
ORDER BY ratio ASC, total ASC
LIMIT 1

// delete both kinds of outgoing relationships from this trainer
OPTIONAL MATCH (t)-[rel:LEADS|OWNS]->()
DELETE rel

// then remove the trainer node
DETACH DELETE t;

// test after
// Show gyms with no leader (ownerless), so you see the “gap” on the graph
MATCH (g:Gym)
WHERE NOT EXISTS { MATCH (:Trainer)-[:LEADS]->(g) }
RETURN g;

// ==================================================================================
// 5. Create Mario (dynamic id), give up to two strongest free Pokémon,
//    and assign him to an ownerless gym from the previous step
// ==================================================================================

// test before
OPTIONAL MATCH (mar:Trainer {trainername: 'New Trainer'})
OPTIONAL MATCH (mar)-[ow:OWNS]->(p:Pokemon)
OPTIONAL MATCH (mar)-[ld:LEADS]->(g:Gym)
RETURN mar, ow, p, ld, g;

// command

// 1) Compute a new trainer id dynamically and create Mario
CALL {
  MATCH (t:Trainer)
  RETURN coalesce(max(t.trainerID), 0) + 1 AS next_id
}
WITH next_id
MERGE (mar:Trainer {trainerID: next_id})
  ON CREATE SET mar.trainername = 'New Trainer'

// 2) Pick up to two strongest free Pokémon (no owner)
//    NOTE: if fewer than two exist, we still proceed with what's available.
WITH mar
MATCH (p:Pokemon)
WHERE NOT EXISTS { MATCH (:Trainer)-[:OWNS]->(p) }
WITH mar, p
ORDER BY p.total DESC, p.id ASC
WITH mar, collect(p)[0..2] AS picks

UNWIND picks AS pick
MERGE (mar)-[:OWNS]->(pick)

// 3) Claim an ownerless gym (one that lost its leader previously)
//    If none exists, this step does nothing.
WITH mar
OPTIONAL MATCH (g:Gym)
WHERE NOT EXISTS { MATCH (:Trainer)-[:LEADS]->(g) }
WITH mar, g
ORDER BY g.gym_id ASC
LIMIT 1
WITH mar, g
WHERE g IS NOT NULL
MERGE (mar)-[:LEADS]->(g);

// test after
MATCH (mar:Trainer {trainername: 'New Trainer'})
OPTIONAL MATCH (mar)-[ow:OWNS]->(p:Pokemon)
OPTIONAL MATCH (p)-[ht:HAS_TYPE]->(ty:Type)
OPTIONAL MATCH (mar)-[ld:LEADS]->(g:Gym)
RETURN mar, ow, p, ht, ty, ld, g;