// 1 check if pokedex number is available
db.Pokemon.find({ pokedex: "9999" })

// 2 insert our new pokemon
db["Pokemon"].insertOne({   pokedex: "9999",   name: "DataDesignosaur",   stats: {     hp: “99”,     atk: “99”,     def: “99”,     sp_atk: “99”,     sp_def: “99”,     tot: “1000”   },   types: [     "5",     "12"   ] }) 

// 3 check if properly inserted
db.Pokemon.find({ pokedex: "9999" })

// 4 remove our new pokemon
db.Pokemon.aggregate([{$match: {_id: "199"}}, {$lookup: {from: "Trainer", localField:"_id", foreignField:"owns", as: "Owner"}}])

// 5 remove Pokemon from previous owner
db.Trainer.updateOne({owns: "199"}, {$pull: {owns: "199"}})

// 6 add Pokemon to new owner
db.Trainer.updateOne({_id: "1"}, {$push: {owns: "199"}})

// 7 Remove a “middle” evolution and connect base ev. to final ev.
db.Pokemon.updateOne({ _id: "1" }, {$set: {evolves_to: "3" }})