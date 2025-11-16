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

// 5. Most winning trainer + most winning Pokémon (UNION-style)
db.Battle.aggregate([
  // Part A: most winning trainer
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
// Assumes evolution_line[0] = root Pokémon name (or ID – adjust if needed)
// db.Battle.aggregate([
//   // count wins per Pokémon
//   {
//     $group: {
//       _id: "$participants.winner.pokemon_id",
//       wins: { $sum: 1 }
//     }
//   },
//   // join with Pokemon to get evolution_line
//   {
//     $lookup: {
//       from: "Pokemon",
//       localField: "_id",
//       foreignField: "_id",
//       as: "pokemon"
//     }
//   },
//   { $unwind: "$pokemon" },
//   {
//     $project: {
//       wins: 1,
//       root: { $arrayElemAt: ["$pokemon.evolution_line", 0] }
//     }
//   },
//   {
//     $group: {
//       _id: "$root",
//       wins_in_chain: { $sum: "$wins" }
//     }
//   },
//   { $sort: { wins_in_chain: -1, _id: 1 } },
//   {
//     $project: {
//       _id: 0,
//       rootPokemon: "$_id",
//       wins_in_chain: 1
//     }
//   }
// ]);

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
// Assumes evolution_line[0] is the base Pokémon's name
// db.Pokemon.aggregate([
//   // 1) Select only base evolutions (no prev evolution)
//   {
//     $match: { "evolution.prev": null }
//   },

//   // 2) Lookup all descendants via graph recursion
//   {
//     $graphLookup: {
//       from: "Pokemon",
//       startWith: "$_id",
//       connectFromField: "evolution.next",
//       connectToField: "_id",
//       as: "descendants"
//     }
//   },

//   // 3) Convert base total and descendants' totals to numbers
//   {
//     $addFields: {
//       baseTotalNum: { $toInt: "$stats.tot" },
//       descendantsTotals: {
//         $map: {
//           input: "$descendants",
//           as: "d",
//           in: { $toInt: "$$d.stats.tot" }
//         }
//       }
//     }
//   },

//   // 4) Compute max descendant total
//   {
//     $addFields: {
//       maxDescTotalNum: { $max: "$descendantsTotals" }
//     }
//   },

//   // 5) Compute improvement (max descendant total − base total)
//   {
//     $addFields: {
//       improvement: {
//         $subtract: ["$maxDescTotalNum", "$baseTotalNum"]
//       }
//     }
//   },

//   // 6) Output final fields only
//   {
//     $project: {
//       _id: 0,
//       basePokemon: "$name",
//       baseTotal: "$baseTotalNum",
//       maxDescTotal: "$maxDescTotalNum",
//       improvement: 1
//     }
//   },

//   // 7) SORT: decreasing order (biggest improvement first)
//   { $sort: { improvement: -1 } },

//   // 8) limit to top 20 
//   { $limit: 20 }
// ]);

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