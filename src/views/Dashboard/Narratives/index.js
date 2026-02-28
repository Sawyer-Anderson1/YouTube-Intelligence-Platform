// Chakra imports
import {
  Flex,
  Grid,
  Image,
  SimpleGrid,
  useColorModeValue,
} from "@chakra-ui/react";
import React from "react";
import NarrativeCard from "./components/NarrativeCard";

function NarrativeCards() {
  return (
    <Flex direction='column'>
      <Grid templateColumns={{ sm: "1fr", xl: "repeat(4, 1fr)" }} my='60px' gap='22px'>
        <NarrativeCard
          title={"New Narrative"}
          name={"The 'Agent-First' Revolution"}
          description={
            "The speakers describe the emergence of a new paradigm where agents are increasingly used as the primary interface between humans and software systems"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <NarrativeCard
          title={"New Narrative"}
          name={"Fears About Job Displacement and Social Change"}
          description={
            "The transcripts touch on concerns about the potential impact of AI on employment, particularly in industries where human workers have traditionally been the norm"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <NarrativeCard
          title={"New Narrative"}
          name={"The 'Post-Human' Era"}
          description={
            "Some speakers hint at a future where humans are no longer the primary focus of software development, instead working closely with agents to achieve greater productivity and efficiency"
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

export default NarrativeCards;

/*
<NarrativeCard
          title={"New Narrative"}
          name={"This is the Placeholder Name of the Narrative"}
          description={
            "This is the Placeholder Description of the Given Narrative | [source]"
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