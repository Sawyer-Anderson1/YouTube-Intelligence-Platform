import React, { useState, useMemo } from "react";
import Card from "components/Card/Card";
import Chart from "react-apexcharts";
import {
  useColorModeValue,
  Select,
  Flex,
  Text,
} from "@chakra-ui/react";

const metricOptions = [
  { label: "Views", value: "viewsRaw" },
  { label: "Likes", value: "likesRaw" },
  { label: "Comments", value: "commentsRaw" },
  { label: "Interaction", value: "interaction" },
];

const BarList = ({ data }) => {
  const [metric, setMetric] = useState("viewsRaw");

  const axisColor = useColorModeValue("#1A202C", "#FFFFFF");

  const processedData = useMemo(() => {
    return [...data]
      .map((item) => ({
        ...item,
        likesRaw: Number(item.likes.toString().replace(/,/g, "")),
        commentsRaw: Number(item.comments.toString().replace(/,/g, "")),
      }))
      .sort((a, b) => b[metric] - a[metric]);
  }, [data, metric]);

  const values = processedData.map((item) => item[metric]);
  const labels = processedData.map((_, i) => i + 1);
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
      custom: function ({ dataPointIndex }) {
        const item = processedData[dataPointIndex];
        if (!item) return "";

        return `
          <div style="
            padding:10px;
            max-width:300px;
            white-space:normal;
            word-wrap:break-word;
          ">
            <b><u>${item.name}</u></b><br/>
            <i>${item.quote}</i><br/><br/>
            Total Views: <b>${item.views}</b><br/>
            Total Likes: <b>${item.likes}</b><br/>
            Total Comments: <b>${item.comments}</b><br/>
            Interaction Score: <b>${item.interaction.toFixed(2)}%</b>
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
      </Flex>

      <Chart
        options={chartOptions}
        series={chartData}
        type="bar"
        width="100%"
        height="100%"
      />

      {metric === "interaction" && (
        <Flex mt="4px" justify="center">
          <Flex direction="column" align="center" w="20%">
            <Flex
              h="8px"
              w="100%"
              borderRadius="md"
              bg="linear-gradient(to right, red, yellow, green)"
            />
            <Flex justify="space-between" w="100%" mt="2px">
              <Text fontSize="xs">Low Interaction</Text>
              <Text fontSize="xs">High Interaction</Text>
            </Flex>
          </Flex>
        </Flex>
      )}
    </Card>
  );
};

export default BarList;