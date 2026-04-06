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
import {
  GreenArrowUpIcon,
  RedArrowDownIcon,
} from "components/Icons/Icons.js";
import Claims from "./components/Claims";
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

      const rawClaims = res?.[0]?.result_text || {};

      const formattedClaims = Object.entries(rawClaims).map(
        ([title, claim]) => {
          const views = Number(claim.view_count) || 0;
          const likes = Number(claim.like_count) || 0;
          const comments = Number(claim.comment_count) || 0;

          const interaction = views > 0 ? ((likes + comments * 10) / views) * 100 : 0;

          return {
            name: title,
            quote: `"${claim.Quote}"`,
            views: views.toLocaleString(),
            likes: likes.toLocaleString(),
            comments: comments.toLocaleString(),
            interaction: interaction,
            logo:
              interaction > 3
                ? GreenArrowUpIcon
                : RedArrowDownIcon,
          };
        }
      );

        if (!cancelled) setClaims(formattedClaims);
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
    <Flex flexDirection='column' pt={{ base: "120px", md: "75px" }}>
      <Grid
        //templateColumns={{ sm: "1fr", md: "1fr 1fr", lg: "2fr 1fr" }}
        templateRows={{ sm: "1fr auto", md: "1fr", lg: "1fr" }}
        gap='24px'>
        <Claims
          title={"Current Claims"}
          amount={claims.length}
          captions={["Claim", "Quote", "Views", "Likes", "Comments", "Interaction"]}
          data={claims}
        />
      </Grid>
    </Flex>
  );
}

export default ClaimCards;
