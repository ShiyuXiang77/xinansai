//地图容器
var chart = echarts.init(document.getElementById('cityMap'));

// //34个省、市、自治区的名字拼音映射数组
// var provinces = {
//     //23个省
//     "台湾": "taiwan",
//     "河北": "hebei",
//     "山西": "shanxi",
//     "辽宁": "liaoning",
//     "吉林": "jilin",
//     "黑龙江": "heilongjiang",
//     "江苏": "jiangsu",
//     "浙江": "zhejiang",
//     "安徽": "anhui",
//     "福建": "fujian",
//     "江西": "jiangxi",
//     "山东": "shandong",
//     "河南": "henan",
//     "湖北": "hubei",
//     "湖南": "hunan",
//     "广东": "guangdong",
//     "海南": "hainan",
//     "四川": "sichuan",
//     "贵州": "guizhou",
//     "云南": "yunnan",
//     "陕西": "shanxi1",
//     "甘肃": "gansu",
//     "青海": "qinghai",
//     //5个自治区
//     "新疆": "xinjiang",
//     "广西": "guangxi",
//     "内蒙古": "neimenggu",
//     "宁夏": "ningxia",
//     "西藏": "xizang",
//     //4个直辖市
//     "北京": "beijing",
//     "天津": "tianjin",
//     "上海": "shanghai",
//     "重庆": "chongqing",
//     //2个特别行政区
//     "香港": "xianggang",
//     "澳门": "aomen"
// };
//
// //直辖市和特别行政区-只有二级地图，没有三级地图
// var special = ["北京","天津","上海","重庆","香港","澳门"];
// 省份数据（颜色渐变效果）
var mapData = [];
$.getJSON('static/map/china.json', function (data) {
    for (var i = 0; i < data.features.length; i++) {
        let provinceName = data.features[i].properties.name;
        let gradientFactor = Math.random(); // 生成一个 0-1 之间的随机值
        let r = Math.round(255 * (1 - gradientFactor) + 136 * gradientFactor);
        let g = Math.round(255 * (1 - gradientFactor) + 84 * gradientFactor);
        let b = Math.round(255 * (1 - gradientFactor) + 241 * gradientFactor);
        let color = `rgb(${r}, ${g}, ${b})`;

        mapData.push({
            name: provinceName,
            value: Math.random() * 100,
            itemStyle: {
                normal: {
                    areaColor: color, // 从白色到 #8854F1 渐变
                    borderColor: '#e5dbfc',
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
                    {name: '字节豆包', value: [116.92, 40.52, 100]},
                    {name: '深度求索', value: [120.25, 30.35, 80]},
                    {name: '智谱清言', value: [116.55, 40.25, 60]},
                    {name: 'Kimi', value: [115.85, 39.65, 70]},
                    {name: '百川智能', value: [116.60, 39.35, 80]},
                    {name: '通义千问', value: [122.05, 31.05, 90]},
                    {name: '海螺AI', value: [122.15, 31.65, 75]},
                    {name: '跃问', value: [121.75, 31.85, 65]},
                    {name: '文心一言', value: [121.25, 31.45, 95]},
                    {name: '商汤日日新', value: [122.25, 31.75, 75]},
                    {name: '腾讯元宝', value: [113.95, 22.55, 85]},
                    {name: '讯飞星火', value: [117.30, 31.90, 85]},
                    {name: '通义万相', value: [120.00, 30.00, 85]},
                ],
                itemStyle: {
                    normal: {
                        color: function (params) {
                        let colors = ["#FF79C6", "#a1faaf", "#F1FA8C", "#FF5555"];
                        return colors[params.dataIndex % colors.length];
                        },
                        shadowBlur: 10,
                        shadowColor: "rgba(0, 0, 0, 0.5)"
                    }
                },
                symbolSize: function (val) {
                    return Math.sqrt(val[2]);
                },
                tooltip: {
                    show: true
                },
                showEffectOn: "render",
                rippleEffect: {
                    brushType: "stroke",
                    color: "#ffffff",
                    period: 9,
                    scale: 3
                },
                hoverAnimation: true,
                label: {
                    show: true,
                    position: 'right',
                    formatter: '{b}'
                },
                zlevel: 1
            }
        ]
    };
    chart.setOption(option2);
}

