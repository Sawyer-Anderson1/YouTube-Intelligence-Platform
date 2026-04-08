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
        console.log("Raw API response:", res);

        // Process the API data
        const formattedDiscussions = res
          .map((item) => {
            const results = item.result_text || {};
            const firstResult = Object.values(results)?.[0] || {};

            // Only include if result_text has at least one entry
            console.log(results);
            if (Object.keys(results).length === 0) {
              return null;
            }
            return {
              title: Object.keys(results)?.[0] || "Discussion", // use video title
              videoId: firstResult.video_id || "",
              comments: results,
            };
          })
          .filter(Boolean); // remove null entries

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
    <Flex direction="row" flexWrap="wrap" gap="22px" my="60px">
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
