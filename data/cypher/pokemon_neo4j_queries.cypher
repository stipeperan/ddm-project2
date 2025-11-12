
// =========================
// Pokémon Neo4j Query Pack
// =========================
// Description: Full set of analytical and aggregation queries for the Pokémon ER graph.
// Compatible with Neo4j Browser & Neo4j Desktop.
// -------------------------------------------

// For each trainer, their most successful Pokémon
MATCH (t:Trainer)-[:OWNS]->(p:Pokemon)
OPTIONAL MATCH (p)-[:WON]->(b:Battle)
WITH t, p, count(b) AS wins
ORDER BY t.trainername, wins DESC
WITH t, collect({pokemon:p, wins:wins}) AS ranked
RETURN t.name AS trainer, ranked[0].pokemon.pokename AS pokemon, ranked[0].wins AS wins;

// For each trainer, the gym where they won the most battles
MATCH (t:Trainer)-[:WON]->(b:Battle)<-[:HOSTS]-(g:Gym)
WITH t, g, count(b) AS wins
ORDER BY t.trainername, wins DESC
WITH t, collect({gym:g, wins:wins}) AS ranked
RETURN t.trainername AS trainer, ranked[0].gym.gymname AS gym, ranked[0].wins AS wins;

// Most winning trainer
MATCH (t:Trainer)-[:WON]->(b:Battle)
WITH t, count(b) AS wins
ORDER BY wins DESC
RETURN t.trainername AS trainer, wins
LIMIT 1;

// Most winning Pokémon
MATCH (p:Pokemon)-[:WON]->(b:Battle)
WITH p, count(b) AS wins
ORDER BY wins DESC
RETURN p.pokename AS pokemon, wins
LIMIT 1;

// Most winning trainer
MATCH (t:Trainer)-[:WON]->(b:Battle)
WITH t, count(b) AS wins
RETURN 'trainer' AS kind, t.trainername AS name, wins
  ORDER BY wins DESC
  LIMIT 1

UNION ALL

// Most winning Pokémon
MATCH (p:Pokemon)-[:WON]->(b:Battle)
WITH p, count(b) AS wins
RETURN 'pokemon' AS kind, p.pokename AS name, wins
  ORDER BY wins DESC
  LIMIT 1;

// Wins for each Pokémon and its evolutions (sum)
MATCH (p:Pokemon)
OPTIONAL MATCH (p)-[:EVOLVES_TO*0..]->(evo:Pokemon)
OPTIONAL MATCH (evo)-[:WON]->(b:Battle)
WITH p, count(DISTINCT b) AS wins_in_chain
ORDER BY wins_in_chain DESC, p.pokename
RETURN p.pokename AS rootPokemon, wins_in_chain;

// Gym that hosted the highest number of battles
MATCH (g:Gym)-[:HOSTS]->(b:Battle)
WITH g, count(b) AS hosted
ORDER BY hosted DESC
RETURN g.gym_name AS gym, hosted
LIMIT 1;

// For each gym, total number of distinct Pokémon that fought there
MATCH (g:Gym)-[:HOSTS]->(b:Battle)<-[:FIGHTS_IN]-(p:Pokemon)
WITH g, count(DISTINCT p) AS fighters
ORDER BY fighters DESC
RETURN g.gym_name AS gym, fighters;

// Pokémon that fought in the most different gyms
MATCH (p:Pokemon)-[:FIGHTS_IN]->(b:Battle)<-[:HOSTS]-(g:Gym)
WITH p, count(DISTINCT g) AS gymCount
ORDER BY gymCount DESC
RETURN p.pokename AS pokemon, gymCount
LIMIT 10;

// Pokémon type with the best winning ratio
MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type)
OPTIONAL MATCH (p)-[:FIGHTS_IN]->(bf:Battle)
OPTIONAL MATCH (p)-[:WON]->(bw:Battle)
WITH t,
     count(DISTINCT bf) AS fights,
     count(DISTINCT bw) AS wins
WHERE fights > 0
WITH t, wins*1.0 / fights AS winRatio, wins, fights
ORDER BY winRatio DESC
RETURN t.name AS type, round(winRatio,3) AS winRatio, wins, fights
LIMIT 5;

// Number of Pokémon that are at maximum evolution
MATCH (p:Pokemon)
WHERE NOT (p)-[:EVOLVES_TO]->()
RETURN count(p) AS numMaxEvolution;

// Most powerful Pokémon (by total)
MATCH (p:Pokemon)
WITH p, coalesce(p.total,
                 p.hp + p.attack + p.defense + p.specialAttack + p.specialDefense + p.speed) AS totalScore
ORDER BY totalScore DESC
RETURN p.pokename AS pokemon, totalScore
LIMIT 10;

// Most powerful Pokémon for each type
MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type)
WITH t, p, coalesce(p.total,
                    p.hp + p.attack + p.defense + p.specialAttack + p.specialDefense + p.speed) AS totalScore
ORDER BY t.name, totalScore DESC
WITH t, collect({pokemon:p.pokename, total:totalScore}) AS ranked
RETURN t.name AS type, ranked[0].pokemon AS pokemon, ranked[0].total AS total;

// Group all Pokémon of type [Water]
MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type {name:'Water'})
RETURN p.pokename AS pokemon
ORDER BY pokemon;

//// Show gyms and their type specialization
//MATCH (g:Gym)-[:SPECIALIZES_IN]->(t:Type)
//RETURN g.gym_name AS gym, t.name AS specializesIn
//ORDER BY gym, specializesIn;

// Highest improvement (Total) from base → max evolution
MATCH (p:Pokemon)
WITH p, coalesce(p.total,
                 p.hp + p.attack + p.defense + p.specialAttack + p.specialDefense + p.speed) AS totalScore
SET p._totalScore = totalScore;

MATCH (base:Pokemon)
WHERE NOT ()-[:EVOLVES_TO]->(base)
WITH base, base._totalScore AS baseTotal
OPTIONAL MATCH (base)-[:EVOLVES_TO*0..]->(desc:Pokemon)
WITH base, baseTotal, max(desc._totalScore) AS maxDescTotal
WITH base, baseTotal, maxDescTotal, (maxDescTotal - baseTotal) AS improvement
ORDER BY improvement DESC
RETURN base.pokename AS basePokemon, baseTotal, maxDescTotal, improvement
LIMIT 20;
