$(document).ready(function() {
  const apiKey = "pub_173261c41e8bf5f13903030807c00d2b6d86";
  const apiUrl = "https://newsdata.io/api/1/news?apikey=";
  const apiUrl2 = "&q=zimbabwe&language=en";
  let newsArr = [];
  let count = 1;
  let index;
  let lat;
  let long;
  let temp;
  let conditions;
  let date = new Date();
  let startDate = new Date("2020-04-18");
  let milisec = date.getTime() - startDate.getTime();
  let volNum = Math.round(milisec / (1000 * 60 * 60 * 24));
  let currDate = date.toDateString();
  var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

  var d = new Date();
  var n = d.toISOString();
  var z = n.split("T")[0];
  var yesd = new Date(d);
  var yesb = yesd.setDate(yesd.getDate() - 1);
  console.log(yesb);
  console.log(z);
  
  const today = new Date()
  const yesterday = new Date(today)
  
  yesterday.setDate(yesterday.getDate() - 2)
  
  var test = yesterday.toISOString();
  var test1 = test.split("T")[0];
  console.log(test1);
  yesterday.toISOString();
  console.log(apiUrl);


  getData();
  getLocation();

  function getData() {
    $.ajax({
      type: "GET",
      url: apiUrl + apiKey + apiUrl2,
      datatype: "jsonp",
      success: function(data) {
        newsArr.push(data);
        insertData();
      }
    });
  }
  
    function insertData() {
      $(".date").append(date.toLocaleDateString("en-US", options));
      $(".vol").append("Edition # " + volNum + " | Page 2");
      for (let i = 1; i < newsArr[0].results.length; i++) {
        index = i - 1;
        let news = newsArr[0].results[index];
        if (news.description && news.source_id != "fox-news") {
          if (count < 4 && news.urlToImage) {
            $(".image" + count).attr("src", news.image_url);
            printData(news);
          } else if (count >= 4) {
            printData(news);
          }
          if (count === 8) {
            return true;
          }
        }
      }
    }
  
    function printData(news) {
      $(".storyTitle" + count).append(news.title);
      $(".story" + count).append(news.description);
      $(".by" + count).append("Source: " + news.source_id);
      $(".a" + count).attr("href", news.link);
      count++;
    }
  
    function getLocation() {
      $.ajax({
        type: "GET",
        url: "https://extreme-ip-lookup.com/json/",
        success: function(data) {
          long = 6.465422;
          lat = 3.406448;
          getWeather();
        }
      });
    }
  
    function getWeather() {
      $.ajax({
        type: "GET",
        url:
          "https://api.darksky.net/forecast/3a616888226060540aaa82c98bfacdb9/" +
          lat +
          "," +
          long,
        dataType: "jsonp",
        success: function(data) {
          showWeather(data);
        }
      });
    }
  
    function showWeather(data) {
      conditions = data.currently.summary;
      temp = Math.round(data.currently.apparentTemperature);
      $(".conditions").append(conditions);
      $(".temp").append(temp + String.fromCharCode(176) + "F");
    }
    function getWeatherLagos() {
        $.ajax({
          type: "GET",
          url:
            "https://api.darksky.net/forecast/3a616888226060540aaa82c98bfacdb9/" +
            6.465422 +
            "," +
            3.406448,
          dataType: "jsonp",
          success: function(data) {
            showWeatherLagos(data);
          }
        });
      }
    
      function showWeatherLagos(data) {
        conditions = data.currently.summary;
        temp = Math.round(data.currently.apparentTemperature);
        $(".conditionsLagos").append(conditions);
        $(".tempLagos").append(temp + String.fromCharCode(176) + "F");
      }
    
  });
  
  
