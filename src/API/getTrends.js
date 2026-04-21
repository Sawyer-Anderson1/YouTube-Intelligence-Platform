import axios from "axios";

const BACKEND_URL =
  "https://youtube-intelligence-api-brb3gghzh5eqahf5.eastus2-01.azurewebsites.net"; // backend server

const getTrends = async () => {
  let res = await axios.get(`${BACKEND_URL}/trends`);
  return res.data;
};

export default getTrends;
