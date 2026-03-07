import { Flex, Image, Spinner } from "@chakra-ui/react";
import React, { useState, useEffect } from "react";
import NarrativeCard from "./components/NarrativeCard";
import getNarratives from "../../../API/getNarratives";

function NarrativeCards() {
  const [narratives, setNarratives] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchNarratives = async () => {
      try {
        const res = await getNarratives();
        if (!cancelled) setNarratives(res.data);
      } catch (error) {
        console.error("Failed to fetch narratives:", error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchNarratives();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Spinner />;

  return (
    <Flex direction="row" flexWrap="wrap" gap="22px" my="60px">
      {narratives.map((narrative, index) => (
        <NarrativeCard
          key={index}
          title={narrative.title}
          name={narrative.name}
          description={narrative.description}
          image={<Image alt="[image]" minWidth={{ md: "300px", lg: "auto" }} />}
        />
      ))}
    </Flex>
  );
}

export default NarrativeCards;
