var options = {
	series: [
		
	{
		name: 'In Millions',
	  data: [
		{
		  	x: '数据泄露',
		  	y: 218
		},		
		{
		  	x: '虚假',
		  	y: 197
		},
		{
			x: '用户数据',
			y: 149
	  	},
		{
		  	x: '性别偏见',
		  	y: 55
		},
		{
		  	x: '误导',
		  	y: 84
		},
		{
		  	x: '少数群体',
		  	y: 31
		},
		{
		  	x: '敏感话题',
		  	y: 70
		},
		{
		  	x: '多元文化',
		  	y: 30
		},
		{
		  	x: '注入攻击',
		  	y: 44
		},
		{
		  	x: '越狱',
		  	y: 68
		},
		{
		  	x: '内容合规',
		  	y: 28
		},
		{
		  	x: '模型偏向',
		  	y: 19
		},
		{
		  	x: '恶意生成',
		  	y: 29
		}
	  ]
	}
  	],
	legend: {
		show: false
  	},
  	chart: {
		height: 270,
		type: 'treemap',
		toolbar: {
			show: false,
	  },
  	},
	  colors: ["#EB3333", "#7943ef"],
	  tooltip: {
        y: {
            formatter: function(val) {
                return '$' + val + " Million"
            }
        }
    },
  };

  var chart = new ApexCharts(document.querySelector("#adsRevenue"), options);
  chart.render();