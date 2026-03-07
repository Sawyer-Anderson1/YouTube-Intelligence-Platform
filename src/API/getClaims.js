import axios from "axios";

const BACKEND_URL = "http://127.0.0.1:8000"; // backend server

const getClaims = async () => {
  let res = await axios.get(`${BACKEND_URL}/claims`);
  return res;
};

export default getClaims;
