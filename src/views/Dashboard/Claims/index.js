// Chakra imports
import {
  Flex,
  Grid,
  Image,
  SimpleGrid,
  useColorModeValue,
} from "@chakra-ui/react";
import React from "react";
import ClaimCard from "./components/ClaimCard";

function ClaimCards() {
  return (
    <Flex direction='column'>
      <Grid templateColumns={{ sm: "1fr", xl: "repeat(4, 1fr)" }} my='60px' gap='22px'>
        <ClaimCard
          title={"New Claim"}
          name={"AI Will Replace Human Workers"}
          description={
            "The speaker suggests that agents can do tasks more efficiently and accurately than humans, potentially leading to job displacement"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <ClaimCard
          title={"New Claim"}
          name={"80% of Ape Developers May Disappear"}
          description={
            "Another speaker mentions that the rise of agents could lead to the obsolescence of apes in software development, with only a small percentage adapting to become API-focused"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
      </Grid>
    </Flex>
  );
}

export default ClaimCards;

/*
<ClaimCard
          title={"New Claim"}
          name={"This is the Placeholder Name of the Claim"}
          description={
            "This is the Placeholder Description of the Given Claim | [source]"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <ClaimCard
          title={"New Claim"}
          name={"This is the Placeholder Name of the Claim"}
          description={
            "This is the Placeholder Description of the Given Claim | [source]"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
*/