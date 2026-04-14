import {
  Avatar,
  AvatarGroup,
  Flex,
  Icon,
  Progress,
  Td,
  Text,
  Tr,
  useColorModeValue,
  Link,
} from "@chakra-ui/react";
import { WarningIcon } from "@chakra-ui/icons";
import React from "react";

function ClaimsTableRow(props) {
  const {
    logo,
    name,
    quote,
    views,
    likes,
    comments,
    interaction,
    videoLink,
    credibilityScore,
  } = props;
  const textColor = useColorModeValue("gray.700", "white");
  const getColor = (value) => {
    const percent = Math.min(value / 8, 1); // normalize 0–5 → 0–1
    const hue = percent * 120;
    return `hsl(${hue}, 90%, 40%)`;
  };

  return (
    <Tr>
      <Td p="0px" minW="160px" maxW="420px">
        <Flex align="flex-start" gap="12px" py=".8rem">
          {/* Icon column */}
          <Flex mt="2px" align="flex-start">
            <Icon
              as={logo}
              h="24px"
              w="24px"
              color={interaction >= 3 ? "teal.300" : "red.400"}
            />
          </Flex>

          {/* Text column */}
          <Flex direction="column" flex="1" minW="0">
            <Link
              href={videoLink}
              isExternal
              _hover={{ textDecoration: "none" }}
            >
              <Text
                fontSize="md"
                fontWeight="bold"
                color={textColor}
                whiteSpace="normal"
                wordBreak="break-word"
                lineHeight="1.4"
              >
                {name}
              </Text>
            </Link>
          </Flex>
        </Flex>
      </Td>
      <Flex align="center" py=".8rem" minWidth="100%" flexWrap="nowrap">
        <Td>
          <Text
            fontSize="ms"
            color={textColor}
            fontWeight="normal"
            fontStyle="italic"
            pb=".5rem"
          >
            {quote}
          </Text>
        </Td>
      </Flex>
      <Td>
        <Text fontSize="md" color={textColor} fontWeight="bold" pb=".5rem">
          {views}
        </Text>
      </Td>
      <Td>
        <Text fontSize="md" color={textColor} fontWeight="normal" pb=".5rem">
          {likes}
        </Text>
      </Td>
      <Td>
        <Text fontSize="md" color={textColor} fontWeight="normal" pb=".5rem">
          {comments}
        </Text>
      </Td>
      <Td>
        <Flex direction="column">
          <Text
            fontSize="md"
            color="blue.300"
            fontWeight="bold"
            pb=".2rem"
          >{`${interaction.toFixed(2)}%`}</Text>
          <Progress
            size="xs"
            value={interaction * 12.5} // scale 0–8 to 0–100
            borderRadius="15px"
            sx={{
              "& > div": {
                backgroundColor: getColor(interaction),
                transition: "background-color 0.3s ease",
              },
            }}
          />
        </Flex>
      </Td>
      <Td>
        <Flex direction="column" minW="120px">
          {/* Score */}
          <Text
            fontSize="sm"
            fontWeight="bold"
            color={
              props.credibilityScore > 70
                ? "green.400"
                : props.credibilityScore > 40
                ? "yellow.400"
                : "red.400"
            }
          >
            {Math.round(props.credibilityScore)} / 100
          </Text>

          {/* Bar */}
          <Progress
            value={props.credibilityScore}
            size="xs"
            borderRadius="10px"
            sx={{
              "& > div": {
                backgroundColor:
                  props.credibilityScore > 70
                    ? "#38A169"
                    : props.credibilityScore > 40
                    ? "#D69E2E"
                    : "#E53E3E",
              },
            }}
          />

          {/* Label */}
          <Text fontSize="xs" color="gray.400" mt="1">
            {props.credibilityScore > 70
              ? "Strong"
              : props.credibilityScore > 40
              ? "Mixed"
              : "Weak"}
          </Text>
        </Flex>
      </Td>
    </Tr>
  );
}

export default ClaimsTableRow;
