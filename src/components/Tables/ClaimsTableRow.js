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
  } = props;
  const textColor = useColorModeValue("gray.700", "white");
  const getColor = (value) => {
    const percent = Math.min(value / 8, 1); // normalize 0–5 → 0–1
    const hue = percent * 120;
    return `hsl(${hue}, 90%, 40%)`;
  };

  return (
    <Tr>
      <Td minWidth={{ sm: "250px" }} pl="0px">
        <Flex align="center" py=".8rem" maxWidth="90%" flexWrap="nowrap">
          <Icon
            as={logo}
            h={"24px"}
            w={"24px"}
            pe="5px"
            color={interaction >= 3 ? "teal.300" : "red"}
          />
          <Link href={videoLink} isExternal>
            <Text
              fontSize="md"
              color={textColor}
              fontWeight="bold"
              minWidth="100%"
            >
              {name}
            </Text>
          </Link>
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
    </Tr>
  );
}

export default ClaimsTableRow;
