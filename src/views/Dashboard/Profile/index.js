// Chakra imports
import { Flex, Grid, useColorModeValue } from "@chakra-ui/react";
import blankAvatar from "assets/img/avatars/blankavatar.png";
import ProfileBgImage from "assets/img/ProfileBackground.png";
import React from "react";
import { FaCube, FaVideo } from "react-icons/fa";
import { IoBookmark } from "react-icons/io5";
import Header from "./components/Header";

function Profile() {
  // Chakra color mode
  const textColor = useColorModeValue("gray.700", "white");
  const bgProfile = useColorModeValue(
    "hsla(0,0%,100%,.8)",
    "linear-gradient(112.83deg, rgba(255, 255, 255, 0.21) 0%, rgba(255, 255, 255, 0) 110.84%)"
  );

  return (
    <Flex direction='column'>
      <Header
        backgroundHeader={ProfileBgImage}
        backgroundProfile={bgProfile}
        avatarImage={blankAvatar}
        name={"Your Profile"}
        email={"Youtube Intelligence User"}
        tabs={[
          {
            name: "OVERVIEW",
            icon: <FaCube w='100%' h='100%' />,
          },
          {
            name: "FAVORITES",
            icon: <IoBookmark w='100%' h='100%' />,
          },
          {
            name: "PERSONAL WORKS",
            icon: <FaVideo w='100%' h='100%' />,
          },
        ]}
      />

      <text align='center'>
        Your Profile is Currently Inaccessible
      </text>
    </Flex>
  );
}

export default Profile;
