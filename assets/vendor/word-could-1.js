document.addEventListener("DOMContentLoaded", function () {
  const modal = document.getElementById("modalXl-1");

  if (modal) {
    modal.addEventListener("shown.bs.modal", function () {

      // Step 1: 清空旧内容（如果反复打开会重复挂图）
      const chartDom = document.querySelector("#wordCloud-1");
      if (!chartDom) return;
      chartDom.innerHTML = "";

      // Step 2: 配置图表数据（可以后期替换成 fetch 来动态获取）
      const options = {
        series: [{
          name: 'In Millions',
          data: [
              { x: '数据泄露', y: 21.33 },
              { x: '虚假', y: 19.28 },
              { x: '用户数据', y: 14.59 },
              { x: '性别偏见', y: 5.38 },
              { x: '误导', y: 8.22 },
              { x: '少数群体', y: 3.03 },
              { x: '敏感话题', y: 6.85 },
              { x: '多元文化', y: 2.94 },
              { x: '注入攻击', y: 4.31 },
              { x: '恶意生成', y: 6.65 },
              { x: '内容合规', y: 2.74 },
              { x: '偏向', y: 1.86 },
              { x: '越狱', y: 2.84 }
          ]
        }],
        chart: {
          height: 270,
          type: 'treemap',
          toolbar: { show: false }
        },
        legend: { show: false },
        colors: ["#3d912d", "#7943ef"],
        tooltip: {
          y: {
            formatter: function (val) {
              return val + "%";
            }
          }
        }
      };

      // Step 3: 渲染 ApexCharts 图表
      const chart = new ApexCharts(chartDom, options);
      chart.render();
    });
  }
});
