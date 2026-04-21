import axios from "axios";

const BACKEND_URL =
  "https://youtube-intelligence-api-brb3gghzh5eqahf5.eastus2-01.azurewebsites.net"; // backend server

const getNarratives = async () => {
  let res = await axios.get(`${BACKEND_URL}/narratives`);
  return res.data;
};

export default getNarratives;
