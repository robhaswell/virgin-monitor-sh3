window.chartColors = {
  red: 'rgb(255, 99, 132)',
  orange: 'rgb(255, 159, 64)',
  yellow: 'rgb(255, 205, 86)',
  green: 'rgb(75, 192, 192)',
  blue: 'rgb(54, 162, 235)',
  purple: 'rgb(153, 102, 255)',
  grey: 'rgb(201, 203, 207)'
}

document.addEventListener('DOMContentLoaded', async (event) => {
  const response = await window.fetch('/data')
  const data = await response.json()

  const timeFormat = 'YYYY-MM-DD HH:mm:ss'

  const color = Chart.helpers.color

  const config = {
    type: 'line',
    data: {
      labels: data.labels.map(isotime => moment(isotime).toDate()),
      datasets: [{
        label: 'Dataset with point data',
        backgroundColor: color(window.chartColors.green).alpha(0.5).rgbString(),
        borderColor: window.chartColors.green,
        fill: false,
        data: data.downstream_power[1].map(({x, y}) => { return {x: moment(x).toDate(), y}})
      }]
    },
    options: {
      title: {text: 'Chart.js Time Scale'},
      scales: {
        xAxes: [{
          type: 'time',
          time: {
            // round: 'day'
            tooltipFormat: 'HH:mm:ss'
          },
          scaleLabel: {display: true, labelString: 'Date'}
        }],
        yAxes: [{scaleLabel: {display: true, labelString: 'value'}}]
      },
    }
  }
  console.log(config)

  const ctx = document.getElementById('canvas').getContext('2d');
  const myLine = new Chart(ctx, config);

})
