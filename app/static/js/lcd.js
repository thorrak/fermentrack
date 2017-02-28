var vm = new Vue({
  el: '#lcdapp',
  data: {
    lcds: ''
  },
  mounted: function () {
    this.getLCDs();
    window.setInterval(() => {
      this.getLCDs()
    }, 5000)
  },
  methods: {
      getLCDs: function() {
        var xhr = new XMLHttpRequest();
        var self = this;
        xhr.open('GET', '/api/lcd/');
        xhr.onload = function () {
          self.lcds = JSON.parse(xhr.responseText);
          // console.log(self.lcds)
        };
        xhr.send()
      }
  }
});
