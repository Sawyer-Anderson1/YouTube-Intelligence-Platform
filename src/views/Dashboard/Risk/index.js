import { Flex, Image, Spinner } from "@chakra-ui/react";
import React, { useState, useEffect } from "react";
import RiskCard from "./components/RiskCard";
import getRiskFactors from "../../../API/getRiskFactors";

function RiskCards() {
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchRisks = async () => {
      try {
        const res = await getRiskFactors();
        if (!cancelled) setRisks(res.data);
      } catch (error) {
        console.error("Failed to fetch risk factors:", error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchRisks();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Spinner />;

  return (
    <Flex direction="row" flexWrap="wrap" gap="22px" my="60px">
      {risks.map((risk, index) => (
        <RiskCard
          key={index}
          title={risk.title}
          name={risk.name}
          description={risk.description}
          image={<Image alt="[image]" minWidth={{ md: "300px", lg: "auto" }} />}
        />
      ))}
    </Flex>
  );
}

export default RiskCards;
