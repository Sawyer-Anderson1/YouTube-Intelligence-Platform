import { Flex, Spinner } from "@chakra-ui/react";
import React, { useState, useEffect } from "react";
import DiscussionCard from "./components/DiscussionCard";
import getComments from "../../../API/getComments";

function DiscussionPage() {
  const [discussions, setDiscussions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      try {
        const res = await getComments();

        // Process the API data
        const formattedDiscussions = res
          .map((item) => {
            const results = item.result_text || {};

            // skip if raw_response exists
            if (results.raw_response) {
              return null;
            }

            const firstResult = Object.values(results)?.[0] || {};

            // Only include if result_text has at least one valid entry
            if (Object.keys(results).length === 0) {
              return null;
            }

            return {
              title: Object.keys(results)?.[0] || "Discussion",
              videoId: firstResult.video_id || "",
              comments: results,
            };
          })
          .filter(Boolean);

        if (!cancelled) setDiscussions(formattedDiscussions);
      } catch (error) {
        console.error("Failed to fetch discussions:", error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchData();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Spinner />;

  return (
    <Flex direction="row" flexWrap="wrap" gap="22px" my="60px" pt="6px">
      {discussions.length > 0 ? (
        discussions.map((d, index) => (
          <DiscussionCard
            key={index}
            title={d.title}
            videoId={d.videoId}
            comments={d.comments}
          />
        ))
      ) : (
        <p>No discussions available</p>
      )}
    </Flex>
  );
}

export default DiscussionPage;
