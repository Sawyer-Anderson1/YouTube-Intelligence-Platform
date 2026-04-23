import { Flex, Icon, Image, Text, Box, VStack } from "@chakra-ui/react";
import React, { useState } from "react";
import { BsArrowRight } from "react-icons/bs";
import { GreenArrowUpIcon, RedArrowDownIcon } from "components/Icons/Icons.js";

const DiscussionCard = ({ title, videoId, comments }) => {
  const [showComments, setShowComments] = useState(false);

  const videoLink = `https://www.youtube.com/watch?v=${videoId}`;

  // Capitalize first letter
  const capitalizeFirst = (str = "") =>
    str.charAt(0).toUpperCase() + str.slice(1);

  // Get arrow based on sentiment
  const getSentimentIcon = (sentiment) => {
    if (sentiment === "positive")
      return { icon: GreenArrowUpIcon, color: "green.300" };
    if (sentiment === "negative")
      return { icon: RedArrowDownIcon, color: "red.400" };
    return { icon: BsArrowRight, color: "gray.400" }; // neutral → gray arrow
  };

  const [expandedComments, setExpandedComments] = useState({});
  const toggleComment = (idx) => {
    setExpandedComments((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  return (
    <Box
      borderWidth="1px"
      borderRadius="md"
      overflow="hidden"
      minWidth="300px"
      maxWidth="350px"
      p="4"
    >
      {/* Video Thumbnail */}
      <a href={videoLink} target="_blank" rel="noopener noreferrer">
        <Image
          src={`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`}
          alt={title}
          borderRadius="md"
          mb="3"
        />
      </a>

      <Box cursor="pointer" onClick={() => setShowComments((prev) => !prev)}>
        <Text fontWeight="bold" mb="1">
          {title}
        </Text>

        <Flex align="center" justify="space-between">
          <Text fontSize="sm" color="gray.500">
            {Object.keys(comments).length || 0} comments
          </Text>

          <Icon
            as={BsArrowRight}
            transform={showComments ? "rotate(90deg)" : "rotate(0deg)"}
            transition="transform 0.2s"
          />
        </Flex>
      </Box>

      {/* Comments */}
      {showComments && Object.keys(comments).length > 0 && (
        <VStack mt="3" spacing="2" align="start">
          {Object.values(comments).map((c, idx) => {
            const { icon: SentimentIcon, color } = getSentimentIcon(
              c.sentiment_class,
            );

            return (
              <Box
                key={idx}
                p="2"
                bg="black"
                borderRadius="md"
                w="100%"
                fontSize="sm"
              >
                <Flex justify="space-between" align="center" mb="1">

                  <Icon as={SentimentIcon} w={5} h={5} color={color} />
                </Flex>

                <Box mb="1">
                  <Text color="white">
                    {expandedComments[idx]
                      ? capitalizeFirst(c.Quote)
                      : capitalizeFirst(c.Quote).length > 120
                      ? capitalizeFirst(c.Quote).slice(0, 120) + "..."
                      : capitalizeFirst(c.Quote)}
                  </Text>

                  {c.Quote.length > 120 && (
                    <Text
                      fontSize="xs"
                      color="blue.300"
                      cursor="pointer"
                      onClick={() => toggleComment(idx)}
                    >
                      {expandedComments[idx] ? "Collapse" : "Read more"}
                    </Text>
                  )}
                </Box>

                <Text fontSize="xs" color="gray.400">
                  Likes: {c.like_count}
                </Text>
              </Box>
            );
          })}
        </VStack>
      )}
    </Box>
  );
};

export default DiscussionCard;
