import React from "react";
import { Link as RouterLink } from "react-router-dom";
// Chakra imports
import {
  Box,
  Flex,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Link,
  Switch,
  Text,
  useColorModeValue,
  Icon,
  HStack,
} from "@chakra-ui/react";
// Assets
import signInImage from "assets/img/signInImage.png";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../../firebaseConfig";
import { useState } from "react";
import { signInWithEmailAndPassword } from "firebase/auth";
import { FaGoogle, FaFacebook, FaApple } from "react-icons/fa";

function SignIn() {
  const bgIcons = useColorModeValue("blue.200", "rgba(255, 255, 255, 0.5)");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const handleSignIn = async () => {
    try {
      if (!email || !password) {
        alert("Enter email and password");
        return;
      }

      const userCredential = await signInWithEmailAndPassword(
        auth,
        email,
        password,
      );

      console.log("Logged in:", userCredential.user);
    } catch (error) {
      if (error.code === "auth/user-not-found") {
        alert("User not found");
      } else if (error.code === "auth/wrong-password") {
        alert("Wrong password");
      } else {
        alert(error.message);
      }
    }
  };
  // Chakra color mode
  const handleGoogleSignIn = async () => {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;

      console.log("User:", user);
      // You can store user info or redirect here
    } catch (error) {
      console.error("Error signing in:", error);
    }
  };

  const titleColor = useColorModeValue("blue.300", "blue.200");
  const textColor = useColorModeValue("gray.400", "white");
  return (
    <Flex position="relative" mb="40px" mt="150px">
      <Flex
        h={{ sm: "initial", md: "75vh", lg: "85vh" }}
        w="100%"
        maxW="1044px"
        mx="auto"
        justifyContent="space-between"
        mb="30px"
        pt={{ sm: "100px", md: "0px" }}
      >
        <Flex
          alignItems="center"
          justifyContent="start"
          style={{ userSelect: "none" }}
          w={{ base: "100%", md: "50%", lg: "42%" }}
        >
          <Flex
            direction="column"
            w="100%"
            background="transparent"
            mt={{ md: "150px", lg: "80px" }}
          >
            <Heading color={titleColor} fontSize="32px" mb="10px">
              Welcome Back
            </Heading>
            <Text
              mb="36px"
              ms="4px"
              color={textColor}
              fontWeight="bold"
              fontSize="14px"
            >
              Enter your email and password to sign in
            </Text>
            <FormControl>
              <FormLabel ms="4px" fontSize="sm" fontWeight="normal">
                Email
              </FormLabel>
              <Input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                borderRadius="15px"
                mb="24px"
                fontSize="sm"
                type="text"
                placeholder="Your email adress"
                size="lg"
              />
              <FormLabel ms="4px" fontSize="sm" fontWeight="normal">
                Password
              </FormLabel>
              <Input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                borderRadius="15px"
                mb="36px"
                fontSize="sm"
                type="password"
                placeholder="Your password"
                size="lg"
              />
              <Button
                onClick={handleSignIn}
                fontSize="10px"
                type="submit"
                bg="teal.300"
                w="100%"
                h="45"
                mb="20px"
                color="white"
                mt="20px"
                _hover={{
                  bg: "blue.200",
                }}
                _active={{
                  bg: "blue.400",
                }}
              >
                SIGN IN
              </Button>
              <Text
                fontSize="lg"
                color="gray.400"
                fontWeight="bold"
                textAlign="center"
                mb="22px"
              >
                or
              </Text>
              <HStack spacing="15px" justify="center" mb="22px">
                <Flex
                  onClick={handleGoogleSignIn}
                  justify="center"
                  align="center"
                  w="75px"
                  h="75px"
                  borderRadius="15px"
                  border="1px solid lightgray"
                  cursor="pointer"
                  transition="all .25s ease"
                  _hover={{ filter: "brightness(120%)", bg: bgIcons }}
                >
                  <Icon as={FaGoogle} w="30px" h="30px" />
                </Flex>
              </HStack>
            </FormControl>
            <Flex
              flexDirection="column"
              justifyContent="center"
              alignItems="center"
              maxW="100%"
              mt="0px"
            >
              <Text color={textColor} fontWeight="medium">
                Don't have an account?
                <Link
                  as={RouterLink}
                  to="/auth/signup"
                  color={titleColor}
                  ms="5px"
                  fontWeight="bold"
                >
                  Sign Up
                </Link>
              </Text>
            </Flex>
          </Flex>
        </Flex>
        <Box
          display={{ base: "none", md: "block" }}
          overflowX="hidden"
          h="100%"
          w="40vw"
          position="absolute"
          right="0px"
        >
          <Box
            bgImage={signInImage}
            w="100%"
            h="100%"
            bgSize="cover"
            bgPosition="50%"
            position="absolute"
            borderBottomLeftRadius="20px"
          ></Box>
        </Box>
      </Flex>
    </Flex>
  );
}

export default SignIn;
