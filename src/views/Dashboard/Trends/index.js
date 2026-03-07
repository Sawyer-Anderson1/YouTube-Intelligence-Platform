import { Flex, Image, Spinner } from "@chakra-ui/react";
import React, { useState, useEffect } from "react";
import TrendCard from "./components/TrendCard";
import getTrends from "../../../API/getTrends";

function TrendCards() {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchTrends = async () => {
      try {
        const res = await getTrends();
        if (!cancelled) setTrends(res.data);
      } catch (error) {
        console.error("Failed to fetch trends:", error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchTrends();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Spinner />;

  return (
    <Flex direction="row" flexWrap="wrap" gap="22px" my="60px">
      {trends.map((trend, index) => (
        <TrendCard
          key={index}
          title={trend.title}
          name={trend.name}
          description={trend.description}
          image={<Image alt="[image]" minWidth={{ md: "300px", lg: "auto" }} />}
        />
      ))}
    </Flex>
  );
}

export default TrendCards;
