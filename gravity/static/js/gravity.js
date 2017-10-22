var vm = new Vue({
  el: '#gravapp',
  data: {
    sensors: ''
  },
  mounted: function () {
    this.getSensors();
    window.setInterval(() => {
      this.getSensors()
    }, 10000)  // Extending the delay as we don't update that often
  },
  methods: {
      getSensors: function() {
        var xhr = new XMLHttpRequest();
        var self = this;
        xhr.open('GET', '/api/gravity/');
        xhr.onload = function () {
          self.sensors = JSON.parse(xhr.responseText);
          // console.log(self.sensors)
        };
        xhr.send()
      }
  }
});
