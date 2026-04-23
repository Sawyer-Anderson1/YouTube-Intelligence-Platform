import {
  Grid,
  Spinner,
  Flex,
  Text,
  Select,
} from "@chakra-ui/react";
import React, { useState, useEffect, useMemo } from "react";
import NarrativeCard from "./components/NarrativeCard";
import getNarratives from "../../../API/getNarratives";

// Sorting metric options
const metricOptions = [
  { label: "Views", value: "views" },
  { label: "Likes", value: "likes" },
  { label: "Comments", value: "comments" },
  { label: "Interaction", value: "interaction" },
];

function NarrativeCards() {
  const [narratives, setNarratives] = useState({
    data: [],
    maxValues: {
      views: 0,
      likes: 0,
      comments: 0,
      interaction: 0,
    },
  });

  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState("views");
  const [sortOrder, setSortOrder] = useState("desc");

  useEffect(() => {
    let cancelled = false;

    const fetchNarratives = async () => {
      try {
        const res = await getNarratives();

        const rawNarratives = res?.[0]?.result_text || {};

        const formattedNarratives = Object.entries(rawNarratives).map(
          ([title, item]) => {
            const views = Number(item.total_view_count) || 0;
            const likes = Number(item.total_like_count) || 0;
            const comments = Number(item.total_comment_count) || 0;

            const interaction =
              views > 0 ? ((likes + comments * 10) / views) * 100 : 0;

            return {
              title,
              description: `"${item.Description}"`,
              videoCount: item.video_ids?.length || 0,
              videoIds: item.video_ids || [],
              views,
              likes,
              comments,
              interaction,
            };
          }
        );

        const maxValues = {
          views: Math.max(...formattedNarratives.map((i) => i.views), 0),
          likes: Math.max(...formattedNarratives.map((i) => i.likes), 0),
          comments: Math.max(...formattedNarratives.map((i) => i.comments), 0),
          interaction: Math.max(
            ...formattedNarratives.map((i) => i.interaction),
            0
          ),
        };

        if (!cancelled) {
          setNarratives({
            data: formattedNarratives,
            maxValues,
          });
        }
      } catch (error) {
        console.error("Failed to fetch narratives:", error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchNarratives();
    return () => (cancelled = true);
  }, []);

  // Sorting logic
  const sortedNarratives = useMemo(() => {
    if (!narratives.data) return [];

    const sorted = [...narratives.data].sort(
      (a, b) => b[metric] - a[metric]
    );

    return sortOrder === "asc" ? sorted.reverse() : sorted;
  }, [narratives, metric, sortOrder]);

  if (loading) return <Spinner />;

  return (
    <>
      {/* Sorting options */}
      <Flex mb="20px" align="center" gap="10px" wrap="wrap" pt="65px">
        <Text fontWeight="bold">Sort By:</Text>

        <Select
          w="180px"
          value={metric}
          onChange={(e) => setMetric(e.target.value)}
        >
          {metricOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </Select>

        <Flex gap="6px" ml="10px">
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
        templateColumns="repeat(auto-fill, minmax(300px, 1fr))"
        gap="22px"
        my="20px"
      >
        {sortedNarratives.map((narrative, index) => (
          <NarrativeCard
            key={index}
            {...narrative}
            maxValues={narratives.maxValues}
          />
        ))}
      </Grid>
    </>
  );
}

export default NarrativeCards;