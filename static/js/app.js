//地图容器
var chart = echarts.init(document.getElementById('cityMap'));
//34个省、市、自治区的名字拼音映射数组
var provinces = {
    //23个省
    "台湾": "taiwan",
    "河北": "hebei",
    "山西": "shanxi",
    "辽宁": "liaoning",
    "吉林": "jilin",
    "黑龙江": "heilongjiang",
    "江苏": "jiangsu",
    "浙江": "zhejiang",
    "安徽": "anhui",
    "福建": "fujian",
    "江西": "jiangxi",
    "山东": "shandong",
    "河南": "henan",
    "湖北": "hubei",
    "湖南": "hunan",
    "广东": "guangdong",
    "海南": "hainan",
    "四川": "sichuan",
    "贵州": "guizhou",
    "云南": "yunnan",
    "陕西": "shanxi1",
    "甘肃": "gansu",
    "青海": "qinghai",
    //5个自治区
    "新疆": "xinjiang",
    "广西": "guangxi",
    "内蒙古": "neimenggu",
    "宁夏": "ningxia",
    "西藏": "xizang",
    //4个直辖市
    "北京": "beijing",
    "天津": "tianjin",
    "上海": "shanghai",
    "重庆": "chongqing",
    //2个特别行政区
    "香港": "xianggang",
    "澳门": "aomen"
};

//直辖市和特别行政区-只有二级地图，没有三级地图
var special = ["北京","天津","上海","重庆","香港","澳门"];
// 省份数据（颜色渐变效果）
var mapData = [];
$.getJSON('static/map/china.json', function (data) {
    for (var i = 0; i < data.features.length; i++) {
        let provinceName = data.features[i].properties.name;
        mapData.push({
            name: provinceName,
            value: Math.random() * 100,
            itemStyle: {
                normal: {
                    areaColor: `rgba(191, 161, 230, ${Math.random()})`, // 随机浅紫色
                    borderColor: '#FFFFFF',
                    borderWidth: 2
                }
            }
        });
    }
    echarts.registerMap('china', data);
    renderMap('china', mapData);
});

function renderMap(map, data) {
    var option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            formatter: function (params) {
                if (params.data && params.data.name) {
                    return `<b>${params.data.name}</b>`;
                }
                return params.name;
            }
        },
        geo: {
            map: 'china',
            roam: false,
            label: {
                normal: { show: false },
                emphasis: { show: false }
            },
            itemStyle: {
                normal: {
                    borderColor: '#FFFFFF',
                    borderWidth: 2
                },
                emphasis: {
                    areaColor: '#A991E1',
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }
            }
        },
        series: [
            {
                name: '省份区域',
                type: 'map',
                mapType: 'china',
                roam: false,
                showLegendSymbol: false,
                data: data,
                label: {
                    normal: { show: false },
                    emphasis: {
                        show: false,
                        textstyle: { color: "#fff" }
                    }
                },
                itemStyle: {
                    normal: {
                        borderColor: '#FFFFFF',
                        borderWidth: 2
                    },
                    emphasis: {
                        areaColor: "#17008d",
                        shadowOffsetX: 0,
                        shadowOffsetY: 0,
                        shadowBlur: 5,
                        borderWidth: 0,
                        shadowColor: "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    };
    chart.setOption(option);

    var option2 = {
        series: [
            {
                type: 'map',
                map: 'china',
                roam: false,
                label: {
                    normal: {
                        show: false
                    },
                    emphasis: {
                        show: false
                    }
                },
                itemStyle: {
                    normal: {
                        areaColor: 'rgba(0, 0, 0, 0)',
                        borderColor: '#CCCCCC',
                        borderWidth: 1
                    },
                    emphasis: {
                        areaColor: 'rgba(100, 149, 237, 0.5)',
                        borderWidth: 2,
                        borderColor: '#FFFFFF'
                    }
                }
            },
            {
                name: '',
                type: 'scatter',
                coordinateSystem: 'geo',
                symbolSize: function (val) {
                    return Math.sqrt(val[2]) * 1.2;
                },
                label: {
                    show: false,
                    position: 'right',
                    color: '#333',
                    fontSize: 12,
                    fontWeight: 'bold',
                    formatter: '{b}'
                },
                itemStyle: {
                    color: '#5bc8b4',
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                },
                emphasis: {
                    label: {
                        show: false
                    }
                }
            },
            {
                name: '大模型分布',
                type: 'effectScatter',
                coordinateSystem: 'geo',
                data: [
                    {name: '字节豆包', value: [116.90, 40.50, 100]}, // 北京
                    {name: '深度求索', value: [120.20, 30.30, 80]}, // 杭州
                    {name: '智谱清言', value: [116.50, 40.20, 60]}, // 北京
                    {name: 'Kimi', value: [115.80, 39.60, 70]}, // 北京
                    {name: '百川智能', value: [116.50, 39.30, 80]}, // 北京
                    {name: '万知', value: [116.00, 39.20, 70]}, // 北京
                    {name: '快手可灵', value: [116.50, 40.50, 65]}, // 北京
                    {name: '智谱清影', value: [115.30, 40.00, 75]}, // 北京
                    {name: '通义千问', value: [122.00, 31.00, 90]}, // 上海
                    {name: '海螺AI', value: [122.10, 31.60, 75]}, // 上海
                    {name: '跃问', value: [121.70, 31.80, 65]}, // 上海
                    {name: '文心一言', value: [121.20, 31.40, 95]}, // 上海
                    {name: '商汤日日新', value: [122.20, 31.70, 75]}, // 上海
                    {name: '腾讯元宝', value: [113.93, 22.53, 85]}, // 深圳
                    {name: '讯飞星火', value: [117.27, 31.86, 85]}, // 合肥
                    {name: '通义万相', value: [120.50, 30.50, 85]}, // 杭州
                ],
                symbolSize: function (val) {
                    return Math.sqrt(val[2]) * 1.2;
                },
                tooltip: {
                    show: true
                },
                showEffectOn: "render",
                rippleEffect: {
                    brushType: "stroke",
                    color: "#0efacc",
                    period: 9,
                    scale: 5
                },
                hoverAnimation: true,
                label: {
                    show: true,
                    position: 'right',
                    formatter: '{b}'
                },
                itemStyle: {
                    color: '#0efacc',
                    shadowBlur: 2,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                },
                zlevel: 1
            }
        ]
    };
    chart.setOption(option2);
}

