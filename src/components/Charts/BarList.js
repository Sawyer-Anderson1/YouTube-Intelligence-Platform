import React, { useState, useMemo } from "react";
import Card from "components/Card/Card";
import Chart from "react-apexcharts";
import {
  useColorModeValue,
  Select,
  Flex,
  Text,
  Tooltip,
  Box,
  Divider,
} from "@chakra-ui/react";
import { InfoOutlineIcon } from "@chakra-ui/icons";

const metricOptions = [
  { label: "Views", value: "viewsRaw" },
  { label: "Likes", value: "likesRaw" },
  { label: "Comments", value: "commentsRaw" },
  { label: "Interaction", value: "interaction" },
];

const BarList = ({ data }) => {
  const [metric, setMetric] = useState("viewsRaw");
  const [sortOrder, setSortOrder] = useState("desc");

  const axisColor = useColorModeValue("#1A202C", "#FFFFFF");

  const processedData = useMemo(() => {
    const mapped = data.map((item) => ({
      ...item,
      likesRaw: Number(item.likes.toString().replace(/,/g, "")),
      commentsRaw: Number(item.comments.toString().replace(/,/g, "")),
    }));

    return mapped.sort((a, b) => {
      const diff = a[metric] - b[metric];
      return sortOrder === "asc" ? diff : -diff;
    });
  }, [data, metric, sortOrder]);

  const rawValues = processedData.map((item) => item[metric]);
  const maxRawValue = Math.max(...rawValues, 0);

  const minBar = maxRawValue * 0.03;

  const values = rawValues.map((v) => (v === 0 ? 0 : Math.max(v, minBar)));
  const labels = processedData.map((_, i) => `#${i + 1}`);
  const maxValue = Math.max(...values, 0);

  const chartData = [
    {
      name: metric,
      data: values,
    },
  ];

  const getInteractionColor = (value, max) => {
    const percent = max > 0 ? value / max : 0; // normalize to dataset
    const hue = percent * 120; // 0 = red, 120 = green
    return `hsl(${hue}, 90%, 40%)`;
  };

  const maxInteraction = Math.max(
    ...processedData.map((item) => item.interaction),
    0
  );

  const chartOptions = {
    chart: {
    type: "bar",
    toolbar: { show: false },

    events: { 
      dataPointSelection: (event, chartContext, config) => { 
        const item = processedData[config.dataPointIndex]; 
          if (item?.videoLink) { 
            window.open(item.videoLink, "_blank"); 
          } 
        }, 
      }, 
    },

    legend: {
      show: false,
    },

    tooltip: {
      theme: "dark",
      followCursor: true,
      intersect: false,
      shared: false,
      translateY: -10,

      custom: function ({ dataPointIndex }) {
        const item = processedData[dataPointIndex];
        if (!item) return "";

        return `
          <div class="custom-tooltip" style="
            padding:12px;
            max-width:320px;
            white-space:normal;
            word-wrap:break-word;
          ">
            <b>${item.name}</b><br/>
            <i>${item.quote}</i><br/><br/>
            Total Views: <b>${item.views}</b><br/>
            Total Likes: <b>${item.likes}</b><br/>
            Total Comments: <b>${item.comments}</b><br/>
            Interaction Score: <b>${item.interaction.toFixed(2)}%</b>
            <br/><br/>
            <u>▶ Click to watch video</u>
          </div>
        `;
      },
    },

    xaxis: {
      categories: labels,
      labels: {
        style: {
          colors: axisColor,
          fontSize: "12px",
        },
      },
    },

    yaxis: {
      min: 0,
      max: maxValue,
      labels: {
        formatter: function (val) {
          return metric === "interaction"
            ? `${val.toFixed(2)}%`
            : Math.floor(val).toLocaleString();
        },
        style: {
          colors: axisColor,
          fontSize: "14px",
          fontWeight: 700,
        },
      },
    },

    plotOptions: {
      bar: {
        borderRadius: 6,
        columnWidth: "40%",
        distributed: metric === "interaction",
        states: {
          hover: {
            filter: {
              type: "lighten",
              value: 0.15,
            },
          },
        },
      },
    },

    dataLabels: { enabled: false },

    colors:
      metric === "interaction"
        ? processedData.map((item) =>
            getInteractionColor(item.interaction, maxInteraction)
          )
        : metric === "viewsRaw"
        ? ["#369cf0"]
        : metric === "likesRaw"
        ? ["#ec205d"]
        : metric === "commentsRaw"
        ? ["#f48428"]
        : ["#4FD1C5"],

    grid: { show: false },
  };

  return (
    <Card w="100%" h="550px" p="20px"> {}
      <Flex mb="10px" align="center" gap="10px">
        <Text fontWeight="bold">Sort By:</Text>

        {metric === "interaction" && (
          <Tooltip
            hasArrow
            shouldWrapChildren
            placement="top"
            label={
            <>
              <Text fontWeight="bold">
                How Interaction Score is Measured
              </Text>

              <Text fontSize="sm" fontStyle="italic">
                <Divider my="4px" borderColor="gray.400" />
                Likes are measured with a value of 1x and comments
                are measured with a value of 10x. These combined
                values are compared against view count for
                interaction percentage.<br /><br />
                Formula is ((Likes+(Comments*10))/Views)*100
              </Text>

              {/* Gradient legend */}
              <Flex mt="10px" direction="column" align="center">
                <Flex
                  h="8px"
                  w="120px"
                  borderRadius="md"
                  bg="linear-gradient(to right, red, yellow, green)"
                />
                <Flex justify="space-between" w="120px" mt="2px">
                  <Text fontSize="xs">Low</Text>
                  <Text fontSize="xs">High</Text>
                </Flex>
              </Flex>
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

        <Select
          w="180px"
          value={metric}
          onChange={(e) => setMetric(e.target.value)}
        >
          {metricOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </Select>

        {/* Sort direction button */}
          <Flex gap="6px" ml="10px">
            {[
              { label: "High → Low", value: "desc" },
              { label: "Low → High", value: "asc" },
            ].map((option) => (
              <Flex
                key={option.value}
                px="10px"
                py="6px"
                borderRadius="12px"
                fontSize="sm"
                cursor="pointer"
                fontWeight="600"
                transition="all 0.2s"
                bg={sortOrder === option.value ? "purple.400" : "transparent"}
                color={sortOrder === option.value ? "white" : "gray.500"}
                _hover={{
                  bg: sortOrder === option.value ? "purple.500" : "gray.100",
                }}
                onClick={() => setSortOrder(option.value)}
              >
                {option.label}
              </Flex>
            ))}
          </Flex>
      </Flex>

      <Chart
        options={chartOptions}
        series={chartData}
        type="bar"
        width="100%"
        height="100%"
      />
    </Card>
  );
};

export default BarList;