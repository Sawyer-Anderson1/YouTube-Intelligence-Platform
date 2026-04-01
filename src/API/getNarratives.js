import axios from "axios";

const BACKEND_URL = "http://127.0.0.1:5000"; // backend server

const getNarratives = async () => {
  let res = await axios.get(`${BACKEND_URL}/results`);
  res = res.data.filter((res) => res.query_type == "narratives");
  console.log(res);
  return res;
};

export default getNarratives;
