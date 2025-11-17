// ======================================
// Pokémon MongoDB Query Pack (PokemonDB)
// ======================================
// Collections: Pokemon, Trainer, Type, Gym, Battle
// --------------------------------------

// 1. For each trainer, their most successful Pokémon
db.Battle.aggregate([
  {
    $group: {
      _id: {
        trainer_id: "$participants.winner.trainer_id",
        pokemon_id: "$participants.winner.pokemon_id"
      },
      wins: { $sum: 1 }
    }
  },
  { $sort: { "_id.trainer_id": 1, wins: -1 } },
  {
    $group: {
      _id: "$_id.trainer_id",
      top: { $first: { pokemon_id: "$_id.pokemon_id", wins: "$wins" } }
    }
  },
  {
    $lookup: {
      from: "Trainer",
      localField: "_id",
      foreignField: "_id",
      as: "trainer"
    }
  },
  { $unwind: "$trainer" },
  {
    $lookup: {
      from: "Pokemon",
      localField: "top.pokemon_id",
      foreignField: "_id",
      as: "pokemon"
    }
  },
  { $unwind: "$pokemon" },
  {
    $project: {
      _id: 0,
      trainer: "$trainer.name",
      pokemon: "$pokemon.name",
      wins: "$top.wins"
    }
  },
  { $sort: { trainer: 1 } }
]);

// 2. For each trainer, the gym where they won the most battles
db.Battle.aggregate([
  {
    $group: {
      _id: {
        trainer_id: "$participants.winner.trainer_id",
        gym_id: "$gym_id"
      },
      wins: { $sum: 1 }
    }
  },
  { $sort: { "_id.trainer_id": 1, wins: -1 } },
  {
    $group: {
      _id: "$_id.trainer_id",
      top: { $first: { gym_id: "$_id.gym_id", wins: "$wins" } }
    }
  },
  {
    $lookup: {
      from: "Trainer",
      localField: "_id",
      foreignField: "_id",
      as: "trainer"
    }
  },
  { $unwind: "$trainer" },
  {
    $lookup: {
      from: "Gym",
      localField: "top.gym_id",
      foreignField: "_id",
      as: "gym"
    }
  },
  { $unwind: "$gym" },
  {
    $project: {
      _id: 0,
      trainer: "$trainer.name",
      gym: "$gym.name",
      wins: "$top.wins"
    }
  },
  { $sort: { trainer: 1 } }
]);

// 3. Most winning trainer
db.Battle.aggregate([
  {
    $group: {
      _id: "$participants.winner.trainer_id",
      wins: { $sum: 1 }
    }
  },
  { $sort: { wins: -1 } },
  { $limit: 1 },
  {
    $lookup: {
      from: "Trainer",
      localField: "_id",
      foreignField: "_id",
      as: "trainer"
    }
  },
  { $unwind: "$trainer" },
  {
    $project: {
      _id: 0,
      trainer: "$trainer.name",
      wins: 1
    }
  }
]);

// 4. Most winning Pokémon 
db.Battle.aggregate([
  {
    $group: {
      _id: "$participants.winner.pokemon_id",
      wins: { $sum: 1 }
    }
  },
  { $sort: { wins: -1 } },
  { $limit: 1 },
  {
    $lookup: {
      from: "Pokemon",
      localField: "_id",
      foreignField: "_id",
      as: "pokemon"
    }
  },
  { $unwind: "$pokemon" },
  {
    $project: {
      _id: 0,
      pokemon_name: "$pokemon.name",
      wins: 1
    }
  }
]);

// 5. Most winning trainer + most winning Pokémon
db.Battle.aggregate([
  {
    $group: {
      _id: "$participants.winner.trainer_id",
      wins: { $sum: 1 }
    }
  },
  { $sort: { wins: -1 } },
  { $limit: 1 },
  {
    $lookup: {
      from: "Trainer",
      localField: "_id",
      foreignField: "_id",
      as: "trainer"
    }
  },
  { $unwind: "$trainer" },
  {
    $project: {
      _id: 0,
      kind: "trainer",
      name: "$trainer.name",
      wins: 1
    }
  },
  {
    $unionWith: {
      coll: "Battle",
      pipeline: [
        {
          $group: {
            _id: "$participants.winner.pokemon_id",
            wins: { $sum: 1 }
          }
        },
        { $sort: { wins: -1 } },
        { $limit: 1 },
        {
          $lookup: {
            from: "Pokemon",
            localField: "_id",
            foreignField: "_id",
            as: "pokemon"
          }
        },
        { $unwind: "$pokemon" },
        {
          $project: {
            _id: 0,
            kind: "pokemon",
            name: "$pokemon.name",
            wins: 1
          }
        }
      ]
    }
  }
]);

// 6. Wins for each Pokémon and its evolutions (sum over evolution chain)
db.Pokemon.aggregate([
  // Base Pokémon: nobody evolves into them
  {
    $lookup: {
      from: "Pokemon",
      localField: "_id",
      foreignField: "evolves_to",
      as: "prevForms"
    }
  },
  { $match: { prevForms: { $eq: [] } } },

  // Get full evolution line starting from the base
  {
    $graphLookup: {
      from: "Pokemon",
      startWith: "$_id",
      connectFromField: "evolves_to",
      connectToField: "_id",
      as: "line"
    }
  },

  // Build an array of all Pokemon IDs in the line: base + descendants
  {
    $project: {
      rootPokemon: "$name",
      lineIds: {
        $concatArrays: [
          ["$_id"],
          {
            $map: {
              input: "$line",
              as: "p",
              in: "$$p._id"
            }
          }
        ]
      }
    }
  },

  // Count wins for any Pokemon in this line
  {
    $lookup: {
      from: "Battle",
      let: { ids: "$lineIds" },
      pipeline: [
        {
          $match: {
            $expr: {
              $in: ["$participants.winner.pokemon_id", "$$ids"]
            }
          }
        },
        { $count: "wins_in_chain" }
      ],
      as: "winsAgg"
    }
  },

  // Normalize missing wins to 0
  {
    $addFields: {
      wins_in_chain: {
        $ifNull: [
          { $arrayElemAt: ["$winsAgg.wins_in_chain", 0] },
          0
        ]
      }
    }
  },

  {
    $project: {
      _id: 0,
      rootPokemon: 1,
      wins_in_chain: 1
    }
  },
  { $sort: { wins_in_chain: -1, rootPokemon: 1 } }
]);

// 7. Gym that hosted the highest number of battles
db.Battle.aggregate([
  {
    $group: {
      _id: "$gym_id",
      hosted: { $sum: 1 }
    }
  },
  { $sort: { hosted: -1 } },
  { $limit: 1 },
  {
    $lookup: {
      from: "Gym",
      localField: "_id",
      foreignField: "_id",
      as: "gym"
    }
  },
  { $unwind: "$gym" },
  {
    $project: {
      _id: 0,
      gym: "$gym.name",
      hosted: 1
    }
  }
]);

// 8. For each gym, total number of distinct Pokémon that fought there
db.Battle.aggregate([
  {
    $project: {
      gym_id: 1,
      pokemon_ids: [
        "$participants.winner.pokemon_id",
        "$participants.loser.pokemon_id"
      ]
    }
  },
  { $unwind: "$pokemon_ids" },
  {
    $group: {
      _id: { gym_id: "$gym_id", pokemon_id: "$pokemon_ids" }
    }
  },
  {
    $group: {
      _id: "$_id.gym_id",
      fighters: { $sum: 1 }
    }
  },
  {
    $lookup: {
      from: "Gym",
      localField: "_id",
      foreignField: "_id",
      as: "gym"
    }
  },
  { $unwind: "$gym" },
  {
    $project: {
      _id: 0,
      gym: "$gym.name",
      fighters: 1
    }
  },
  { $sort: { fighters: -1 } }
]);

// 9. Pokémon that fought in the most different gyms
db.Battle.aggregate([
  {
    $project: {
      gym_id: 1,
      winner_pokemon: "$participants.winner.pokemon_id",
      loser_pokemon: "$participants.loser.pokemon_id"
    }
  },
  {
    $project: {
      pairs: [
        { gym_id: "$gym_id", pokemon_id: "$winner_pokemon" },
        { gym_id: "$gym_id", pokemon_id: "$loser_pokemon" }
      ]
    }
  },
  { $unwind: "$pairs" },
  {
    $group: {
      _id: {
        pokemon_id: "$pairs.pokemon_id",
        gym_id: "$pairs.gym_id"
      }
    }
  },
  {
    $group: {
      _id: "$_id.pokemon_id",
      gymCount: { $sum: 1 }
    }
  },
  { $sort: { gymCount: -1 } },
  { $limit: 10 },
  {
    $lookup: {
      from: "Pokemon",
      localField: "_id",
      foreignField: "_id",
      as: "pokemon"
    }
  },
  { $unwind: "$pokemon" },
  {
    $project: {
      _id: 0,
      pokemon: "$pokemon.name",
      gymCount: 1
    }
  }
]);

// 10. Pokémon type with the best winning ratio
db.Battle.aggregate([
  // reshape battle into "fights" documents (pokemon_id + isWin)
  {
    $project: {
      winner_pokemon: "$participants.winner.pokemon_id",
      loser_pokemon: "$participants.loser.pokemon_id"
    }
  },
  {
    $project: {
      fights: [
        { pokemon_id: "$winner_pokemon", isWin: true },
        { pokemon_id: "$loser_pokemon", isWin: false }
      ]
    }
  },
  { $unwind: "$fights" },
  {
    $group: {
      _id: "$fights.pokemon_id",
      fights: { $sum: 1 },
      wins: {
        $sum: { $cond: ["$fights.isWin", 1, 0] }
      }
    }
  },
  // join Pokémon to get types
  {
    $lookup: {
      from: "Pokemon",
      localField: "_id",
      foreignField: "_id",
      as: "pokemon"
    }
  },
  { $unwind: "$pokemon" },
  { $unwind: "$pokemon.types" },
  {
    $group: {
      _id: "$pokemon.types",
      fights: { $sum: "$fights" },
      wins: { $sum: "$wins" }
    }
  },
  { $match: { fights: { $gt: 0 } } },
  {
    $project: {
      wins: 1,
      fights: 1,
      winRatio: { $divide: ["$wins", "$fights"] }
    }
  },
  { $sort: { winRatio: -1 } },
  { $limit: 5 },
  // attach type name
  {
    $lookup: {
      from: "Type",
      localField: "_id",
      foreignField: "_id",
      as: "typeInfo"
    }
  },
  { $unwind: "$typeInfo" },
  {
    $project: {
      _id: 0,
      type: "$typeInfo.name",
      winRatio: { $round: ["$winRatio", 3] },
      wins: 1,
      fights: 1
    }
  }
]);

// 11. Number of Pokémon that are at maximum evolution
// Assumes:
//   "evolution.next" is null or missing for final evolutions
db.Pokemon.aggregate([
  {
    $match: {
      $or: [
        { "evolution.next": null },
        { "evolution.next": { $exists: false } }
      ]
    }
  },
  { $count: "numMaxEvolution" }
]);

// 12. Most powerful Pokémon (by total) 
db.Pokemon.aggregate([
  { 
    $project: { 
      _id: 0, 
      name: 1, 
      tot: "$stats.tot", 
      form: "$has_form" 
    } 
  },
  { $sort: { tot: -1 } },
  { $limit: 10 }
]);

// 13. Most powerful Pokémon for each type 
db.Pokemon.aggregate([
  { $unwind: "$types" },
  { $sort: { "stats.tot": -1 } },
  {
    $group: {
      _id: "$types",
      pokemon: { $first: "$name" },
      total: { $first: "$stats.tot" }
    }
  },
  {
    $lookup: {
      from: "Type",
      localField: "_id",
      foreignField: "_id",
      as: "typeInfo"
    }
  },
  { $unwind: "$typeInfo" },
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

// 14. Group all Pokémon of type Water
db.Type.aggregate([
  { $match: { name: "Water" } },
  {
    $lookup: {
      from: "Pokemon",
      localField: "_id",
      foreignField: "types",
      as: "pokemon"
    }
  },
  { $unwind: "$pokemon" },
  {
    $project: {
      _id: 0,
      pokemon: "$pokemon.name"
    }
  },
  { $sort: { pokemon: 1 } }
]);

// 15. Highest improvement (Total) from base → max evolution
db.Pokemon.aggregate([
  // 1) Base evolutions: no previous form
  {
    $lookup: {
      from: "Pokemon",
      localField: "_id",
      foreignField: "evolves_to",
      as: "prevForms"
    }
  },
  { $match: { prevForms: { $eq: [] } } },

  // 2) Get all evolutions in the line (descendants)
  {
    $graphLookup: {
      from: "Pokemon",
      startWith: "$_id",
      connectFromField: "evolves_to",
      connectToField: "_id",
      as: "line"
    }
  },

  // 3) Convert totals to numbers
  {
    $addFields: {
      baseTotal: { $toInt: "$stats.tot" },
      lineTotals: {
        $map: {
          input: "$line",
          as: "p",
          in: { $toInt: "$$p.stats.tot" }
        }
      }
    }
  },

  // 4) Max descendant total (or base itself if no descendants)
  {
    $addFields: {
      maxDescTotal: {
        $cond: [
          { $gt: [{ $size: "$lineTotals" }, 0] },
          { $max: "$lineTotals" },
          "$baseTotal"
        ]
      }
    }
  },

  // 5) Improvement = maxDescTotal − baseTotal
  {
    $addFields: {
      improvement: { $subtract: ["$maxDescTotal", "$baseTotal"] }
    }
  },

  {
    $project: {
      _id: 0,
      basePokemon: "$name",
      baseTotal: 1,
      maxDescTotal: 1,
      improvement: 1
    }
  },
  { $sort: { improvement: -1, basePokemon: 1 } },
  { $limit: 20 }
]);

// 16. Gyms and their type specialization
db.Gym.aggregate([
  {
    $lookup: {
      from: "Type",
      localField: "type",
      foreignField: "_id",
      as: "typeInfo"
    }
  },
  { $unwind: "$typeInfo" },
  {
    $project: {
      _id: 0,
      gym: "$name",
      specializesIn: "$typeInfo.name"
    }
  },
  { $sort: { gym: 1, specializesIn: 1 } }
]);