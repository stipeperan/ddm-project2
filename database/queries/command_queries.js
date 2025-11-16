// ================
// 1. Add a Pokémon
// ================
// Test before
db.pokemon.findOne({ pokedex: "9999" })

// Command
const newPokemon = {
	_id: "p9999",
	pokedex: "9999",
	name: "DataDesignosaur",
	evolves_to: null,
	has_form: null,
	stats: { hp: "99", atk: "99", def: "99", sp_atk: "99", sp_def: "99", tot: "499" },
	types: ["5", "12"]
};

db.pokemon.insertOne(newPokemon);
const newPokemonId = newPokemon._id;

// Test after
db.pokemon.findOne({ _id: newPokemonId })

// ==========================================
// 2. Move a Pokémon from one trainer to another
// ==========================================
const pokemonId = "217";
const newTrainerId = "1";

// Test before
db.pokemon.aggregate([
	{ $match: { _id: pokemonId } },
	{ $lookup: { from: "trainer", localField: "_id", foreignField: "owns", as: "owners" } }
])

// Command
// Remove references to the Pokemon from any trainer (1 pokemon -> 1 trainer)
db.trainer.updateMany({ owns: pokemonId }, { $pull: { owns: pokemonId } })

// Add the Pokemon to a trainer (ensure owns is an array first, then add)
db.trainer.updateOne({ _id: newTrainerId, $or: [ { owns: { $exists: false } }, { owns: null } ] }, { $set: { owns: [] } });
db.trainer.updateOne({ _id: newTrainerId }, { $addToSet: { owns: pokemonId } });

// Test after
db.pokemon.aggregate([
	{ $match: { _id: pokemonId } },
	{ $lookup: { from: "trainer", localField: "_id", foreignField: "owns", as: "owners" } }
])

// ================================================================
// 3. Remove a “middle” evolution and connect base ev. to final ev.
// ================================================================
const baseId = "1";  // Basic PokemonId

// Test before
db.pokemon.findOne({ _id: baseId });

// Command
const base = db.pokemon.findOne({ _id: baseId });
const middleId = base.evolves_to;
const middle = db.pokemon.findOne({ _id: middleId });
const finalId = middle.evolves_to;

// 1) Any Pokemon that evolved into middle should now evolve into final
db.pokemon.updateMany(
  { evolves_to: middleId },
  { $set: { evolves_to: finalId } }
);

// 2) Delete the middle evolution
db.pokemon.deleteOne({ _id: middleId });

// Test after
db.pokemon.find(
  { _id: { $in: [baseId, middleId, finalId] } },
  { _id: 1, name: 1, evolves_to: 1 }
);

// =========================================================================
// 4. Remove the gym leader with the lowest win ratio and delete the trainer
// =========================================================================
const worstLeader = db.trainer.aggregate([
  // Only gym leaders
  {
    $match: {
      leads: { $exists: true, $ne: null }
    }
  },

  // Look up all battles where this trainer participated (winner OR loser)
  {
    $lookup: {
      from: "battles",
      let: { tid: "$_id" },
      pipeline: [
        {
          $match: {
            $expr: {
              $or: [
                { $eq: ["$participants.winner.trainer_id", "$$tid"] },
                { $eq: ["$participants.loser.trainer_id", "$$tid"] }
              ]
            }
          }
        }
      ],
      as: "battles"
    }
  },

  // total battles and wins for this trainer
  {
    $addFields: {
      total: { $size: "$battles" },
      wins: {
        $size: {
          $filter: {
            input: "$battles",
            as: "b",
            cond: {
              $eq: ["$$b.participants.winner.trainer_id", "$_id"]
            }
          }
        }
      }
    }
  },

  // Ignore leaders with no battles
  {
    $match: {
      total: { $gt: 0 }
    }
  },

  // win ratio = wins / total
  {
    $addFields: {
      ratio: {
        $divide: ["$wins", "$total"]
      }
    }
  },

  // Worst first: lowest ratio, then fewest battles as tiebreaker
  {
    $sort: {
      ratio: 1,
      total: 1
    }
  },
  { $limit: 1 }
]).toArray()[0];

db.trainer.deleteOne({ _id: worstLeader._id });

// ====================================================================
// 5. Create the trainer Mario, give him the two strongest free Pokémon
// and assign him to an ownerless gym
// ====================================================================
const freeStrongest = db.pokemon.aggregate([
  // Join with trainers that own this pokemon
  {
    $lookup: {
      from: "trainer",
      localField: "_id",
      foreignField: "owns",
      as: "owners"
    }
  },
  // Keep only pokemon with no owners
  {
    $match: {
      owners: { $eq: [] }
    }
  },
  // Turn stats.tot (string) into a number for correct sorting
  {
    $addFields: {
      totalInt: { $toInt: "$stats.tot" }
    }
  },
  // Strongest first
  {
    $sort: { totalInt: -1 }
  },
  // Grab only the top 2
  { $limit: 2 }
]).toArray();

const marioPokemonIds = freeStrongest.map(p => p._id);
marioPokemonIds;

// find an ownerless gym
const freeGym = db.gym.aggregate([
  {
    $lookup: {
      from: "trainer",
      localField: "_id",
      foreignField: "leads",
      as: "leaders"
    }
  },
  {
    $match: {
      leaders: { $eq: [] }  // gyms with no leader
    }
  },
  { $limit: 1 }
]).toArray()[0];

const marioGymId = freeGym._id;
marioGymId;

// Create Mario
const marioId = "t9999";

const mario = {
  _id: marioId,
  name: "Mario",
  owns: marioPokemonIds,
  leads: marioGymId
};

db.trainer.insertOne(mario);

// test after
db.trainer.findOne({ _id: marioId});