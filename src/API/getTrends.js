import axios from "axios";

const BACKEND_URL = "http://127.0.0.1:5000"; // backend server

const getTrends = async () => {
  let res = await axios.get(`${BACKEND_URL}/results`);
  res = res.data.filter((res) => res.query_type == "trends");
  console.log(res);
  return res;
};

export default getTrends;
