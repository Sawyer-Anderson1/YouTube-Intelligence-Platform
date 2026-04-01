require("dotenv").config();
const express = require("express");
const { MongoClient, ServerApiVersion } = require("mongodb");

const app = express();
const cors = require("cors");
app.use(cors());
const PORT = 5000;

const client = new MongoClient(process.env.MONGO_URI, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  },
});

async function connectDB() {
  try {
    await client.connect();
    console.log("✅ Connected to MongoDB");

    const db = client.db("youtube_intelligence");

    app.get("/results", async (req, res) => {
      try {
        const videos = await db.collection("results").find({}).toArray();

        res.json(videos);
      } catch (err) {
        console.error(err);
        res.status(500).send("Error fetching data");
      }
    });
  } catch (err) {
    console.error(err);
  }
}

connectDB();

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
