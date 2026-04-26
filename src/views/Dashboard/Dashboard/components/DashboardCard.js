import {
  Flex,
  Text,
  useColorModeValue,
  Box,
  Button,
} from "@chakra-ui/react";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import { useHistory } from "react-router-dom";
import React from "react";

import {
  StatsIcon,
  DocumentIcon,
  FilledChatIcon,
} from "components/Icons/Icons";
import { StarIcon } from "@chakra-ui/icons";

const DashboardCard = ({
  title,
  description,
  count,
  views,
  likes,
  comments,
  interaction,
  videos,
  positive = 0,
  neutral = 0,
  negative = 0,
  maxValues,
  route,
  isDiscussion = false,
}) => {
  const textColor = useColorModeValue("gray.700", "white");
  const trackBg = useColorModeValue("gray.300", "gray.700");

  const history = useHistory();

  const getWidth = (value, max) => {
    if (max === 0) return "0%";
    return `${(value / max) * 100}%`;
  };

  const getInteractionColor = (value, max) => {
    const percent = max > 0 ? value / max : 0;
    const hue = percent * 120;
    return `hsl(${hue}, 90%, 40%)`;
  };

  const getIcon = () => {
    switch (title) {
      case "Claims":
        return <DocumentIcon />;
      case "Trends":
        return <StatsIcon />;
      case "Narratives":
        return <StarIcon />;
      case "Discussions":
        return <FilledChatIcon />;
      default:
        return null;
    }
  };

  const MetricBar = ({ label, value, max, color, isInteraction, isPercent }) => (
    <Flex direction="column" w="100%" mt="8px">
      <Flex justify="space-between">
        <Text fontSize="xs">{label}</Text>
        <Text fontSize="xs" fontWeight="bold">
          {isInteraction || isPercent
            ? `${value.toFixed(1)}%`
            : value.toLocaleString()}
        </Text>
      </Flex>

      <Box w="100%" h="8px" bg={trackBg} borderRadius="md" mt="2px">
        <Box
          h="100%"
          borderRadius="md"
          width={getWidth(value, max)}
          bg={
            isInteraction
              ? getInteractionColor(value, max)
              : color
          }
        />
      </Box>
    </Flex>
  );

  return (
    <Card
      minH="320px"
      p="18px"
      cursor="pointer"
      onClick={() => history.push(route)}
      transition="all 0.3s ease"
      _hover={{
        transform: "translateY(-4px)",
        boxShadow: "xl",
      }}
    >
      <CardBody>
        <Flex direction="column" h="100%" justify="space-between">
          <Box>
            <Flex justify="space-between" align="center">
              <Text fontSize="lg" fontWeight="bold" color={textColor}>
                {title}
              </Text>

              <Box fontSize="20px" color="blue.300">
                {getIcon()}
              </Box>
            </Flex>

            <Text fontSize="sm" color="gray.400" mt="6px">
              {description}
            </Text>

            <Text mt="10px" fontSize="sm">
              Across <b>{count}</b> {title}:
            </Text>

            <Flex direction="column" mt="8px">
              {isDiscussion ? (
                <>
                  <MetricBar label="Comments" value={comments} max={maxValues.discussionComments} color="#f48428" />
                  <MetricBar label="Comment Likes" value={likes} max={maxValues.discussionLikes} color="#ec205d" />
                  <MetricBar label="Positive Sentiments" value={positive} max={maxValues.positive} color="#22c55e" isPercent />
                  <MetricBar label="Neutral Sentiments" value={neutral} max={maxValues.neutral} color="#a0aec0" isPercent />
                  <MetricBar label="Negative Sentiments" value={negative} max={maxValues.negative} color="#ef4444" isPercent />
                </>
              ) : (
                <>
                  <MetricBar label="Views" value={views} max={maxValues.views} color="#369cf0" />
                  <MetricBar label="Likes" value={likes} max={maxValues.likes} color="#ec205d" />
                  <MetricBar label="Comments" value={comments} max={maxValues.comments} color="#f48428" />
                  <MetricBar label="Interaction" value={interaction} max={maxValues.interaction} isInteraction />
                  <MetricBar label="Videos" value={videos} max={maxValues.videos} color="#7C3AED" />
                </>
              )}
            </Flex>
          </Box>

          <Button
            mt="14px"
            size="sm"
            colorScheme="purple"
            alignSelf="flex-end"
            onClick={(e) => {
              e.stopPropagation();
              history.push(route);
            }}
          >
            Explore {title}
          </Button>
        </Flex>
      </CardBody>
    </Card>
  );
};

export default DashboardCard;