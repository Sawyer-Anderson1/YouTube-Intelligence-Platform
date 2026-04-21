import axios from "axios";

const BACKEND_URL =
  "https://youtube-intelligence-api-brb3gghzh5eqahf5.eastus2-01.azurewebsites.net"; // backend server

const getComments = async () => {
  let res = await axios.get(`${BACKEND_URL}/results`);
  res = res.data.filter((res) => res.query_type == "comments");
  console.log(res);
  return res;
};

export default getComments;
