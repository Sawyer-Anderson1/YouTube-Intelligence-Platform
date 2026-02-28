// Chakra imports
import {
  Flex,
  Grid,
  Image,
  SimpleGrid,
  useColorModeValue,
} from "@chakra-ui/react";
import React from "react";
import TrendCard from "./components/TrendCard";

function TrendCards() {
  return (
    <Flex direction='column'>
      <Grid templateColumns={{ sm: "1fr", xl: "repeat(4, 1fr)" }} my='60px' gap='22px'>
        <TrendCard
          title={"New Trend"}
          name={"Rise of New Business Models and Services"}
          description={
            "As agents become more prevalent, companies are exploring new ways to monetize their capabilities, including offering solutions for tasks like data management and problem-solving"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <TrendCard
          title={"New Trend"}
          name={"Growing Excitement and Optimism about AI"}
          description={
            "The speakers express enthusiasm for the potential benefits of AI, including increased productivity, creativity, and accessibility"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <TrendCard
          title={"New Trend"}
          name={"Shift from Human-Centric to Agent-Centric Interactions"}
          description={
            "The transcripts highlight the increasing use of agents in everyday life, such as accessing websites, sending messages, and completing tasks"
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

export default TrendCards;

/*
<TrendCard
          title={"New Trend"}
          name={"This is the Placeholder Name of the Trend"}
          description={
            "This is the Placeholder Description of the Given Trend | [source]"
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