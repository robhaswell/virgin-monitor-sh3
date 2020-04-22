const channelColours = {
  1: 'rgb(238, 32, 77)',
  2: 'rgb(252, 232, 131)',
  3: 'rgb(31, 117, 254)',
  4: 'rgb(180, 103, 77)',
  5: 'rgb(255, 117, 56)',
  6: 'rgb(28, 172, 120)',
  7: 'rgb(146, 110, 174)',
  8: 'rgb(35, 35, 35)',
  9: 'rgb(255, 170, 204)',
  10: 'rgb(255, 182, 83)',
  11: 'rgb(25, 158, 189)',
  12: 'rgb(192, 68, 143)',
  13: 'rgb(255, 83, 73)',
  14: 'rgb(197, 227, 132)',
  15: 'rgb(115, 102, 189)',
  16: 'rgb(162, 173, 208)',
  17: 'rgb(247, 83, 148)',
  18: 'rgb(253, 219, 109)',
  19: 'rgb(29, 172, 214)',
  20: 'rgb(253, 217, 181)',
  21: 'rgb(252, 40, 71)',
  22: 'rgb(240, 232, 145)',
  23: 'rgb(93, 118, 203)',
  24: 'rgb(149, 145, 140)',
}

document.addEventListener('DOMContentLoaded', async (event) => {
  const response = await window.fetch('/data')
  const data = await response.json()

  const config = {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: Object.keys(data.downstream_power).map(channel => {
        return {
          label: `Channel ${channel}`,
          borderColor: channelColours[channel],
          borderWidth: 1,
          fill: false,
          data: data.downstream_power[channel]
        }
      })
    },
    options: {
      title: {text: 'Chart.js Time Scale'},
      animation: {
        duration: 0
      },
      scales: {
        xAxes: [{
          type: 'time',
          time: {
            // round: 'minute',
            tooltipFormat: 'HH:mm:ss'
          },
          scaleLabel: {display: true, labelString: 'Date'}
        }],
        yAxes: [{scaleLabel: {display: true, labelString: 'value'}}]
      },
      elements: {
        point: {
          radius: 0
        }
      }
    }
  }

  const ctx = document.getElementById('canvas').getContext('2d');
  const myLine = new Chart(ctx, config);
})
