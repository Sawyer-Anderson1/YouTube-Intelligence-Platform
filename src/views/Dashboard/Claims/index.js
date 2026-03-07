// Chakra imports
import {
  Flex,
  Grid,
  Image,
  SimpleGrid,
  useColorModeValue,
  Spinner,
} from "@chakra-ui/react";
import React from "react";
import ClaimCard from "./components/ClaimCard";
import getClaims from "../../../API/getClaims";
import { useState, useEffect } from "react";
function ClaimCards() {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;

    const fetchClaims = async () => {
      try {
        const res = await getClaims();
        if (!cancelled) setClaims(res.data);
      } catch (error) {
        console.error("Failed to fetch claims:", error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchClaims();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Spinner />;
  return (
    <Grid
      templateColumns={{
        sm: "1fr",
        md: "repeat(2, 1fr)",
        xl: "repeat(4, 1fr)",
      }}
      my="60px"
      gap="22px"
    >
      {claims.map((claim, index) => (
        <ClaimCard
          key={index}
          title={claim.title}
          name={claim.name}
          description={claim.description}
          image={<Image alt="[image]" minWidth={{ md: "300px", lg: "auto" }} />}
        />
      ))}
    </Grid>
  );
}

export default ClaimCards;
