import {
  Grid,
  Flex,
  Text,
  Spinner,
  Box,
  Skeleton,
} from "@chakra-ui/react";
import React, { useEffect, useState } from "react";

import DashboardCard from "./components/DashboardCard";

import getClaims from "../../../API/getClaims";
import getTrends from "../../../API/getTrends";
import getNarratives from "../../../API/getNarratives";
import getComments from "../../../API/getComments";

function Dashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchAll = async () => {
      try {
        const [claimsRes, trendsRes, narrativesRes, commentsRes] =
          await Promise.all([
            getClaims(),
            getTrends(),
            getNarratives(),
            getComments(),
          ]);

        const formatData = (raw) => {
          const items = Object.values(raw || {});

          let views = 0;
          let likes = 0;
          let comments = 0;
          let interaction = 0;
          let videos = 0;

          items.forEach((item) => {
            const v = Number(item.total_view_count) || 0;
            const l = Number(item.total_like_count) || 0;
            const c = Number(item.total_comment_count) || 0;

            views += v;
            likes += l;
            comments += c;
            interaction += v > 0 ? ((l + c * 10) / v) * 100 : 0;
            videos += item.video_ids?.length || 0;
          });

          return {
            count: items.length,
            views,
            likes,
            comments,
            interaction,
            videos,
          };
        };

        const formatClaimsData = (claimsRes) => {
          const rawClaims = claimsRes.reduce(
            (acc, item) => ({
              ...acc,
              ...(item.result_text || {}),
            }),
            {}
          );

          const items = Object.values(rawClaims);

          let views = 0;
          let likes = 0;
          let comments = 0;
          let interaction = 0;
          let videos = 0;

          items.forEach((claim) => {
            const v = Number(claim.view_count) || 0;
            const l = Number(claim.like_count) || 0;
            const c = Number(claim.comment_count) || 0;

            views += v;
            likes += l;
            comments += c;
            interaction += v > 0 ? ((l + c * 10) / v) * 100 : 0;

            // Each claim has ONE video_id
            if (claim.video_id) videos += 1;
          });

          return {
            count: items.length,
            views,
            likes,
            comments,
            interaction,
            videos,
          };
        };

        const formatDiscussionData = (commentsRes) => {
          let totalComments = 0;
          let totalLikes = 0;

          let positive = 0;
          let neutral = 0;
          let negative = 0;

          commentsRes.forEach((item) => {
            const results = item.result_text || {};

            Object.values(results).forEach((comment) => {
              totalComments += 1;
              totalLikes += Number(comment.like_count) || 0;

              switch (comment.sentiment_class) {
                case "positive":
                  positive += 1;
                  break;
                case "neutral":
                  neutral += 1;
                  break;
                case "negative":
                  negative += 1;
                  break;
                default:
                  break;
              }
            });
          });

          const totalSentiment = positive + neutral + negative;

          const toPercent = (val) =>
            totalSentiment > 0 ? (val / totalSentiment) * 100 : 0;

          return {
            count: totalComments,
            comments: totalComments,
            likes: totalLikes,
            positive: toPercent(positive),
            neutral: toPercent(neutral),
            negative: toPercent(negative),
          };
        };

        const mergeResults = (res) =>
          res.reduce(
            (acc, item) => ({
              ...acc,
              ...(item.result_text || {}),
            }),
            {}
          );

        const claims = formatClaimsData(claimsRes);
        const trends = formatData(mergeResults(trendsRes));
        const narratives = formatData(mergeResults(narrativesRes));
        const discussions = formatDiscussionData(commentsRes);

        const maxValues = {
          views: Math.max(claims.views, trends.views, narratives.views),
          likes: Math.max(claims.likes, trends.likes, narratives.likes),
          comments: Math.max(claims.comments, trends.comments, narratives.comments),
          interaction: Math.max(claims.interaction, trends.interaction, narratives.interaction),
          videos: Math.max(claims.videos, trends.videos, narratives.videos),

          discussionComments: discussions.comments,
          discussionLikes: discussions.likes,
          positive: 100,
          neutral: 100,
          negative: 100,
        };

        if (!cancelled) {
          setData({
            claims,
            trends,
            narratives,
            discussions,
            maxValues,
          });
        }
      } catch (err) {
        console.error(err);
      }
    };

    fetchAll();
    return () => (cancelled = true);
  }, []);

  if (!data) return (
    <Box pt="80px" pr="80px">
      <Flex
        direction="column"
        align="center"
        textAlign="center"
        mb="40px"
      >
        <Text fontSize="3xl" fontWeight="bold">
          AI Insights Dashboard
        </Text>

        <Text
          mt="10px"
          maxW="700px"
          color="gray.500"
          fontSize="17px"
        >
          Analyzes data from the YouTube API, through the use of LLMs,
          to generate insights about claims, trends, narratives, and
          discussions on relevant topics about Artificial Intelligence.
        </Text>
      </Flex>

      {/* Dashboard cards */}
      <Grid
        templateColumns="repeat(auto-fit, minmax(200px, 1fr))"
        gap="24px"
      >
        <Skeleton
          borderRadius="lg"
          startColor="gray.700"
          endColor="gray.600"
          minH="380px"
        />
        <Skeleton
          borderRadius="lg"
          startColor="gray.700"
          endColor="gray.600"
          minH="380px"
        />
        <Skeleton
          borderRadius="lg"
          startColor="gray.700"
          endColor="gray.600"
          minH="380px"
        />
        <Skeleton
          borderRadius="lg"
          startColor="gray.700"
          endColor="gray.600"
          minH="380px"
        />
      </Grid>
    </Box>
  );

  return (
    <Box pt="80px" pr="80px">
      <Flex
        direction="column"
        align="center"
        textAlign="center"
        mb="40px"
      >
        <Text fontSize="3xl" fontWeight="bold">
          AI Insights Dashboard
        </Text>

        <Text
          mt="10px"
          maxW="700px"
          color="gray.500"
          fontSize="17px"
        >
          Analyzes data from the YouTube API, through the use of LLMs,
          to generate insights about claims, trends, narratives, and
          discussions on relevant topics about Artificial Intelligence.
        </Text>
      </Flex>

      {/* Dashboard cards */}
      <Grid
        templateColumns="repeat(auto-fit, minmax(200px, 1fr))"
        gap="24px"
      >
        <DashboardCard
          title="Claims"
          description="Key statements and assertions extracted from AI-related content."
          {...data.claims}
          maxValues={data.maxValues}
          route="/admin/claims"
        />

        <DashboardCard
          title="Trends"
          description="Emerging patterns and recurring topics gaining traction in the AI."
          {...data.trends}
          maxValues={data.maxValues}
          route="/admin/trends"
        />

        <DashboardCard
          title="Narratives"
          description="Broader storylines shaping the conversation around AI."
          {...data.narratives}
          maxValues={data.maxValues}
          route="/admin/narratives"
        />

        <DashboardCard
            title="Discussions"
            description="Breakdown of audiences within comment sections on AI videos."
            {...data.discussions}
            maxValues={data.maxValues}
            route="/admin/discussions"
            isDiscussion
          />
      </Grid>
    </Box>
  );
}

export default Dashboard;