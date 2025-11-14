// 2. Most powerful Pokémon
db.Pokemon.find({}, { _id: 0, name: 1}).sort({"stats.tot": -1}).limit(1)

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
      name: "$pokemon.name",
      wins: 1
    }
  }
]);