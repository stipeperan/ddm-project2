// 1) Check if a pokedex number is available
// Use the lowercase collection names and fields that match validation (strings)
db.pokemon.findOne({ pokedex: "9999" })

// 2) Insert a new Pokémon (document must satisfy the validator)
// Provide all required fields and use string ids/types as in the schema
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

// 3) Verify the insert
db.pokemon.findOne({ _id: newPokemonId })

// 4) Find owners (trainers) of this Pokemon using an aggregation (lookup)
db.pokemon.aggregate([
	{ $match: { _id: newPokemonId } },
	{ $lookup: { from: "trainer", localField: "_id", foreignField: "owns", as: "owners" } }
])

// 5) Remove references to the Pokemon from any trainer (safe removal)
// Pull by matching value; trainer.owns is stored as array of string ids (or null)
db.trainer.updateMany({ owns: newPokemonId }, { $pull: { owns: newPokemonId } })

// Then remove the Pokemon document itself
db.pokemon.deleteOne({ _id: newPokemonId })

// 6) Add the Pokemon to a trainer (ensure owns is an array first, then add)
// Make sure we do not duplicate entries by using $addToSet
// If the field can be null, ensure it's an array before pushing
db.trainer.updateOne({ _id: "1", $or: [ { owns: { $exists: false } }, { owns: null } ] }, { $set: { owns: [] } });
db.trainer.updateOne({ _id: "1" }, { $addToSet: { owns: newPokemonId } });

// 7) Update evolution links: set base Pokemon to evolve to a different id
// All ids and fields are strings according to the schema
db.pokemon.updateOne({ _id: "1" }, { $set: { evolves_to: "3" } })