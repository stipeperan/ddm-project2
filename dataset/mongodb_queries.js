

// 4. Most winning Pokémon
db.Battle.aggregate([
    // Count wins per Pokémon ID
    {
        $group: {
            _id: "$participants.winner.pokemon_id",
            wins: { $sum: 1 }
        }
    },
    
    // Sort by number of wins
    { $sort: { wins: -1 } },
    
    // Keep only the top Pokémon
    { $limit: 1 },
    
    // Join with Pokemon collection to retrieve name
    {
        $lookup: {
            from: "Pokemon",
            localField: "_id",
            foreignField: "_id",
            as: "pokemon"
        }
    },
    
    // Flatten lookup result
    { $unwind: "$pokemon" },
    
    // Final clean output: ONLY the name and wins
    {
        $project: {
            _id: 0,
            pokemon_name: "$pokemon.name",
            wins: 1
        }
    }
]);

// 12. Most powerful Pokémon (by total)
db.Pokemon.aggregate([
  { $project: { _id: 0, name: 1, tot: "$stats.tot" }},
  { $sort: { tot: -1 }},
  { $limit: 1 }
]);

// 13. Most powerful Pokémon (by type)
db.Pokemon.aggregate([
  // break out each type
  { $unwind: "$types" },

  // sort so $first selects the strongest per type
  { $sort: { "stats.tot": -1 }},

  // group by type ID
  {
    $group: {
      _id: "$types",
      pokemon: { $first: "$name" },
      total:   { $first: "$stats.tot" }
    }
  },

  // lookup type name
  {
    $lookup: {
      from: "Type",
      localField: "_id",
      foreignField: "_id",
      as: "typeInfo"
    }
  },

  { $unwind: "$typeInfo" },

  // final clean output
  {
    $project: {
      _id: 0,
      type: "$typeInfo.name",
      pokemon: 1,
      total: 1
    }
  },

  { $sort: { type: 1 } }
]);