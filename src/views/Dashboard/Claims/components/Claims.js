// Chakra imports
import {
  Flex,
  Icon,
  Table,
  Tbody,
  Text,
  Th,
  Thead,
  Tr,
  useColorModeValue,
} from "@chakra-ui/react";
// Custom components
import Card from "components/Card/Card.js";
import CardHeader from "components/Card/CardHeader.js";
import ClaimsTableRow from "components/Tables/ClaimsTableRow";
import React from "react";
import { IoCheckmarkDoneCircleSharp } from "react-icons/io5";
import { Tooltip } from "@chakra-ui/react";
import { InfoOutlineIcon } from "@chakra-ui/icons";
import { Box } from "@chakra-ui/react";

const Claims = ({ title, amount, captions, data }) => {
  const textColor = useColorModeValue("gray.700", "white");
  
  return (
    <Card p='16px' overflowX={{ sm: "scroll", xl: "hidden" }}>
      <CardHeader p='12px 0px 28px 0px'>
        <Flex direction='column'>
          <Text fontSize='lg' color={textColor} fontWeight='bold' pb='.5rem'>
            {title}
          </Text>
          <Flex align='center'>
            <Icon
              as={IoCheckmarkDoneCircleSharp}
              color='teal.300'
              w={4}
              h={4}
              pe='3px'
            />
            <Text fontSize='sm' color='gray.400' fontWeight='normal'>
              <Text fontWeight='bold' as='span'>
                {amount} claims
              </Text>{" "}
              available.
            </Text>
          </Flex>
        </Flex>
      </CardHeader>
      <Table variant='simple' color={textColor}>
        <Thead>
          <Tr my='.8rem' ps='0px'>
            {captions.map((caption, idx) => {
              return (
                <Th color='gray.400' key={idx} ps={idx === 0 ? "0px" : null}>
                  <Flex align="center" gap="6px">
                    {caption}

                    {caption === "Interaction" && (
                      <Tooltip
                        hasArrow
                        shouldWrapChildren
                        placement="top"
                        label={
                          <>
                            <Text fontWeight="bold">How Interaction Score is Measured</Text>
                            <Text fontSize="sm" fontStyle="italic">
                              <br></br>
                              Likes are measured with a value of 1x and comments are measured with a value of 10x. 
                              These combined values are compared against view count for interaction percentage.<br></br>
                              <br></br>
                              Percentages are measured from 0%-8%<br></br>
                              Formula is ((Likes+(Comments*10))/Views)*100
                            </Text>
                          </>
                        }
                        bg="gray.700"
                        color="white"
                        borderRadius="md"
                        p="8px"
                      >
                        <Box>
                          <InfoOutlineIcon cursor="pointer" />
                        </Box>
                      </Tooltip>
                    )}
                  </Flex>
                </Th>
              );
            })}
          </Tr>
        </Thead>
        <Tbody>
          {data && data.length > 0 ? (
            data.map((row) => (
              <ClaimsTableRow
                key={`${row.name}-${row.quote}`}
                name={row.name}
                logo={row.logo}
                quote={row.quote}
                views={row.views}
                likes={row.likes}
                comments={row.comments}
                interaction={row.interaction}
              />
            ))
          ) : (
            <Tr>
              <td colSpan="6">No data available</td>
            </Tr>
          )}
        </Tbody>
      </Table>
    </Card>
  );
};

export default Claims;
