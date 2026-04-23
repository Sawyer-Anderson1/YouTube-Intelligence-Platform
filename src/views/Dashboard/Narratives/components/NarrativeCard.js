import {
  Flex,
  Text,
  useColorModeValue,
  Box,
  Image,
  Divider,
} from "@chakra-ui/react";
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import React from "react";

const NarrativeCard = ({
  title,
  description,
  videoIds,
  views,
  likes,
  comments,
  interaction,
  maxValues,
}) => {
  const textColor = useColorModeValue("gray.700", "white");

  const getWidth = (value, max) => {
    if (max === 0) return "0%";
    return `${(value / max) * 100}%`;
  };

  const getInteractionColor = (value, max) => {
    const percent = max > 0 ? value / max : 0;
    const hue = percent * 120;
    return `hsl(${hue}, 90%, 40%)`;
  };

  const trackBg = useColorModeValue("gray.300", "gray.700");

  const MetricBar = ({ label, value, max, color, isInteraction }) => (
    <Flex direction="column" w="100%" mt="8px">
      <Flex justify="space-between">
        <Text fontSize="xs">{label}</Text>
        <Text fontSize="xs" fontWeight="bold">
          {isInteraction
            ? `${value.toFixed(2)}%`
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
      maxW="350px"
      p="16px"
      transition="all 0.3s ease"
      _hover={{
        transform: "translateY(-3px)",
        boxShadow: "xl",
      }}
    >
      <CardBody>
        <Flex direction="column" h="100%">
          {/* Narrative title */}
          <Text fontSize="md" fontWeight="bold" color={textColor}>
            {title}
          </Text>

          {/* Narrative description */}
          <Text fontSize="sm" color="gray.400" mt="6px">
            {description}
          </Text>

          {/* Metric bars */}
          <Flex direction="column" mt="10px">
            <MetricBar
              label="Views"
              value={views}
              max={maxValues.views}
              color="#369cf0"
            />
            <MetricBar
              label="Likes"
              value={likes}
              max={maxValues.likes}
              color="#ec205d"
            />
            <MetricBar
              label="Comments"
              value={comments}
              max={maxValues.comments}
              color="#f48428"
            />
            <MetricBar
              label="Interaction"
              value={interaction}
              max={maxValues.interaction}
              isInteraction
            />
          </Flex>

          <Divider my="14px" borderColor="gray.400" />

          {/* Video count badge */}
            <Box mb="6px">
              <Box
                display="inline-block"
                bg="green.400"
                color="white"
                px="8px"
                py="2px"
                borderRadius="md"
                fontSize="xs"
                fontWeight="bold"
              >
                {videoIds.length} {videoIds.length === 1 ? "video" : "videos"}
              </Box>
            </Box>
          <Box mb="10px">
            {/* Video thumbnails */}
            <Flex gap="6px">
              {videoIds.map((videoId, index) => (
                <Box
                  key={index}
                  flex="1"
                  borderRadius="md"
                  overflow="hidden"
                  cursor="pointer"
                  onClick={() =>
                    window.open(
                      `https://www.youtube.com/watch?v=${videoId}`,
                      "_blank"
                    )
                  }
                >
                  <Image
                    src={`https://img.youtube.com/vi/${videoId}/mqdefault.jpg`}
                    w="100%"
                    h="80px"
                    objectFit="cover"
                    transition="transform 0.3s ease"
                    _hover={{ transform: "scale(1.06)" }}
                  />
                </Box>
              ))}
            </Flex>
          </Box>
        </Flex>
      </CardBody>
    </Card>
  );
};

export default NarrativeCard;