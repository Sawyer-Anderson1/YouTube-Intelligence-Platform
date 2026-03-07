import getResults from "./getResults.js";
import getClaims from "./getResults.js";

const run = async () => {
  try {
    const results = await getResults();
    console.log("Results:", results);
  } catch (err) {
    console.error("Error fetching results:", err.message);
  }
};

run();
