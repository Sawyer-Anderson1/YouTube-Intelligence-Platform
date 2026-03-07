import axios from "axios";

const BACKEND_URL = "http://127.0.0.1:8000"; // backend server

const getNarratives = async () => {
  let res = await axios.get(`${BACKEND_URL}/narratives`);
  console.log(res);
  return res;
};

export default getNarratives;
