# 🧩 DDM Project 2 — Pokémon Database with MongoDB

## 📘 Overview
This project was developed as part of the **Data Design and Modeling (DDM)** course.  
It extends the work from **Project 1**, where we designed and queried a Pokémon dataset using **Neo4j** and the **graph data model**.  

In this second phase, we adopt a **NoSQL approach** using **MongoDB**, focusing on the **document-oriented model**.  
Our goal is to design suitable collections, import JSON data, and perform complex queries and aggregations using **MongoDB Compass**.

---

## 📂 Repository Structure
```
ddm-project2/
├── data/
│   ├── pokemons.json          # Pokémon entity data
│   ├── abilities.json         # Pokémon abilities
│   ├── types.json             # Pokémon types
│   └── evolutions.json        # Evolution relationships
├── queries/
│   ├── find_pokemon_by_type.json
│   ├── aggregate_average_stats.json
│   └── ...
├── scripts/
│   └── csv_to_json.py         # Optional helper script for data conversion
└── README.md                  # Project documentation
```

---

## 🧠 Conceptual Design
The data model is based on the main Pokémon entities:
- **Pokémon**: General information, stats, and references to types and abilities  
- **Types**: Category information (e.g., Fire, Water, Electric)  
- **Abilities**: Special powers or passive effects  
- **Evolutions**: Relationships between Pokémon species  

Each collection is stored as a separate JSON file and imported into MongoDB Compass.

---

## 🧰 Technologies Used
- **MongoDB Compass** → Data import and query execution  
- **VS Code** → Dataset creation and project organization  
- **Python (optional)** → CSV to JSON conversion  
- **Git + GitHub** → Version control and collaboration  

---

## ⚙️ How to Run the Project
1. **Open MongoDB Compass** and connect to your local or cloud instance.
2. **Create a new database**, e.g. `pokemon_db`.
3. For each collection (Pokémon, Types, Abilities, Evolutions):
   - Click **Import Data → JSON file**
   - Select the corresponding file from `data/`
4. Run the queries in **MongoDB Compass → Aggregations / Filter**.
5. (Optional) Export queries as JSON into the `queries/` folder.

---

## 🧮 Example Query
Example: *Find all Pokémon with “Fire” type and attack > 100*
```js
db.pokemons.find({
  "types": "Fire",
  "stats.attack": { $gt: 100 }
})
```

---

## 👥 Team Members
- **Simone Cotardo**
- **Arthur Morgan** 
- **Stipe Peran**  
- **Srimal Fonseka**   

---

## 📅 Project Context
**University:** Università della Svizzera italiana (USI)  
**Course:** Data Design and Modeling (DDM)  
**Instructor:** Prof. Dr. Marco Brambilla  
**Semester:** SA 2025 - 2026

---

## 🏁 Notes
- The JSON data follows the MongoDB document structure and has been validated before import.
- All queries were tested in MongoDB Compass.
- This project is a continuation of **DDM Project 1 (Neo4j Pokémon Database)**.

---