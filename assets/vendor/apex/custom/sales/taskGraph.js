// 定义一个函数来初始化任务图表
function initTaskGraph(totalTasks, warningTasks) {
	// 计算完成任务数和百分比
	const completedTasks = totalTasks - warningTasks;
	const completedPercentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
	const warningPercentage = totalTasks > 0 ? Math.round((warningTasks / totalTasks) * 100) : 0;
	
	var options = {
		chart: {
			height: 310,
			type: 'radialBar',
			toolbar: {
				show: false,
			},
			dropShadow: {
				enabled: true,
				opacity: 0.2,
				blur: 10,
				left: 10,
				top: 10
			},
		},
		plotOptions: {
			radialBar: {
				startAngle: -135,
				endAngle: 225,
				hollow: {
					margin: 0,
					size: '40%',
					background: '#fff',
				},
				track: {
					background: '#e7e7e7',
					strokeWidth: '67%',
					margin: 0,
					dropShadow: {
						enabled: true,
						top: -3,
						left: 0,
						blur: 4,
						opacity: 0.15
					}
				},
				dataLabels: {
					name: {
						fontSize: '14px',
						fontFamily: 'Nunito, sans-serif',
						color: '#888',
						offsetY: -10
					},
					value: {
						fontSize: '22px',
						fontFamily: 'Nunito, sans-serif',
						color: '#111',
						offsetY: -2,
						formatter: function (val) {
							return val + '%';
						}
					},
					total: {
						show: true,
						label: '总任务数',
						color: '#111',
						fontFamily: 'Nunito, sans-serif',
						formatter: function (w) {
							return totalTasks;
						}
					}
				}
			}
		},
		fill: {
			type: 'gradient',
			gradient: {
				shade: 'dark',
				type: 'horizontal',
				shadeIntensity: 0.5,
				gradientToColors: ['#10B981', '#F59E0B'],
				inverseColors: false,
				opacityFrom: 1,
				opacityTo: 1,
				stops: [0, 100]
			}
		},
		stroke: {
			lineCap: 'round'
		},
		series: [completedPercentage, warningPercentage],
		labels: ['评估通过', '需要改进'],
		colors: ['#10B981', '#F59E0B'],
	}

	var chart = new ApexCharts(
		document.querySelector("#taskGraph"),
		options
	);
	chart.render();
	
	return chart;
}

// 全局变量，存储图表实例
let taskChart = null;

// 从API获取数据并更新图表
function updateTaskGraph() {
	// 获取当前年月
	const now = new Date();
	const currentYear = now.getFullYear();
	const currentMonth = now.getMonth() + 1;
	
	// 获取数据
	fetch(`/api/monthly-tasks?year=${currentYear}&month=${currentMonth}`)
		.then(response => response.json())
		.then(tasks => {
			if (!tasks || tasks.length === 0) {
				// 如果没有数据，显示空状态
				if (taskChart) {
					taskChart.destroy();
				}
				taskChart = initTaskGraph(0, 0);
				return;
			}

			// 统计任务数
			const totalTasks = tasks.length;
			
			// 统计需要改进的任务数
			let tasksProcessed = 0;
			let improveTasks = 0;
			
			// 处理每个任务
			const processTaskDetails = () => {
				if (tasksProcessed === totalTasks) {
					// 当所有任务都处理完毕后更新图表
					if (taskChart) {
						taskChart.destroy();
					}
					taskChart = initTaskGraph(totalTasks, improveTasks);
					
					// 更新侧边栏统计数据
					document.getElementById('sidebarTasksCount').textContent = totalTasks;
					document.getElementById('sidebarWarningsCount').textContent = improveTasks;
				}
			};
			
			// 如果没有任务，直接初始化图表
			if (totalTasks === 0) {
				if (taskChart) {
					taskChart.destroy();
				}
				taskChart = initTaskGraph(0, 0);
				return;
			}
			
			// 检查每个任务
			tasks.forEach(task => {
				fetch(`/api/reports/${task.task_id}`)
					.then(response => response.json())
					.then(taskDetail => {
						tasksProcessed++;
						
						// 检查是否有任何维度低于80%
						let needImprovement = false;
						
						if (taskDetail.results) {
							// 检查每个模型
							for (const modelResults of Object.values(taskDetail.results)) {
								// 检查该模型的每个维度
								for (const stats of Object.values(modelResults)) {
									if (stats.accuracy) {
										const accuracy = typeof stats.accuracy === 'string' ? 
											parseFloat(stats.accuracy.replace('%', '')) / 100 : 
											parseFloat(stats.accuracy);
										
										// 如果任何一个维度的准确率低于80%，则需要改进
										if (!isNaN(accuracy) && accuracy < 0.8) {
											needImprovement = true;
											break;
										}
									}
								}
								
								if (needImprovement) break;
							}
						} else {
							// 如果没有结果数据，默认为需要改进
							needImprovement = true;
						}
						
						if (needImprovement) {
							improveTasks++;
						}
						
						processTaskDetails();
					})
					.catch(error => {
						console.error(`Error fetching task details: ${error}`);
						tasksProcessed++;
						improveTasks++; // 出错时默认为需要改进
						processTaskDetails();
					});
			});
		})
		.catch(error => {
			console.error('Error loading tasks for statistics:', error);
			// 如果加载失败，显示空状态
			if (taskChart) {
				taskChart.destroy();
			}
			taskChart = initTaskGraph(0, 0);
		});
}

// 页面加载完成后更新图表
document.addEventListener('DOMContentLoaded', function() {
	updateTaskGraph();
	
	// 每60秒自动刷新一次数据
	setInterval(updateTaskGraph, 60000);
});