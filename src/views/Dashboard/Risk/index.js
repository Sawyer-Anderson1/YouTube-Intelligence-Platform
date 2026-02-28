// Chakra imports
import {
  Flex,
  Grid,
  Image,
  SimpleGrid,
  useColorModeValue,
} from "@chakra-ui/react";
import React from "react";
import RiskCard from "./components/RiskCard";

function RiskCards() {
  return (
    <Flex direction='column'>
      <Grid templateColumns={{ sm: "1fr", xl: "repeat(4, 1fr)" }} my='60px' gap='22px'>
        <RiskCard
          title={"New Risk"}
          name={"This is the Placeholder Name of the Risk"}
          description={
            "This is the Placeholder Description of the Given Risk | [source]"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <RiskCard
          title={"New Risk"}
          name={"This is the Placeholder Name of the Risk"}
          description={
            "This is the Placeholder Description of the Given Risk | [source]"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <RiskCard
          title={"New Risk"}
          name={"This is the Placeholder Name of the Risk"}
          description={
            "This is the Placeholder Description of the Given Risk | [source]"
          }
          image={
            <Image
              //src={}
              alt='[image]'
              minWidth={{ md: "300px", lg: "auto" }}
            />
          }
        />
        <RiskCard
          title={"New Risk"}
          name={"This is the Placeholder Name of the Risk"}
          description={
            "This is the Placeholder Description of the Given Risk | [source]"
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

export default RiskCards;
