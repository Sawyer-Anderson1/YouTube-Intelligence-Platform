import axios from "axios";

const BACKEND_URL = "http://127.0.0.1:8000"; // backend server

const getRiskFactors = async () => {
  let res = await axios.get(`${BACKEND_URL}/risk_factors`);
  console.log(res);
  return res;
};

export default getRiskFactors;
