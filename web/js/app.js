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

  const drawChart = (id, label) => {
    const datasets = Object.keys(data[id]).map(channel => {
      return {
        label: `Channel ${channel}`,
        borderColor: channelColours[channel],
        borderWidth: 1,
        fill: false,
        data: data[id][channel],
        yAxisID: 'y-main'
      }
    })

    datasets.push({
      label: 'Log events',
      type: 'bar',
      backgroundColor: 'rgba(0, 0, 0, 0)',
      borderColor: 'rgba(255, 0, 0, 0.5)',
      borderWidth: 2,
      data: data.network_log_events,
      yAxisID: 'y-log'
    })

    const config = {
      type: 'line',
      data: {
        datasets: datasets
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
            scaleLabel: {display: true, labelString: 'Time'}
          }],
          yAxes: [
            {
              scaleLabel: {
                display: true,
                labelString: label
              },
              position: 'left',
              id: 'y-main',
            },
            {
              scaleLabel: {
                display: true,
                labelString: 'Log events (minute)'
              },
              position: 'right',
              id: 'y-log',
            }
          ]
        },
        elements: {
          point: {
            radius: 0
          }
        }
      }
    }

    const ctx = document.getElementById(`${id}_chart`).getContext('2d');
    const chart = new Chart(ctx, config);
  }

  drawChart('downstream_power', 'Downstream power (dBmV)')
  drawChart('downstream_snr', 'Downstream SNR')
  drawChart('downstream_rxmer', 'Downstream RxMER (dB)')
  drawChart('upstream_power', 'Upstream power (dBmV)')
})
