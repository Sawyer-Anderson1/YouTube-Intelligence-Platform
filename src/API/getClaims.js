import axios from "axios";

const BACKEND_URL =
  "https://youtube-intelligence-api-brb3gghzh5eqahf5.eastus2-01.azurewebsites.net"; // backend server

const getClaims = async () => {
  let res = await axios.get(`${BACKEND_URL}/claims`);

  const filteredClaims = res.data.filter(
    (item) => item.source_chunks && item.source_chunks.length > 0,
  );

  return filteredClaims;
};

export default getClaims;
