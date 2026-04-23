import { Flex, Grid, Spinner } from "@chakra-ui/react";
import React, { useEffect, useState } from "react";
import TrendCharts from "./components/TrendCharts";
import getTrends from "../../../API/getTrends";

function Trends() {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchTrends = async () => {
      try {
        const res = await getTrends();

        const rawTrends = res.reduce(
          (acc, item) => ({
            ...acc,
            ...(item.result_text || {}),
          }),
          {},
        );

        const formattedTrends = Object.entries(rawTrends).map(([title, item]) => {
          const views = Number(item.total_view_count) || 0;
          const likes = Number(item.total_like_count) || 0;
          const comments = Number(item.total_comment_count) || 0;

          const interaction =
            views > 0 ? ((likes + comments * 10) / views) * 100 : 0;

          return {
            name: title,
            quote: `"${item.Description}"`,

            views: views.toLocaleString(),
            viewsRaw: views,

            likes: likes.toLocaleString(),
            likesRaw: likes,

            comments: comments.toLocaleString(),
            commentsRaw: comments,

            interaction,

            videoLink: `https://www.youtube.com/watch?v=${item.video_ids?.[0]}`,
          };
        });

        if (!cancelled) setTrends(formattedTrends);
      } catch (err) {
        console.error("Failed to fetch trends:", err);
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
    <Flex flexDirection="column" pt={{ base: "80px", md: "50px" }}>
      <Grid gap="24px">
        <Flex mt="24px">
          <TrendCharts
            title="Current Trends"
            amount={trends.length}
            data={trends}
          />
        </Flex>
      </Grid>
    </Flex>
  );
}

export default Trends;
