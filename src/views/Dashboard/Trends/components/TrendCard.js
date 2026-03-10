// Chakra imports
import {
  Button,
  Flex,
  Icon,
  Spacer,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
// Custom components
import Card from "components/Card/Card.js";
import CardBody from "components/Card/CardBody.js";
import React from "react";
// react icons
import { BsArrowRight } from "react-icons/bs";

const TrendCard = ({ title, name, description, image }) => {
  const textColor = useColorModeValue("gray.700", "white");

  return (
    <Card minHeight='290.5px' p='0.85rem' maxWidth='350px'>
      <CardBody w='100%'>
        <Flex flexDirection={{ sm: "row", lg: "column" }} w='100%'>
          <Flex
            //bg='blue.300'
            align='center'
            justify='center'
            borderRadius='15px'
            overflow='hidden'
            width={{ lg: "100%" }}
            minHeight={{ sm: "250px" }}>
            {image}
          </Flex>
          <Spacer />
          <Flex
            flexDirection='column'
            h='100%'
            lineHeight='1.6'
            my='1'
            width={{ lg: "100%" }}>
            <Text fontSize='sm' color='gray.400' fontWeight='bold'>
              {title}
            </Text>
            <Text fontSize='lg' color={textColor} fontWeight='bold' pb='.5rem'>
              {name}
            </Text>
            <Text fontSize='sm' color='gray.400' fontWeight='normal'>
              {description}
            </Text>
            <Spacer />
            <Flex align='center' my='5'>
              <Button
                p='0px'
                variant='no-hover'
                bg='transparent'
                my={{ sm: "1.5rem", lg: "0px" }}>
                <Text
                  fontSize='sm'
                  color={textColor}
                  fontWeight='bold'
                  cursor='pointer'
                  transition='all .5s ease'
                  my={{ sm: "1.5rem", lg: "0px" }}
                  _hover={{ me: "4px" }}>
                  Read more
                </Text>
                <Icon
                  as={BsArrowRight}
                  w='20px'
                  h='20px'
                  fontSize='2xl'
                  transition='all .5s ease'
                  mx='.3rem'
                  cursor='pointer'
                  pt='4px'
                  _hover={{ transform: "translateX(20%)" }}
                />
              </Button>
            </Flex>
          </Flex>
        </Flex>
      </CardBody>
    </Card>
  );
};

export default TrendCard;
