import { Flex, Icon, Text, useColorModeValue } from "@chakra-ui/react";
import Card from "components/Card/Card.js";
import CardHeader from "components/Card/CardHeader.js";
import React from "react";
import BarList from "components/Charts/BarList";
import { IoCheckmarkDoneCircleSharp } from "react-icons/io5";

const TrendCharts = ({ title, amount, data }) => {
  const textColor = useColorModeValue("gray.700", "white");

  return (
    <Card p="16px">
      <CardHeader p="12px 0px 20px 0px">
        <Flex direction="column">
          <Text fontSize="lg" color={textColor} fontWeight="bold" pb=".5rem">
            {title}
          </Text>
          <Flex align="center">
            <Icon
              as={IoCheckmarkDoneCircleSharp}
              color="teal.300"
              w={4}
              h={4}
              pe="3px"
            />
            <Text fontSize="sm" color="gray.400" fontWeight="normal">
              <Text fontWeight="bold" as="span">
                {amount} trends
              </Text>{" "}
              available.
            </Text>
          </Flex>
        </Flex>
      </CardHeader>

      <BarList data={data} />
    </Card>
  );
};

export default TrendCharts;