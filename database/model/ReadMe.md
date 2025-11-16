# Pokémon Database Schema Model

## Overview
This schema model represents the structure of a NoSQL MongoDB database designed to manage Pokémon-related data, including trainers, battles, gyms, and types.

## Collections
### 1. `pokemon.trainer`
- Stores trainer profiles.
- Fields: `_id`, `name`, `leads`, `owns`

### 2. `pokemon.pokemon`
- Stores Pokémon details.
- Fields: `_id`, `name`, `pokedex`, `evolves_to`, `has_form`, `stats`, `types`

### 3. `pokemon.gym`
- Stores gym information.
- Fields: `_id`, `name`, `badge_name`, `location`, `region`, `type`

### 4. `pokemon.battles`
- Stores battle records.
- Fields: `_id`, `date`, `gym_id`, `participants` (winner & loser)

### 5. `pokemon.type`
- Stores Pokémon type definitions.
- Fields: `_id`, `name`

## Relationships
- Trainers own Pokémon (`owns → pokemon._id`)
- Pokémon may evolve or have alternate forms (`evolves_to`, `has_form`)
- Battles reference trainers and Pokémon
- Gyms are linked to battles via `gym_id`
- Pokémon are associated with types

## Usage
- Import the `.mdm` file in MongoDB Compass via the Schema tab.
- Use Compass or VS Code MongoDB extension to explore and query the data.
- Refer to the schema diagrams for visual understanding.

## Version History
- v1.0 – Initial schema design and export
- v1.1 – /* "Add once schema change" */

## Notes
- This schema is flexible and designed for learning and prototyping.

# ✅ Team Schema Review Checklist

This checklist helps ensure quality and consistency when reviewing MongoDB schema models collaboratively.

## 🔍 Structure & Consistency
- [X] Are all field names consistent across collections?
- [X] Are data types clearly defined and appropriate?
- [X] Are optional fields handled properly (e.g., `null`, defaults)?

## 🔗 Relationships
- [X] Are relationships between collections clearly mapped?
- [X] Are references (e.g., foreign keys) valid and documented?

## 📊 Data Modeling
- [X] Are embedded documents used where appropriate?
- [X] Are arrays used correctly for multi-value fields?
- [ ] Is the schema normalized or denormalized appropriately?

## ⚙️ Performance
- [ ] Are indexes defined for frequently queried fields?
- [ ] Are large arrays or nested objects optimized?

## 📁 Documentation
- [X] Is the README up to date and clear?
- [X] Are diagrams available and understandable?
- [X] Are schema changes tracked (e.g., version history)?

## 🧪 Testing
- [ ] Have sample queries been tested?
- [ ] Are edge cases considered (e.g., missing fields, empty arrays)?
- [ ] Is the schema compatible with the application logic?


# 🛠️ Recommended Way to Update a MongoDB Schema
MongoDB is schema-flexible, but updating a schema without planning can lead to data inconsistencies or loss. The recommended approach is to treat schema changes like code changes — versioned, tested, and documented.

## ✅ Use Schema Versioning and Migration Scripts

- Track schema versions (e.g., v1.0, v1.1) in your documentation.
- Write migration scripts to safely update existing documents.
- Avoid manual edits to production data.

## ✅ Use Validation Rules (Optional)

- MongoDB supports JSON Schema validation at the collection level.
- Use validation to enforce structure, but apply cautiously to avoid rejecting legacy documents.


# 🔄 Workflow for Safe Schema Updates
Follow this workflow when a team member modifies the schema model:

### 1. Review the New Schema

- Compare the updated .mdm model with the current schema.
- Identify added, removed, or changed fields.

### 2. Test on a Copy

- Clone the collection or use a test database.
- Apply the new schema and test queries and updates.

### 3. Write Migration Scripts
Use mongosh or backend scripts to:

- Add new fields with default values
db.collection.updateMany({}, { $set: { newField: "default" } })
- Rename fields
db.collection.updateMany({}, { $rename: { "oldField": "newField" } })
- Convert data types if needed

### 4. Validate and Test

- Run queries to check for missing or malformed data.
- Use Compass’s Schema tab to re-analyze structure.

### 5. Deploy Carefully

- Apply changes to production only after thorough testing.
- Always back up data before migration.

### 6. Document the Change

- Update the README and schema diagrams.
- Update the Team Schema Review Checklist.
- Note the schema version and migration steps.


## 📘 Best Practices

- ✅ Always back up your data before applying schema changes.
- ✅ Use scripts for consistency and repeatability.
- ✅ Keep schema documentation and diagrams up to date.
- ✅ Communicate schema changes clearly with your team.
- ✅ Validate changes using Compass or automated tests.
