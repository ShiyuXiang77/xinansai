var options = {
  series: [
      {
        name: "测评结果",
        data: [
          {
            x: "真实",
            y: 92,
            goals: [
              {
                name: "期望",
                value: 90,
                strokeHeight: 10,
                strokeWidth: 1,
                strokeColor: "#BBBBBB",
              },
            ],
          },
          {
            x: "隐私",
            y: 57,
            goals: [
              {
                name: "期望",
                value: 90,
                strokeHeight: 10,
                strokeWidth: 1,
                strokeColor: "#BBBBBB",
              },
            ],
          },
          {
            x: "安全",
            y: 98,
            goals: [
              {
                name: "期望",
                value: 90,
                strokeHeight: 10,
                strokeWidth: 1,
                strokeColor: "#BBBBBB",
              },
            ],
          },
          {
            x: "越狱",
            y: 86,
            goals: [
              {
                name: "期望",
                value: 90,
                strokeHeight: 10,
                strokeWidth: 1,
                strokeColor: "#BBBBBB",
              },
            ],
          },
          {
            x: "伦理",
            y: 95,
            goals: [
              {
                name: "期望",
                value: 90,
                strokeHeight: 10,
                strokeWidth: 1,
                strokeColor: "#BBBBBB",
              },
            ],
          },
          {
            x: "公平",
            y: 91,
            goals: [
              {
                name: "期望",
                value: 90,
                strokeHeight: 10,
                strokeWidth: 1,
                strokeColor: "#BBBBBB",
              },
            ],
          },
          {
            x: "政策",
            y: 99,
            goals: [
              {
                name: "期望",
                value: 90,
                strokeHeight: 10,
                strokeWidth: 1,
                strokeColor: "#BBBBBB",
              },
            ],
          },
        ],
      },
  ],
  chart: {
    height: 270,
    type: "bar",
    toolbar: {
      show: false,
    },
  },
  plotOptions: {
    bar: {
      horizontal: false,
      columnWidth: "70%",
    },
  },
  dataLabels: {
    enabled: false,
  },
  stroke: {
    show: false,
  },
  colors: ["#7943ef"],
  yaxis: {
    show: false,
  },
  legend: {
    show: true,
    showForSingleSeries: true,
    customLegendItems: ["测评结果", "期望"],
    markers: {
      fillColors: ["#7943ef", "#BBBBBB"],
    },
  },
};

var chart = new ApexCharts(document.querySelector("#keyMetrics"), options);
chart.render();
