// Chakra imports
import {
  Flex,
  Grid,
  Image,
  SimpleGrid,
  useColorModeValue,
  Spinner,
  Text,
} from "@chakra-ui/react";
import React from "react";
import { GreenArrowUpIcon, RedArrowDownIcon } from "components/Icons/Icons.js";
import Claims from "./components/Claims";
import getClaims from "../../../API/getClaims";
import getComments from "../../../API/getComments";
import { useState, useEffect } from "react";
function ClaimCards() {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState("credibility");
  const [sortOrder, setSortOrder] = useState("desc");
  useEffect(() => {
    let cancelled = false;

    const fetchClaims = async () => {
      try {
        const [claimsRes, commentsRes] = await Promise.all([
          getClaims(),
          getComments(),
        ]);

        const rawClaims = claimsRes.reduce(
          (acc, item) => ({
            ...acc,
            ...(item.result_text || {}),
          }),
          {},
        );

        // Build comment map: video_id → comments
        const commentMap = {};

        commentsRes.forEach((item) => {
          const results = item.result_text || {};
          Object.values(results).forEach((c) => {
            const vid = c.video_id;
            if (!commentMap[vid]) commentMap[vid] = [];
            commentMap[vid].push(c);
          });
        });

        const formattedClaims = Object.entries(rawClaims).map(
          ([title, claim]) => {
            const views = Number(claim.view_count);
            const likes = Number(claim.like_count);
            const commentsCount = Number(claim.comment_count);

            const interaction =
              views > 0 ? ((likes + commentsCount * 10) / views) * 100 : 0;

            const videoId = claim.video_id;
            const videoComments = commentMap[videoId] || [];

            const total = videoComments.length;
            const negativeCount = videoComments.filter(
              (c) => c.sentiment_class === "negative",
            ).length;

            const avgPolarity =
              total > 0
                ? videoComments.reduce(
                    (sum, c) => sum + Number(c.polarity_score || 0),
                    0,
                  ) / total
                : 0;

            const negativeRatio = total > 0 ? negativeCount / total : 0;

            const credibilityScore = Math.max(
              0,
              Math.min(
                100,
                100 - negativeRatio * 80 - Math.abs(avgPolarity * 50),
              ),
            );

            const videoLink = `https://www.youtube.com/watch?v=${videoId}`;

            console.log("Video:", videoId);
            console.log("Comments:", videoComments);
            return {
              name: title,
              quote: `"${claim.Quote}"`,
              views: views.toLocaleString(),
              likes: likes.toLocaleString(),
              comments: commentsCount.toLocaleString(),
              interaction,
              logo: interaction > 3 ? GreenArrowUpIcon : RedArrowDownIcon,
              videoLink,
              credibilityScore,
            };
          },
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

  const sortedClaims = [...claims].sort((a, b) => {
    let valA, valB;

    switch (sortBy) {
      case "credibility":
        valA = a.credibilityScore;
        valB = b.credibilityScore;
        break;

      case "interaction":
        valA = a.interaction;
        valB = b.interaction;
        break;

      case "views":
        valA = Number(a.views.replace(/,/g, ""));
        valB = Number(b.views.replace(/,/g, ""));
        break;

      case "likes":
        valA = Number(a.likes.replace(/,/g, ""));
        valB = Number(b.likes.replace(/,/g, ""));
        break;

      case "comments":
        valA = Number(a.comments.replace(/,/g, ""));
        valB = Number(b.comments.replace(/,/g, ""));
        break;

      default:
        valA = a.credibilityScore;
        valB = b.credibilityScore;
    }

    return sortOrder === "asc" ? valA - valB : valB - valA;
  });
  return (
    <Flex flexDirection="column" pt={{ base: "100px", md: "60px" }}>
      <Flex
        mb="20px"
        gap="12px"
        align="center"
        p="12px 16px"
        borderRadius="16px"
        bg={useColorModeValue("white", "gray.800")}
        boxShadow="sm"
        border="1px solid"
        borderColor={useColorModeValue("gray.100", "gray.700")}
      >
        <Flex gap="8px">
          {[
            { label: "Credibility", value: "credibility" },
            { label: "Interaction", value: "interaction" },
            { label: "Views", value: "views" },
            { label: "Likes", value: "likes" },
            { label: "Comments", value: "comments" },
          ].map((option) => (
            <Flex
              key={option.value}
              px="10px"
              py="6px"
              borderRadius="12px"
              fontSize="sm"
              cursor="pointer"
              fontWeight="600"
              transition="all 0.2s"
              bg={sortBy === option.value ? "blue.400" : "transparent"}
              color={sortBy === option.value ? "white" : "gray.500"}
              _hover={{
                bg: sortBy === option.value ? "blue.500" : "gray.100",
              }}
              onClick={() => setSortBy(option.value)}
            >
              {option.label}
            </Flex>
          ))}
        </Flex>

        <Flex ml="auto" gap="8px">
          {[
            { label: "High → Low", value: "desc" },
            { label: "Low → High", value: "asc" },
          ].map((option) => (
            <Flex
              key={option.value}
              px="10px"
              py="6px"
              borderRadius="12px"
              fontSize="sm"
              cursor="pointer"
              fontWeight="600"
              transition="all 0.2s"
              bg={sortOrder === option.value ? "purple.400" : "transparent"}
              color={sortOrder === option.value ? "white" : "gray.500"}
              _hover={{
                bg: sortOrder === option.value ? "purple.500" : "gray.100",
              }}
              onClick={() => setSortOrder(option.value)}
            >
              {option.label}
            </Flex>
          ))}
        </Flex>
      </Flex>
      <Grid
        //templateColumns={{ sm: "1fr", md: "1fr 1fr", lg: "2fr 1fr" }}
        templateRows={{ sm: "1fr auto", md: "1fr", lg: "1fr" }}
        gap="24px"
      >
        <Claims
          title={"Current Claims"}
          amount={claims.length}
          captions={[
            "Claim",
            "Quote",
            "Views",
            "Likes",
            "Comments",
            "Interaction",
            "Credibility",
          ]}
          data={sortedClaims}
        />
      </Grid>
    </Flex>
  );
}

export default ClaimCards;
