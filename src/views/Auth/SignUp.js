import { Link as RouterLink } from "react-router-dom";
// Chakra imports
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  HStack,
  Icon,
  Input,
  Link,
  Switch,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
// Assets
import BgSignUp from "assets/img/BgSignUp.png";
import React from "react";
import { useState } from "react";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { auth } from "../../firebaseConfig";

function SignUp() {
  const titleColor = useColorModeValue("blue.300", "blue.200");
  const textColor = useColorModeValue("gray.700", "white");
  const bgColor = useColorModeValue("white", "gray.700");
  const bgIcons = useColorModeValue("blue.200", "rgba(255, 255, 255, 0.5)");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const handleSignUp = async () => {
    try {
      if (!email || !password) {
        alert("Please fill all fields");
        return;
      }

      if (password.length < 6) {
        alert("Password must be at least 6 characters");
        return;
      }

      const userCredential = await createUserWithEmailAndPassword(
        auth,
        email,
        password,
      );

      console.log("User created:", userCredential.user);
    } catch (error) {
      if (error.code === "auth/email-already-in-use") {
        alert("Email already exists");
      } else {
        alert(error.message);
      }
    }
  };
  return (
    <Flex
      direction="column"
      alignSelf="center"
      justifySelf="center"
      overflow="hidden"
    >
      <Box
        position="absolute"
        minH={{ base: "70vh", md: "50vh" }}
        w={{ md: "calc(100vw - 50px)" }}
        borderRadius={{ md: "15px" }}
        left="0"
        right="0"
        bgRepeat="no-repeat"
        overflow="hidden"
        zIndex="-1"
        top="0"
        bgImage={BgSignUp}
        bgSize="cover"
        mx={{ md: "auto" }}
        mt={{ md: "14px" }}
      ></Box>
      <Flex
        direction="column"
        textAlign="center"
        justifyContent="center"
        align="center"
        mt="6.5rem"
        mb="30px"
      >
        <Text fontSize="4xl" color="white" fontWeight="bold">
          Welcome to Youtube Intelligence!
        </Text>
        <Text fontSize="2xl" color="white">
          Create an account to get started.
        </Text>
      </Flex>
      <Flex alignItems="center" justifyContent="center" mb="60px" mt="20px">
        <Flex
          direction="column"
          w="445px"
          background="transparent"
          borderRadius="15px"
          p="40px"
          mx={{ base: "100px" }}
          bg={bgColor}
          boxShadow="0 20px 27px 0 rgb(0 0 0 / 5%)"
        >
          <FormControl>
            <FormLabel ms="4px" fontSize="sm" fontWeight="normal">
              Name
            </FormLabel>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              fontSize="sm"
              ms="4px"
              borderRadius="15px"
              type="text"
              placeholder="Your full name"
              mb="24px"
              size="lg"
            />
            <FormLabel ms="4px" fontSize="sm" fontWeight="normal">
              Email
            </FormLabel>
            <Input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              fontSize="sm"
              ms="4px"
              borderRadius="15px"
              type="email"
              placeholder="Your email address"
              mb="24px"
              size="lg"
            />
            <FormLabel ms="4px" fontSize="sm" fontWeight="normal">
              Password
            </FormLabel>
            <Input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fontSize="sm"
              ms="4px"
              borderRadius="15px"
              type="password"
              placeholder="Your password"
              mb="24px"
              size="lg"
            />
            <Button
              onClick={handleSignUp}
              type="submit"
              bg="blue.300"
              fontSize="10px"
              color="white"
              fontWeight="bold"
              w="100%"
              h="45"
              mb="24px"
              _hover={{
                bg: "blue.600",
              }}
              _active={{
                bg: "blue.700",
              }}
            >
              SIGN UP
            </Button>
          </FormControl>
          <Flex
            flexDirection="column"
            justifyContent="center"
            alignItems="center"
            maxW="100%"
            mt="0px"
          >
            <Text color={textColor} fontWeight="medium">
              Already have an account?
              <Link
                as={RouterLink}
                color={titleColor}
                ms="5px"
                to="/auth/signin"
                fontWeight="bold"
              >
                Sign In
              </Link>
            </Text>
          </Flex>
        </Flex>
      </Flex>
    </Flex>
  );
}

export default SignUp;
